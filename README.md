# BharatDoc — Intelligent Document Q&A Platform

BharatDoc is an advanced, fully containerized Document Intelligence platform built for securely processing, embedding, and interacting with documents via highly accurate AI Q&A. Designed for offline capability and strict privacy, BharatDoc utilizes state-of-the-art local semantic vector embeddings combined with a strict "Confidence Gate" to prevent AI hallucinations.

## 🚀 Features

- **End-to-End Containerization**: Runs completely in Docker (Frontend, Backend, Postgres+pgvector, Redis, Celery Worker, Caddy Proxy).
- **Secure Authentication**: JWT-based stateless authentication with strict route protection.
- **Advanced Document Parsing**: Multilingual PDF OCR support using PaddleOCR and PyMuPDF.
- **High-Precision Embeddings**: Uses `BAAI/bge-m3` (1024-dimensional) via `sentence-transformers` for precise English/Hindi semantic representation.
- **Dual-Mode AI Q&A**:
  - **Quick Summary**: Relaxed local generative AI using lightweight models (`google/flan-t5-base`) for fast, offline document summarization.
  - **Strict Audit**: Strict Cross-Encoder validation (`cross-encoder/ms-marco-MiniLM-L-6-v2`) to ensure factual queries are directly supported by the document, refusing to answer if the confidence is too low.
- **Complete Privacy**: No external API keys are required for the core document processing and inference loop. Everything runs on your own hardware.

---

## 🏗️ Architecture

- **Frontend**: React + TypeScript + Vite + TailwindCSS
- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL 16 with `pgvector` extension
- **Background Jobs**: Celery + Redis
- **Reverse Proxy**: Caddy

---

## 💻 Local Development

### Prerequisites
- Docker and Docker Compose
- Node.js (if running frontend outside docker)
- Python 3.10+ (if running backend outside docker)

### Running with Docker Compose (Recommended)
1. Clone the repository:
   ```bash
   git clone https://github.com/Inayat-0007/BharatDoc.git
   cd BharatDoc
   ```
2. Start the entire stack:
   ```bash
   docker compose up -d --build
   ```
3. Access the application:
   - Go to `http://localhost` in your browser.
   - The API is available at `http://localhost/api` (Swagger docs at `http://localhost/api/docs`).

---

## 🌍 Production Deployment

BharatDoc is fully equipped for VM/VPS deployments (e.g., AWS EC2, DigitalOcean, Azure).

1. Copy `.env.production.example` to `.env`:
   ```bash
   cp .env.production.example .env
   # Edit .env and securely generate a new SECRET_KEY and DB Password.
   ```
2. Modify `docker-compose.prod.yml` and `infra/caddy/Caddyfile.prod` to use your domain name.
3. Start the production stack:
   ```bash
   docker compose -f docker-compose.prod.yml up -d --build
   ```

---

## 🛡️ The "Confidence Gate"

BharatDoc differentiates itself from generic AI wrappers by implementing a strict Confidence Gate.
- It calculates semantic distance, average chunk distance, and uses a Cross-Encoder for deep relevance scoring.
- If a query does not map to factual evidence in the text, the engine deterministicly responds: *"This information is not present in the uploaded document."*
- Generative extraction operates strictly on the retrieved context, preventing hallucinated answers.

---

## 📜 License
Internal / Proprietary. Copyright © 2026. All Rights Reserved.
