# Architecture Decisions

## 1. Single VM + Docker Compose
**Decision**: We will deploy everything to a single VM using Docker Compose.
**Rationale**: Keeps operational complexity to an absolute minimum for a solo founder. No Kubernetes overhead.

## 2. Local File Storage
**Decision**: Raw uploaded documents will be stored on a local Docker volume.
**Rationale**: Avoids the complexity and configuration required for S3/MinIO in the MVP stage.

## 3. Extract-First, Local-LLM Second
**Decision**: The system will attempt to extract exact spans from the text before falling back to Ollama.
**Rationale**: Increases speed, reduces hallucination, and avoids cloud API costs. Guarantees 100% privacy.

## 4. PaddleOCR + Tesseract Fallback
**Decision**: PaddleOCR is the primary OCR engine, with Tesseract as backup.
**Rationale**: PaddleOCR has better accuracy, especially for languages like Hindi, which is a core requirement for BharatDoc.

## 5. Explicit Refusal Gate
**Decision**: An explicit confidence gate will sit before the answer engine.
**Rationale**: Enforces the privacy/trust product positioning. It's better to refuse to answer than to hallucinate.

## 6. Email/Password Auth Only
**Decision**: Custom email/password auth using JWT, no OAuth.
**Rationale**: Simplifies initial deployment without needing to set up third-party OAuth apps or rely on external identity providers.
