import os
import time
import logging
from celery import Celery
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Document, DocumentStatus

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "worker",
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600, # 1 hour max
)

@celery_app.task(bind=True, max_retries=3)
def process_document(self, document_id: int):
    """
    Phase 6 pipeline: extracts text from PDF page by page.
    """
    import fitz # PyMuPDF
    from models import DocumentPage
    
    logger.info(f"Starting processing for document {document_id}")
    
    db: Session = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            return {"status": "error", "message": "Document not found"}
        
        doc.status = DocumentStatus.processing
        db.commit()
        
        if not os.path.exists(doc.file_path):
            raise FileNotFoundError(f"File {doc.file_path} missing")
            
        # Delete old pages if reprocessing
        db.query(DocumentPage).filter(DocumentPage.document_id == document_id).delete()
        db.commit()
        
        # Only process PDFs for now
        if doc.content_type == "application/pdf":
            logger.info(f"Extracting text from PDF: {doc.file_path}")
            pdf_doc = fitz.open(doc.file_path)
            
            for page_num in range(len(pdf_doc)):
                page = pdf_doc.load_page(page_num)
                text = page.get_text()
                
                # Low-text heuristic: if < 50 chars, mark fallback_needed (for OCR later)
                fallback = len(text.strip()) < 50
                
                doc_page = DocumentPage(
                    document_id=document_id,
                    page_number=page_num + 1,
                    text_content=text,
                    fallback_needed=fallback
                )
                db.add(doc_page)
            
            pdf_doc.close()
            db.commit()
            logger.info(f"Extracted {len(pdf_doc)} pages for document {document_id}")
        else:
            logger.info(f"Document {document_id} is not a PDF. Skipping extraction.")
            
        doc.status = DocumentStatus.ready
        db.commit()
        
        return {"status": "success", "document_id": document_id}
        
    except Exception as exc:
        logger.error(f"Error processing document {document_id}: {exc}")
        db.rollback()
        
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.status = DocumentStatus.failed
            db.commit()
            
        raise self.retry(exc=exc, countdown=5 ** self.request.retries)
    finally:
        db.close()
