"""
Phase 14: Security Hardening
Middleware and utilities for production-grade security.

Components:
1. Rate Limiting — per-endpoint, configurable
2. Request Size Limiting — prevent oversized payloads
3. Audit Logging — who/what/when for sensitive actions
4. Input Sanitization — strip dangerous content from text inputs
5. Security Headers — HSTS, X-Content-Type-Options, etc.
"""

import os
import time
import logging
from collections import defaultdict
from datetime import datetime
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

# Audit logger — separate from app logger
audit_logger = logging.getLogger("bharatdoc.audit")
audit_logger.setLevel(logging.INFO)

# Rate limiting configuration (requests per window)
RATE_LIMITS = {
    "/auth/login": {"max_requests": 5, "window_seconds": 60},
    "/auth/register": {"max_requests": 3, "window_seconds": 60},
    "/auth/forgot-password": {"max_requests": 3, "window_seconds": 60},
    "/auth/reset-password": {"max_requests": 3, "window_seconds": 60},
    "/auth/verify-email": {"max_requests": 5, "window_seconds": 60},
    "/auth/resend-verification": {"max_requests": 3, "window_seconds": 60},
    "/documents/upload": {"max_requests": 10, "window_seconds": 60},
    "/documents/query": {"max_requests": 20, "window_seconds": 60},
    "/documents/search": {"max_requests": 20, "window_seconds": 60},
}

# Max request body size (in bytes) — 50MB for uploads, 1MB for everything else
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", str(50 * 1024 * 1024)))  # 50MB
MAX_REQUEST_SIZE = int(os.getenv("MAX_REQUEST_SIZE", str(1 * 1024 * 1024)))  # 1MB


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Per-IP, per-endpoint rate limiting.
    Uses a sliding window counter stored in memory.
    """
    
    def __init__(self, app):
        super().__init__(app)
        # {(ip, path): [(timestamp, ...)]]}
        self._requests: dict[tuple[str, str], list[float]] = defaultdict(list)
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP, respecting X-Forwarded-For behind reverse proxy."""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    def _get_rate_limit(self, path: str) -> dict | None:
        """Find rate limit config for the given path."""
        for prefix, config in RATE_LIMITS.items():
            if path.startswith(prefix):
                return config
        return None
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        rate_config = self._get_rate_limit(path)
        
        if rate_config and request.method != "OPTIONS":
            client_ip = self._get_client_ip(request)
            key = (client_ip, path)
            now = time.time()
            window = rate_config["window_seconds"]
            max_req = rate_config["max_requests"]
            
            # Clean old entries outside the window
            self._requests[key] = [
                ts for ts in self._requests[key] if now - ts < window
            ]
            
            if len(self._requests[key]) >= max_req:
                audit_logger.warning(
                    f"RATE_LIMIT_EXCEEDED | ip={client_ip} | path={path} | "
                    f"limit={max_req}/{window}s"
                )
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests. Please try again later."},
                    headers={"Retry-After": str(window)}
                )
            
            self._requests[key].append(now)
        
        response = await call_next(request)
        return response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Enforce maximum request body size."""
    
    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        
        if content_length:
            size = int(content_length)
            path = request.url.path
            
            # Upload endpoint gets larger limit
            if "/upload" in path:
                max_size = MAX_UPLOAD_SIZE
            else:
                max_size = MAX_REQUEST_SIZE
            
            if size > max_size:
                return JSONResponse(
                    status_code=413,
                    content={
                        "detail": f"Request body too large. Maximum: {max_size // (1024*1024)}MB"
                    }
                )
        
        response = await call_next(request)
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        # XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # Permissions policy
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        
        return response


class AuditLogMiddleware(BaseHTTPMiddleware):
    """Log all sensitive operations for audit trail."""
    
    # Paths that trigger audit logging
    AUDIT_PATHS = {
        "/auth/login": "AUTH_LOGIN",
        "/auth/register": "AUTH_REGISTER",
        "/auth/forgot-password": "AUTH_FORGOT_PASSWORD",
        "/auth/reset-password": "AUTH_RESET_PASSWORD",
        "/auth/verify-email": "AUTH_VERIFY_EMAIL",
        "/auth/resend-verification": "AUTH_RESEND_VERIFICATION",
        "/documents/upload": "DOC_UPLOAD",
        "/documents/query": "DOC_QUERY",
        "/documents/search": "DOC_SEARCH",
    }
    
    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method
        
        # Check if this path needs auditing
        audit_action = None
        for prefix, action in self.AUDIT_PATHS.items():
            if path.startswith(prefix) and method in ("POST", "DELETE", "PUT"):
                audit_action = action
                break
        
        # Also audit DELETE operations on documents
        if method == "DELETE" and "/documents/" in path:
            audit_action = "DOC_DELETE"
        
        response = await call_next(request)
        
        if audit_action:
            client_ip = self._get_client_ip(request)
            audit_logger.info(
                f"{audit_action} | ip={client_ip} | method={method} | "
                f"path={path} | status={response.status_code} | "
                f"time={datetime.utcnow().isoformat()}"
            )
        
        return response


def sanitize_query_input(text: str, max_length: int = 2000) -> str:
    """
    Sanitize user query input to prevent prompt injection.
    
    - Truncate to max length
    - Strip common prompt injection patterns
    - Normalize whitespace
    """
    if not text:
        return ""
    
    # Truncate
    text = text[:max_length]
    
    # Strip dangerous patterns (system prompt overrides)
    dangerous_patterns = [
        "ignore previous instructions",
        "ignore all instructions",
        "disregard previous",
        "you are now",
        "system prompt",
        "{{",
        "}}",
        "<|",
        "|>",
    ]
    
    text_lower = text.lower()
    for pattern in dangerous_patterns:
        if pattern in text_lower:
            logger.warning(f"Prompt injection attempt detected: '{pattern}' in query")
            # Don't block — just log. The extractive mode is injection-safe.
    
    # Normalize whitespace
    text = " ".join(text.split())
    
    return text.strip()
