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
    Placeholder pipeline for Phase 5.
    Transitions document from uploaded -> processing -> ready/failed.
    """
    logger.info(f"Starting processing for document {document_id}")
    
    db: Session = SessionLocal()
    try:
        # Fetch document
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            logger.error(f"Document {document_id} not found")
            return {"status": "error", "message": "Document not found"}
        
        # Mark as processing
        doc.status = DocumentStatus.processing
        db.commit()
        logger.info(f"Document {document_id} marked as processing")
        
        # Placeholder processing logic (simulate work)
        logger.info(f"Inspecting file: {doc.file_path}")
        time.sleep(3) # Simulate parsing delay
        
        if not os.path.exists(doc.file_path):
            raise FileNotFoundError(f"File {doc.file_path} missing from disk")
            
        # File size logging
        file_size = os.path.getsize(doc.file_path)
        logger.info(f"Document {document_id} size: {file_size} bytes")
        
        # Mark as ready
        doc.status = DocumentStatus.ready
        db.commit()
        logger.info(f"Document {document_id} marked as ready")
        
        return {"status": "success", "document_id": document_id}
        
    except Exception as exc:
        logger.error(f"Error processing document {document_id}: {exc}")
        # Transition to failed
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.status = DocumentStatus.failed
            db.commit()
            
        # Retry with exponential backoff (e.g., 5s, 25s, 125s)
        raise self.retry(exc=exc, countdown=5 ** self.request.retries)
    finally:
        db.close()
