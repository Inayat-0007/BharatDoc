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
            
            # Setup OCR if enabled
            use_ocr = os.getenv("USE_OCR", "true").lower() == "true"
            ocr_engine = None
            if use_ocr:
                try:
                    from paddleocr import PaddleOCR
                    ocr_engine = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
                    logger.info("PaddleOCR initialized successfully.")
                except Exception as e:
                    logger.warning(f"PaddleOCR failed to initialize: {e}. Falling back to pytesseract.")
                    ocr_engine = "tesseract"

            for page_num in range(len(pdf_doc)):
                page = pdf_doc.load_page(page_num)
                text = page.get_text()
                
                # Low-text heuristic: if < 50 chars, mark fallback_needed
                fallback = len(text.strip()) < 50
                parser_used = "pymupdf"
                
                if fallback and use_ocr:
                    logger.info(f"Page {page_num+1} has low text. Running OCR fallback.")
                    # Render page to image
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) # 2x zoom for better OCR
                    
                    if ocr_engine != "tesseract" and ocr_engine is not None:
                        # PaddleOCR
                        try:
                            import numpy as np
                            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
                            if pix.n == 4:
                                img = img[:, :, :3] # drop alpha
                            
                            result = ocr_engine.ocr(img, cls=True)
                            ocr_text = ""
                            if result and result[0]:
                                for line in result[0]:
                                    ocr_text += line[1][0] + "\n"
                            
                            text = ocr_text
                            fallback = False
                            parser_used = "paddleocr"
                        except Exception as e:
                            logger.error(f"PaddleOCR error on page {page_num+1}: {e}")
                    
                    if parser_used == "pymupdf": # If paddle failed or using tesseract
                        try:
                            from PIL import Image
                            import io
                            import pytesseract
                            img = Image.open(io.BytesIO(pix.tobytes("png")))
                            ocr_text = pytesseract.image_to_string(img)
                            text = ocr_text
                            fallback = False
                            parser_used = "tesseract"
                        except Exception as e:
                            logger.error(f"Tesseract error on page {page_num+1}: {e}")
                
                doc_page = DocumentPage(
                    document_id=document_id,
                    page_number=page_num + 1,
                    text_content=text,
                    fallback_needed=fallback,
                    parser_used=parser_used
                )
                db.add(doc_page)
            
            pdf_doc.close()
            db.commit()
            logger.info(f"Extracted {len(pdf_doc)} pages for document {document_id}")
            
        elif doc.content_type in ["image/png", "image/jpeg", "image/jpg"]:
            logger.info(f"Extracting text from Image: {doc.file_path}")
            
            # Setup OCR if enabled
            use_ocr = os.getenv("USE_OCR", "true").lower() == "true"
            ocr_engine = None
            if use_ocr:
                try:
                    from paddleocr import PaddleOCR
                    ocr_engine = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
                except Exception as e:
                    ocr_engine = "tesseract"
                    
            text = ""
            fallback = True
            parser_used = "none"
            
            if use_ocr:
                if ocr_engine != "tesseract" and ocr_engine is not None:
                    try:
                        import cv2
                        img = cv2.imread(doc.file_path)
                        result = ocr_engine.ocr(img, cls=True)
                        if result and result[0]:
                            for line in result[0]:
                                text += line[1][0] + "\n"
                        fallback = False
                        parser_used = "paddleocr"
                    except Exception as e:
                        logger.error(f"PaddleOCR error on image: {e}")
                
                if parser_used == "none":
                    try:
                        from PIL import Image
                        import pytesseract
                        img = Image.open(doc.file_path)
                        text = pytesseract.image_to_string(img)
                        fallback = False
                        parser_used = "tesseract"
                    except Exception as e:
                        logger.error(f"Tesseract error on image: {e}")
                        
            doc_page = DocumentPage(
                document_id=document_id,
                page_number=1,
                text_content=text,
                fallback_needed=fallback,
                parser_used=parser_used
            )
            db.add(doc_page)
            db.commit()
            
        else:
            logger.info(f"Document {document_id} is not supported. Skipping extraction.")
            
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
