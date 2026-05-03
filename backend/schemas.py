from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime
import re


# ── Password Complexity Rules ──
# Enforced: min 8 chars, at least 1 uppercase, 1 lowercase, 1 digit, 1 special char
# This matches NIST SP 800-63B and OWASP password recommendations.
PASSWORD_MIN_LENGTH = 8
PASSWORD_PATTERN = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?`~])"
)


class UserCreate(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        errors = []
        if len(v) < PASSWORD_MIN_LENGTH:
            errors.append(f"at least {PASSWORD_MIN_LENGTH} characters")
        if not re.search(r"[a-z]", v):
            errors.append("one lowercase letter")
        if not re.search(r"[A-Z]", v):
            errors.append("one uppercase letter")
        if not re.search(r"\d", v):
            errors.append("one digit")
        if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?`~]", v):
            errors.append("one special character (!@#$%^&*...)")
        if errors:
            raise ValueError(
                f"Password must contain: {', '.join(errors)}"
            )
        return v

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime
    is_verified: bool = False
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str | None = None

# ── Phase 18: Auth Hardening Schemas ──

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        errors = []
        if len(v) < PASSWORD_MIN_LENGTH:
            errors.append(f"at least {PASSWORD_MIN_LENGTH} characters")
        if not re.search(r"[a-z]", v):
            errors.append("one lowercase letter")
        if not re.search(r"[A-Z]", v):
            errors.append("one uppercase letter")
        if not re.search(r"\d", v):
            errors.append("one digit")
        if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?`~]", v):
            errors.append("one special character (!@#$%^&*...)")
        if errors:
            raise ValueError(
                f"Password must contain: {', '.join(errors)}"
            )
        return v

class VerifyEmailRequest(BaseModel):
    token: str

class ResendVerificationRequest(BaseModel):
    email: EmailStr

class MessageResponse(BaseModel):
    message: str

# ── Document Schemas (unchanged) ──

class DocumentResponse(BaseModel):
    id: int
    filename: str
    content_type: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class DocumentPageBase(BaseModel):
    page_number: int
    text_content: Optional[str] = None
    fallback_needed: bool
    parser_used: Optional[str] = None

class DocumentPageResponse(DocumentPageBase):
    id: int
    document_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class DocumentChunkBase(BaseModel):
    page_number: int
    chunk_index: int
    text: str
    start_offset: int
    end_offset: int

class DocumentChunkResponse(DocumentChunkBase):
    id: int
    document_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class DocumentSearchRequest(BaseModel):
    query: str
    top_k: int = 5
    document_ids: Optional[List[int]] = None

class DocumentSearchResult(BaseModel):
    chunk: DocumentChunkResponse
    similarity: float
    document_filename: str

class QueryRequest(BaseModel):
    query: str
    document_id: int
    top_k: int = 5
    mode: str = "audit" # "audit" (strict) or "summary" (conversational)

class Citation(BaseModel):
    page_number: int
    chunk_index: int
    text: str
    similarity: float

class QueryResponse(BaseModel):
    status: str  # "answered" | "refused"
    answer: Optional[str] = None
    confidence: float
    support_level: Optional[str] = None  # "supported" | "partially_supported" | "unsupported"
    answer_mode: Optional[str] = None    # "extractive" | "synthesis"
    citations: List[Citation] = []
    refusal_message: Optional[str] = None
    diagnostics: Optional[dict] = None
