# Open Issues and Risks

## Current Risks
1. **Model Download Size**: BGE-M3 and PaddleOCR models are quite large. We need to handle the first-run download gracefully so the worker doesn't time out.
2. **RAM Usage on Single VM**: Running PostgreSQL, Celery, FastAPI, React, and potentially Ollama on a single VM could lead to Out of Memory (OOM) kills. We need memory limits in Docker Compose.
3. **Hindi OCR Accuracy**: Needs testing with real-world low-quality mobile scans.
4. **Chunk Size Tuning**: 512 tokens might be too big or small depending on the document density and citation granularity required.

## Deferred Items
- Full text search (FTS) in PostgreSQL as a fallback to vector search.
- User email verification and password reset flows (to keep MVP simple, assuming manual onboarding or trusted users).
- Cloud storage (S3/MinIO) migration.
