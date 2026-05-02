# BharatDoc Architecture

## System Architecture
A single-VM monolith with a worker queue for document processing.

- **Frontend**: React + Vite + TypeScript + Tailwind + shadcn/ui.
- **Backend**: FastAPI + Python.
- **Database**: PostgreSQL with pgvector for relational data and embeddings.
- **Worker/Queue**: Redis + Celery for background parsing and OCR.
- **Proxy/Web Server**: Caddy acting as reverse proxy with automatic HTTPS.
- **Deployment**: Docker Compose.

## Data Flow
1. **Upload**: User uploads file via frontend -> API stores metadata in DB and raw file on disk -> Enqueues task.
2. **Parsing**: Worker picks up task -> PyMuPDF extracts text -> Low-text pages sent to PaddleOCR/Tesseract.
3. **Chunking & Embedding**: Extracted text chunked -> Embedded via BGE-M3 model -> Stored in pgvector.
4. **Query**: User asks question -> Query embedded -> Cosine similarity search on pgvector -> Top-K chunks retrieved.
5. **Confidence Gate**: System checks retrieval confidence -> If too low, immediately refuse.
6. **Answer Synthesis**: If extractive, return span. If generative, query local Ollama model with strict context.
7. **Support Validation**: Check generated answer against chunks -> Override with refusal if unsupported.

## Deployment Model
- Target: Single VM (minimum 4GB RAM, 2 vCPUs).
- All components run in Docker containers orchestrated by Docker Compose.
- Persistent volumes mapped for PostgreSQL, Redis, and raw uploaded files.
