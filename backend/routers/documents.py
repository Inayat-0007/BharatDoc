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

@router.post("/search", response_model=List[schemas.DocumentSearchResult])
def search_documents(
    request: schemas.DocumentSearchRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Search document chunks using vector embeddings.
    """
    from embedding_service import embedding_service
    
    # Generate query embedding
    query_embedding = embedding_service.get_embedding(request.query)
    
    # Base query for chunks belonging to user's documents
    base_query = db.query(models.DocumentChunk, models.Document.filename).join(
        models.Document, models.DocumentChunk.document_id == models.Document.id
    ).filter(models.Document.user_id == current_user.id)
    
    # Filter by specific documents if provided
    if request.document_ids:
        base_query = base_query.filter(models.DocumentChunk.document_id.in_(request.document_ids))
        
    # pgvector cosine distance: embedding.cosine_distance(query_embedding)
    # Cosine similarity is 1 - cosine_distance
    distance_col = models.DocumentChunk.embedding.cosine_distance(query_embedding).label("distance")
    
    results = base_query.add_columns(distance_col).order_by(
        distance_col
    ).limit(request.top_k).all()
    
    search_results = []
    for chunk, filename, distance in results:
        search_results.append({
            "chunk": chunk,
            "similarity": 1.0 - float(distance) if distance is not None else 0.0,
            "document_filename": filename
        })
        
    return search_results

@router.post("/query", response_model=schemas.QueryResponse)
def query_document(
    request: schemas.QueryRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Phase 10: Gated document Q&A endpoint.
    
    1. Retrieves top-k chunks via vector similarity
    2. Runs results through the confidence gate
    3. If gate FAILS → returns exact refusal phrase
    4. If gate PASSES → returns extractive answer from top chunks
    """
    from embedding_service import embedding_service
    from confidence_gate import confidence_gate, RetrievalResult, REFUSAL_PHRASE
    
    # Verify document belongs to user
    document = db.query(models.Document).filter(
        models.Document.id == request.document_id,
        models.Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if document.status != models.DocumentStatus.ready:
        raise HTTPException(status_code=400, detail="Document is not ready for queries")
    
    # Step 1: Vector retrieval
    query_embedding = embedding_service.get_embedding(request.query)
    
    distance_col = models.DocumentChunk.embedding.cosine_distance(query_embedding).label("distance")
    
    results = db.query(models.DocumentChunk).filter(
        models.DocumentChunk.document_id == request.document_id,
        models.DocumentChunk.embedding.isnot(None)
    ).add_columns(distance_col).order_by(
        distance_col
    ).limit(request.top_k).all()
    
    # Convert to RetrievalResult objects for the gate
    retrieval_results = []
    for chunk, distance in results:
        similarity = 1.0 - float(distance) if distance is not None else 0.0
        retrieval_results.append(RetrievalResult(
            text=chunk.text,
            similarity=similarity,
            document_id=chunk.document_id,
            page_number=chunk.page_number,
            chunk_index=chunk.chunk_index
        ))
    
    # Step 2: Confidence gate
    gate_result = confidence_gate.evaluate(request.query, retrieval_results)
    
    if not gate_result.passed:
        return schemas.QueryResponse(
            status="refused",
            answer=None,
            confidence=gate_result.confidence_score,
            citations=[],
            refusal_message=gate_result.refusal_message,
            diagnostics=gate_result.diagnostics
        )
    
    # Step 3: Answer Engine (Phase 11)
    from answer_engine import answer_engine
    
    chunks_for_engine = [
        {
            "text": r.text,
            "page_number": r.page_number,
            "chunk_index": r.chunk_index,
            "similarity": r.similarity
        }
        for r in retrieval_results
    ]
    
    answer_result = answer_engine.generate_answer(
        query=request.query,
        chunks=chunks_for_engine,
        confidence_score=gate_result.confidence_score
    )
    
    citations = [
        schemas.Citation(
            page_number=r.page_number,
            chunk_index=r.chunk_index,
            text=r.text[:200],
            similarity=round(r.similarity, 4)
        )
        for r in retrieval_results
    ]
    
    diagnostics = gate_result.diagnostics
    diagnostics["answer_mode"] = answer_result.mode
    
    # Step 4: Support Validator (Phase 12)
    from support_validator import support_validator
    
    validation = support_validator.validate(
        answer=answer_result.answer,
        chunks=chunks_for_engine,
        query=request.query
    )
    
    diagnostics["support_level"] = validation.level.value
    diagnostics["coverage_score"] = validation.coverage_score
    diagnostics["validation"] = validation.diagnostics
    if validation.rejection_reasons:
        diagnostics["rejection_reasons"] = validation.rejection_reasons
    
    # If unsupported → override answer with refusal
    if validation.level.value == "unsupported":
        return schemas.QueryResponse(
            status="refused",
            answer=None,
            confidence=gate_result.confidence_score,
            support_level=validation.level.value,
            answer_mode=answer_result.mode,
            citations=[],
            refusal_message=REFUSAL_PHRASE,
            diagnostics=diagnostics
        )
    
    # Filter citations to only supporting chunks
    citations = []
    for i, r in enumerate(retrieval_results):
        if i in validation.supporting_chunk_indices:
            citations.append(
                schemas.Citation(
                    page_number=r.page_number,
                    chunk_index=r.chunk_index,
                    text=r.text[:200],
                    similarity=round(r.similarity, 4)
                )
            )
    
    # If no supporting citations found, include all (extractive mode is inherently supported)
    if not citations:
        citations = [
            schemas.Citation(
                page_number=r.page_number,
                chunk_index=r.chunk_index,
                text=r.text[:200],
                similarity=round(r.similarity, 4)
            )
            for r in retrieval_results
        ]
    
    return schemas.QueryResponse(
        status="answered",
        answer=validation.validated_answer,
        confidence=gate_result.confidence_score,
        support_level=validation.level.value,
        answer_mode=answer_result.mode,
        citations=citations,
        refusal_message=None,
        diagnostics=diagnostics
    )
