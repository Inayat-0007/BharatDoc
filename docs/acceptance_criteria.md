# Testable Milestones (Acceptance Criteria)

- **Phase 3 (Auth)**: Users can successfully register, log in, and hit a protected route.
- **Phase 4 (Upload)**: Files up to a configurable limit can be uploaded, stored, and deleted.
- **Phase 5 (Worker)**: Uploads trigger a Redis/Celery job that successfully updates status to 'ready'.
- **Phase 6 (PDF Extraction)**: Text is successfully extracted page-by-page from a digital PDF and saved to DB.
- **Phase 7 (OCR)**: Scanned image uploads are correctly converted to text by PaddleOCR and saved.
- **Phase 8 (Chunking)**: Extracted text is divided into overlapping chunks without crossing page boundaries.
- **Phase 9 (Embeddings)**: Chunks are successfully embedded by BGE-M3 and retrievable via pgvector similarity search.
- **Phase 10 (Confidence Gate)**: Questions completely unrelated to the text are predictably rejected with the exact refusal phrase.
- **Phase 11 (Answer Engine)**: Valid questions receive an accurate answer derived strictly from the text.
- **Phase 12 (Validator)**: Generated answers that hallucinate are caught and overridden with the refusal phrase.
- **Phase 13 (UI)**: The frontend fully allows uploading, status polling, asking questions, viewing citations, and deleting.
- **Phase 14 (Security)**: Rate limits enforce, and trying to access another user's document via ID returns 404/403.
- **Phase 15 (Deployment)**: The `docker-compose.prod.yml` successfully boots the entire stack on a fresh system.
