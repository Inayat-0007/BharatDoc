import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from routers import auth, documents
from security import (
    RateLimitMiddleware,
    RequestSizeLimitMiddleware,
    SecurityHeadersMiddleware,
    AuditLogMiddleware,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
)

# Configure audit logger
audit_handler = logging.StreamHandler()
audit_handler.setFormatter(logging.Formatter(
    "%(asctime)s [AUDIT] %(message)s"
))
audit_logger = logging.getLogger("bharatdoc.audit")
audit_logger.addHandler(audit_handler)
audit_logger.setLevel(logging.INFO)

app = FastAPI(
    title="BharatDoc API",
    version="1.0.0",
    description="Intelligent document Q&A platform with OCR, embeddings, and semantic search",
    docs_url="/docs" if os.getenv("ENABLE_DOCS", "true").lower() == "true" else None,
    redoc_url=None,
)

# ── Security Middleware Stack (order matters: outermost first) ──

# 1. Security Headers (outermost — runs on every response)
app.add_middleware(SecurityHeadersMiddleware)

# 2. Audit Logging
app.add_middleware(AuditLogMiddleware)

# 3. Rate Limiting
app.add_middleware(RateLimitMiddleware)

# 4. Request Size Limiting
app.add_middleware(RequestSizeLimitMiddleware)

# 5. CORS — restricted to known origins
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# 6. Trusted Host (prevents host header attacks)
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,backend").split(",")
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=ALLOWED_HOSTS,
)

# ── Routers ──
app.include_router(auth.router)
app.include_router(documents.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
