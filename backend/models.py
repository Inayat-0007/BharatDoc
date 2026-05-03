from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from database import Base
from pgvector.sqlalchemy import Vector

class DocumentStatus(str, enum.Enum):
    uploaded = "uploaded"
    processing = "processing"
    ready = "ready"
    failed = "failed"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # ── Phase 18: Auth Hardening Fields ──
    # Email verification — accounts are unverified by default
    is_verified = Column(Boolean, default=False, server_default="false", nullable=False)

    # Account lockout — brute-force protection
    # Locks after MAX_FAILED_ATTEMPTS consecutive failures for LOCKOUT_DURATION_MINUTES
    failed_login_attempts = Column(Integer, default=0, server_default="0", nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)

    # Password change tracking — invalidate old sessions after password reset
    password_changed_at = Column(DateTime(timezone=True), nullable=True)

    documents = relationship("Document", back_populates="owner", cascade="all, delete-orphan")

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    status = Column(Enum(DocumentStatus), default=DocumentStatus.uploaded, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    owner = relationship("User", back_populates="documents")
    pages = relationship("DocumentPage", back_populates="document", cascade="all, delete-orphan")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

class DocumentPage(Base):
    __tablename__ = "document_pages"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    page_number = Column(Integer, nullable=False)
    text_content = Column(String, nullable=True)
    fallback_needed = Column(Boolean, default=False)
    parser_used = Column(String, default="pymupdf")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    document = relationship("Document", back_populates="pages")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    page_number = Column(Integer, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    text = Column(String, nullable=False)
    start_offset = Column(Integer, nullable=False)
    end_offset = Column(Integer, nullable=False)
    # Dimension 1024 matches the BGE-M3 embedding model output (BAAI/bge-m3).
    # If EMBEDDING_MODEL is changed, update this dimension AND create a new migration.
    embedding = Column(Vector(1024))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    document = relationship("Document", back_populates="chunks")
