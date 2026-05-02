from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str | None = None

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
