from pydantic import BaseModel, EmailStr
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

from typing import Optional

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
