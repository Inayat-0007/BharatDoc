import os
import shutil
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from database import get_db
import models, schemas, auth

router = APIRouter(prefix="/documents", tags=["documents"])

UPLOAD_DIR = "/app/uploads"
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
ALLOWED_MIME_TYPES = {"application/pdf", "image/png", "image/jpeg"}
MAX_FILE_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", 10 * 1024 * 1024)) # 10MB

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", response_model=schemas.DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Validate extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file extension")

    # 2. Validate MIME type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    # 3. Read and check file size
    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large")
    
    # 4. Save file to disk
    # To prevent overwriting, we can prepend a timestamp or UUID to the filename
    safe_filename = f"{current_user.id}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    
    with open(file_path, "wb") as f:
        f.write(file_content)
        
    # 5. Create database record
    new_doc = models.Document(
        filename=file.filename,
        file_path=file_path,
        content_type=file.content_type,
        user_id=current_user.id
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)
    
    # 6. Trigger background processing
    from worker import process_document
    process_document.delay(new_doc.id)
    
    return new_doc

@router.get("", response_model=List[schemas.DocumentResponse])
def get_documents(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    docs = db.query(models.Document).filter(models.Document.user_id == current_user.id).order_by(models.Document.created_at.desc()).all()
    return docs

@router.get("/{doc_id}", response_model=schemas.DocumentResponse)
def get_document(
    doc_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    doc = db.query(models.Document).filter(
        models.Document.id == doc_id, 
        models.Document.user_id == current_user.id
    ).first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    return doc

@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    doc_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    doc = db.query(models.Document).filter(
        models.Document.id == doc_id, 
        models.Document.user_id == current_user.id
    ).first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    # Delete the physical file
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)
        
    # Delete DB record
    db.delete(doc)
    db.commit()
    
    return None

@router.get("/{document_id}/pages", response_model=List[schemas.DocumentPageResponse])
def get_document_pages(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Get all extracted pages for a document.
    """
    document = db.query(models.Document).filter(
        models.Document.id == document_id,
        models.Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
        
    pages = db.query(models.DocumentPage).filter(
        models.DocumentPage.document_id == document_id
    ).order_by(models.DocumentPage.page_number).all()
    
    return pages

@router.get("/{document_id}/chunks", response_model=List[schemas.DocumentChunkResponse])
def get_document_chunks(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Get all extracted chunks for a document.
    """
    document = db.query(models.Document).filter(
        models.Document.id == document_id,
        models.Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
        
    chunks = db.query(models.DocumentChunk).filter(
        models.DocumentChunk.document_id == document_id
    ).order_by(models.DocumentChunk.page_number, models.DocumentChunk.chunk_index).all()
    
    return chunks
