# BharatDoc: Full Implementation Plan
> **Source of Truth**: [Master_Prompts.md](file:///c:/Users/moham/Music/New%20folder/Master_Prompts.md)  
> **Progress Tracker**: [_. ANTIGRAVITY WORK LEVEL.md](file:///c:/Users/moham/Music/New%20folder/_.%20ANTIGRAVITY%20WORK%20LEVEL.md)  
> **This File**: The ordered execution plan. Updated after every phase.

---

## Architecture Overview

```
┌─────────────┐      ┌──────────────┐      ┌──────────────┐
│   Frontend   │◄────►│    Caddy      │◄────►│   Backend    │
│ React+Vite   │      │ Reverse Proxy │      │   FastAPI    │
│ TypeScript   │      └──────────────┘      └──────┬───────┘
│ Tailwind     │                                    │
│ shadcn/ui    │                              ┌─────▼──────┐
└─────────────┘                              │  PostgreSQL  │
                                              │  + pgvector  │
                                              └─────┬───────┘
                                                    │
                              ┌──────────┐    ┌─────▼──────┐
                              │  Redis    │◄──►│  Celery     │
                              │  Broker   │    │  Worker     │
                              └──────────┘    └─────────────┘
                                                    │
                                        ┌───────────┼───────────┐
                                        ▼           ▼           ▼
                                   PyMuPDF    PaddleOCR    BGE-M3
                                   (parse)    (OCR)        (embed)
```

**Data Flow**: Upload → Worker (Parse/OCR) → Chunk → Embed → pgvector Store → Query → Retrieve Top-K → Confidence Gate → Extract/Generate → Support Validate → Answer+Citation OR Refusal

---

## Phase Dependency Chain

```
Phase 0 (Planning)
  └─► Phase 1 (Scaffold)
       └─► Phase 2 (Documentation)
            └─► Phase 3 (Auth)
                 └─► Phase 4 (Upload)
                      └─► Phase 5 (Worker Pipeline)
                           ├─► Phase 6 (PDF Extraction)
                           │    └─► Phase 7 (OCR Fallback)
                           │         └─► Phase 8 (Chunking)
                           │              └─► Phase 9 (Embeddings)
                           │                   └─► Phase 10 (Confidence Gate)
                           │                        └─► Phase 11 (Answer Engine)
                           │                             └─► Phase 12 (Support Validator)
                           │                                  └─► Phase 13 (Q&A UI)
                           └─────────────────────────────────────────┘
                                                                      └─► Phase 14 (Security Hardening)
                                                                           └─► Phase 15 (Deployment Pack)
                                                                                └─► Phase 16 (CI/CD)
                                                                                     └─► Phase 17 (Launch Audit)
```

---

## Phase Weight Allocation (for % calculation)

| Phase | Name                   | Weight | Cumulative |
|-------|------------------------|--------|------------|
| 0     | Planning & Setup       | 2%     | 2%         |
| 1     | Scaffold               | 5%     | 7%         |
| 2     | Documentation          | 3%     | 10%        |
| 3     | Authentication         | 8%     | 18%        |
| 4     | Document Upload        | 7%     | 25%        |
| 5     | Worker Pipeline        | 8%     | 33%        |
| 6     | PDF Text Extraction    | 7%     | 40%        |
| 7     | OCR Fallback           | 8%     | 48%        |
| 8     | Chunking               | 5%     | 53%        |
| 9     | Embeddings & Retrieval | 10%    | 63%        |
| 10    | Confidence Gate        | 5%     | 68%        |
| 11    | Answer Engine          | 10%    | 78%        |
| 12    | Support Validator      | 4%     | 82%        |
| 13    | Main Q&A UI            | 6%     | 88%        |
| 14    | Security Hardening     | 4%     | 92%        |
| 15    | Deployment Pack        | 4%     | 96%        |
| 16    | CI/CD                  | 2%     | 98%        |
| 17    | Final Launch Audit     | 2%     | 100%       |

---

## Phase Details

### Phase 0 — Planning & Setup (2%)
**Ref**: Master_Prompts.md Part 1-4 (Agent Upgrade, Memory Governor, Skill Mode, Constitution)

**Deliverables**:
- [x] Parse and internalize Master Prompts Database
- [x] Create Implementation Plan (this file)
- [x] Create Work Level Tracker
- [ ] Get human approval on plan and folder location

**Human Actions Required**: 
- Confirm project folder location (`bharatdoc` subdirectory vs root of `c:\Users\moham\Music\New folder`)
- Say "APPROVED" to proceed to Phase 1

**Review Gate**: N/A (planning only)

---

### Phase 1 — Scaffold (5%)
**Ref**: Master_Prompts.md Part 5, Prompt 1

**Deliverables**:
- Root monorepo: `frontend/`, `backend/`, `infra/`, `docs/`
- Frontend: React + Vite + TypeScript scaffold with placeholder dashboard shell
- Backend: FastAPI scaffold with `GET /health` returning `{"status": "ok"}`
- Infra: `docker-compose.yml` (api + frontend services), `infra/caddy/Caddyfile`
- Docs: Empty memory files (`product_prd.md`, `architecture.md`, `build_status.md`, `decisions.md`, `open_issues.md`, `acceptance_criteria.md`)
- Root: `README.md`, `Makefile`, `.gitignore`
- Per-service: `Dockerfile`, `.env.example`

**Files Created** (estimated ~20 files):
| Path | Purpose |
|------|---------|
| `README.md` | Setup/run instructions |
| `Makefile` | Task shortcuts: `make dev`, `make build`, `make test` |
| `.gitignore` | Standard ignores |
| `docker-compose.yml` | Dev orchestration |
| `backend/main.py` | FastAPI app + `/health` |
| `backend/requirements.txt` | Python deps |
| `backend/Dockerfile` | Python container |
| `backend/.env.example` | Backend env template |
| `frontend/package.json` | Node deps |
| `frontend/vite.config.ts` | Vite config |
| `frontend/tsconfig.json` | TS config |
| `frontend/index.html` | HTML entry |
| `frontend/src/main.tsx` | React entry |
| `frontend/src/App.tsx` | Dashboard shell |
| `frontend/src/App.css` | Base styles |
| `frontend/Dockerfile` | Node container |
| `frontend/.env.example` | Frontend env template |
| `infra/caddy/Caddyfile` | Reverse proxy config |
| `docs/*.md` (×6) | Memory files |

**Verification**:
1. `docker-compose up --build` — all services start
2. `curl http://localhost:8000/health` → `{"status": "ok"}`
3. Browser → `http://localhost:5173` → dashboard shell renders

**Human Actions Required**: None (code only)

**Review Gate**: Self-Critic + No-Scope-Creep

---

### Phase 2 — Documentation (3%)
**Ref**: Master_Prompts.md Part 5, Prompt 2

**Deliverables**:
- `docs/product_prd.md` — MVP scope, user stories, non-goals, acceptance criteria
- `docs/architecture.md` — System diagram, data flow, deployment model, DB schema outline
- `docs/acceptance_criteria.md` — Testable milestones per phase
- `docs/decisions.md` — Initial architecture decisions with rationale
- `docs/build_status.md` — Current phase status (auto-syncs with Work Level tracker)

**Constraints**: No enterprise fantasy. Design for 1 VM, 1 user first.

**Human Actions Required**: Review docs for accuracy against your vision.

**Review Gate**: No-Scope-Creep only

---

### Phase 3 — Authentication (8%)
**Ref**: Master_Prompts.md Part 5, Prompt 3

**Deliverables**:
- Backend: `users` table, Alembic migration, bcrypt hashing, JWT tokens
- Endpoints: `POST /auth/register`, `POST /auth/login`, `GET /auth/me`, `POST /auth/logout`
- Frontend: Login page, Register page, Protected route wrapper, Auth context/state
- Tests: Registration, login, invalid credentials, token expiry, protected route access

**Strict Non-Goals**: No OAuth, no Supabase, no Keycloak, no social login.

**Human Actions Required**: Set `SECRET_KEY` and `DATABASE_URL` in `.env` (template provided).

**Review Gate**: Self-Critic + Adversarial QA + No-Scope-Creep

---

### Phase 4 — Document Upload (7%)
**Ref**: Master_Prompts.md Part 5, Prompt 4

**Deliverables**:
- Backend: `documents` table (id, user_id, filename, mimetype, size, status, created_at, updated_at)
- File validation: magic bytes check, extension whitelist (PDF/PNG/JPG/JPEG), configurable size limit
- Endpoints: `POST /documents/upload`, `GET /documents`, `GET /documents/{id}`, `DELETE /documents/{id}`
- Frontend: Upload form with drag-drop, document list with status badges, delete confirmation
- Storage: Local filesystem with Docker volume mount
- Tests: Upload, list, delete, unauthorized access, invalid file type, oversized file

**Human Actions Required**: None

**Review Gate**: Self-Critic + Adversarial QA + No-Scope-Creep

---

### Phase 5 — Worker Pipeline (8%)
**Ref**: Master_Prompts.md Part 5, Prompt 5

**Deliverables**:
- Redis container in `docker-compose.yml`
- Celery worker service in `docker-compose.yml`
- Upload triggers async processing job
- Placeholder pipeline: fetch file → inspect type → log → mark success/failure
- Status transitions: `uploaded → processing → ready/failed`
- Frontend: Real-time status display (polling or SSE)
- Retry handling with exponential backoff
- Structured logging

**Human Actions Required**: None

**Review Gate**: Self-Critic + Adversarial QA + No-Scope-Creep

---

### Phase 6 — PDF Text Extraction (7%)
**Ref**: Master_Prompts.md Part 5, Prompt 6

**Deliverables**:
- `document_pages` table (document_id, page_number, extracted_text, parser_used, text_length, fallback_needed)
- PyMuPDF page-by-page extraction in worker pipeline
- Low-text heuristic: if page text < configurable threshold chars → mark `fallback_needed=true`
- Idempotent: re-running clears old pages and re-extracts
- Dev endpoint: `GET /documents/{id}/pages`
- Tests with sample digital PDFs

**Human Actions Required**: None

**Review Gate**: Self-Critic + Adversarial QA

---

### Phase 7 — OCR Fallback (8%)
**Ref**: Master_Prompts.md Part 5, Prompt 7

**Deliverables**:
- PaddleOCR integration (primary OCR engine)
- Tesseract fallback if PaddleOCR fails
- Handles: scanned PDFs (render page to image → OCR), image uploads (direct OCR)
- Languages: English + Hindi
- Stores OCR text in `document_pages` with `parser_used='paddleocr'` or `parser_used='tesseract'`
- Quality metadata: confidence score if available
- Graceful degradation if OCR deps missing (logs warning, marks page as failed)

**Human Actions Required**: None (deps bundled in Docker)

**Review Gate**: Self-Critic + Adversarial QA

---

### Phase 8 — Chunking (5%)
**Ref**: Master_Prompts.md Part 5, Prompt 8

**Deliverables**:
- `chunks` table (id, document_id, page_number, chunk_index, text, start_offset, end_offset)
- Configurable via env: `CHUNK_SIZE=512`, `CHUNK_OVERLAP=64`
- No cross-page merging (preserves citation accuracy)
- Idempotent rebuild: delete old chunks before re-chunking
- Dev endpoint: `GET /documents/{id}/chunks`
- Tests for boundary conditions and overlap correctness

**Human Actions Required**: None

**Review Gate**: Self-Critic

---

### Phase 9 — Embeddings & Retrieval (10%)
**Ref**: Master_Prompts.md Part 5, Prompt 9

**Deliverables**:
- Enable `pgvector` extension in PostgreSQL
- `embedding` column on chunks table (vector type of 1024 dimensions)
- BGE-M3 (1024-dim) model loading and embedding generation
- Query embedding → cosine similarity search → top-k results
- **Strict scoping**: WHERE `document_id = :doc_id` AND `user owns document`
- Backfill CLI command for existing documents
- Modular embedding provider abstraction (swap models later)

**Human Actions Required**: None (BGE-M3 downloaded at build/first-run)

> [!WARNING]
> BGE-M3 model is ~2GB. First run will download it. This is the heaviest dependency.

**Review Gate**: Self-Critic + Adversarial QA

---

### Phase 10 — Confidence Gate (5%)
**Ref**: Master_Prompts.md Part 5, Prompt 10

**Deliverables**:
- Deterministic gating module with configurable thresholds
- Inputs: top retrieval score, avg top-k score, lexical overlap ratio
- If below threshold → return exact refusal: *"This information is not present in the uploaded document."*
- If below threshold → **do NOT call answer engine** (saves compute, prevents hallucination)
- Returns: `{passed: bool, external_confidence: float, diagnostics: {...}}`
- Env vars: `CONFIDENCE_THRESHOLD_TOP=0.65`, `CONFIDENCE_THRESHOLD_AVG=0.45`

**Human Actions Required**: None

**Review Gate**: Self-Critic

---

### Phase 11 — Answer Engine (10%)
**Ref**: Master_Prompts.md Part 5, Prompt 11

**Deliverables**:
- **Extraction-first**: If answer span exists verbatim in chunks, return it directly with citation
- **Generation-second**: If synthesis needed, use Ollama (local LLM) with strict system prompt
- System prompt enforces: answer only from context, refuse if unsupported, never invent citations
- **Fallback**: If Ollama unavailable, system works in extractive-only mode + refusal
- Response schema: `{answer, confidence, citations: [{page, chunk_id, text}], status}`

**Human Actions Required**: Optionally install Ollama on the VM (not required — extractive mode works without it)

**Review Gate**: Self-Critic + Adversarial QA + No-Scope-Creep

---

### Phase 12 — Support Validator (4%)
**Ref**: Master_Prompts.md Part 5, Prompt 12

**Deliverables**:
- Post-generation validation: check if answer is grounded in retrieved chunks
- Support labels: `supported`, `partially_supported`, `unsupported`
- If `unsupported` → override with exact refusal phrase
- Citations filtered to only point at supporting chunks
- Logging of rejection reasons

**Human Actions Required**: None

**Review Gate**: Self-Critic + Adversarial QA

---

### Phase 13 — Main Q&A UI (6%)
**Ref**: Master_Prompts.md Part 5, Prompt 13

**Deliverables**:
- Document detail page with metadata
- Question input with submit
- Answer card: answer text, confidence bar, citations list with page refs
- Refusal state: distinct UI treatment (not an error — a trust signal)
- Query history per document
- Loading / error / empty states
- Responsive: mobile-first, desktop-optimized
- API integration layer with typed models

**Human Actions Required**: Test the UI end-to-end as a real user

**Review Gate**: Self-Critic + No-Scope-Creep

---

### Phase 14 — Security Hardening (4%)
**Ref**: Master_Prompts.md Part 5, Prompt 14

**Deliverables**:
- Request body size limits (configurable)
- Rate limiting: auth endpoints (5/min), upload (10/min), query (20/min)
- CORS: restrict to frontend origin
- Trusted hosts middleware
- Audit logging: register, login, upload, query, delete (who, what, when)
- Safe delete: cascade delete document → pages → chunks → embeddings → file
- Tests: unauthorized access, cross-user access, oversized requests

**Human Actions Required**: None

**Review Gate**: Self-Critic + Adversarial QA

---

### Phase 15 — Deployment Pack (4%)
**Ref**: Master_Prompts.md Part 5, Prompt 15

**Deliverables**:
- `docker-compose.prod.yml` with all services
- Caddy config with HTTPS (auto-cert via Let's Encrypt)
- Persistent volumes for: PostgreSQL data, Redis data, uploaded files
- Health checks on all containers
- `env.production.example` with all required vars
- Deployment README: exact SSH commands, DNS setup, backup/restore, rollback

**Human Actions Required**:
1. Create a VM (any cloud provider)
2. Install Docker + Docker Compose
3. Point domain DNS to VM IP
4. Copy `.env.production` with real secrets
5. Run `docker-compose -f docker-compose.prod.yml up -d`

**Review Gate**: Self-Critic

---

### Phase 16 — CI/CD (2%)
**Ref**: Master_Prompts.md Part 5, Prompt 16

**Deliverables**:
- `.github/workflows/ci.yml`: lint, test, build Docker images
- `.github/workflows/deploy.yml`: optional SSH deploy on push to `main`
- Post-deploy health check step
- Required secrets checklist documented
- Rollback strategy notes

**Human Actions Required**:
1. Create GitHub repo
2. Add secrets (SSH key, server IP, etc.) to GitHub Settings

**Review Gate**: Self-Critic

---

### Phase 17 — Final Launch Audit (2%)
**Ref**: Master_Prompts.md Part 5, Prompt 17

**Deliverables**:
- Full system audit across all 16 prior phases
- Go / No-Go recommendation
- Blocker list (must-fix before first user)
- Known limitations (acceptable for v1)
- Day-1 operations guide (logs, restart, backup)
- Launch checklist
- Top 10 improvements for after first paying user

**Human Actions Required**: Final deploy, first user test, payment setup

**Review Gate**: All three reviews (Self-Critic, Adversarial QA, No-Scope-Creep)

---

## Post-Launch: Business & GTM (Not Tracked in Build %)
**Ref**: Master_Prompts.md Parts 7-8

After Phase 17 ships, these prompts are executed:
1. **Credentials Checklist** — every account/secret needed
2. **Deployment Supervisor** — step-by-step for human
3. **Go-Live Dry Run** — simulated user journey
4. **Business Strategy** — ICP, use cases, pricing, sales scripts
5. **Revenue Model** — plans, limits, ₹10K → ₹1L/month paths
6. **Go-to-Market** — 90-day zero-budget plan

These are run as separate prompts after MVP ships. They don't block development.

---

## Review Protocol (runs after every phase)

From Master_Prompts.md Part 6:

| Review | What It Checks | When |
|--------|---------------|------|
| **Self-Critic** | Broken imports, missing migrations, auth bypass, data isolation, race conditions, error handling, tests | Every phase |
| **Adversarial QA** | Happy path, edge cases, abuse, unauthorized access, data leakage, failure recovery | Phases 3-14 |
| **No-Scope-Creep** | Unnecessary abstractions, premature complexity, features not needed for MVP | Phases 1, 3, 4, 5, 11, 13 |

---

## Human Supervisor Actions Summary

| When | What You Do |
|------|-------------|
| Phase 0 | Confirm folder location, say "APPROVED" |
| Phase 3 | Set `SECRET_KEY` and `DATABASE_URL` in `.env` |
| Phase 15 | Create VM, install Docker, point DNS, copy `.env.production` |
| Phase 16 | Create GitHub repo, add secrets |
| Phase 17 | Final deploy, test as user, set up payments |
| Every phase end | Say "APPROVED" to proceed |

Everything else is built by the agent.
