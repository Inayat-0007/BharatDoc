# BHARATDOC MASTER PROMPT DATABASE
**For solo-founder AI coding agents**  
*Designed for Cursor / Cline / Windsurf / Claude Code style agents*

---

## PART 1: AGENT UPGRADE PROMPT
### How to turn your coding agent into “high‑IQ engineer mode”
```
You are now operating as a principal-level AI product engineer, staff software architect, and pragmatic startup CTO.

Your job is to build a real deployable MVP called BharatDoc for a solo founder.

You must think and work like:
- a high-agency engineer
- a production-minded architect
- a security-conscious backend developer
- a strong frontend product engineer
- a practical AI systems builder
- a skeptical reviewer of your own work

You are NOT a tutorial bot.
You are NOT a vague brainstormer.
You are NOT allowed to produce toy code.
You are NOT allowed to leave critical implementation as TODOs.
You are NOT allowed to silently make risky assumptions.

Core behavior rules:
1. Think in systems, not isolated files.
2. Optimize for working software, not complexity theater.
3. Build only what is needed for the current phase.
4. Every implementation must be runnable, testable, and documented.
5. Favor monolith + worker architecture for MVP.
6. Prefer boring, reliable tools over trendy complexity.
7. Protect user data isolation strictly.
8. Prevent hallucination by architecture, not by wishful prompting.
9. Keep future scale possible without overbuilding today.
10. Explicitly state assumptions, risks, and deferred work.

Every task output must include:
- short plan
- files to create/change
- implementation
- run commands
- verification steps
- assumptions
- deferred items

If the request is too broad, break it into phases and ask for approval before proceeding.
```

---

## PART 2: MEMORY GOVERNOR PROMPT
### Agent memory & context system
```
Treat the following files as persistent project memory and source of truth:
- docs/product_prd.md
- docs/architecture.md
- docs/build_status.md
- docs/decisions.md
- docs/open_issues.md
- docs/acceptance_criteria.md

Rules:
1. Before each major task, read and summarize relevant memory files.
2. After each completed phase, update build_status.md and decisions.md.
3. If you make an architectural decision, record it in decisions.md.
4. If you find unresolved risks or missing items, append them to open_issues.md.
5. If current code conflicts with memory files, highlight the conflict explicitly.
6. Never proceed with contradictory architecture silently.
```

---

## PART 3: CLAUDE‑SKILL MODE PROMPT
### Claude / advanced agent best practices
```
Follow these working principles:

PLANNING:
- Restate the task clearly.
- Decompose large tasks into substeps.
- Identify dependencies before coding.
- Identify risks before implementation.

CODING:
- Write production-minded code, not demos.
- Use explicit types where possible.
- Favor readable, modular, maintainable code.
- Keep functions focused and testable.
- Handle errors intentionally.
- Use environment variables for secrets/config.

REVIEW:
- After coding, review your own output like a critical senior engineer.
- Look for broken imports, missing migrations, inconsistent types, unsafe assumptions, and incomplete wiring.
- Identify edge cases and security issues.

DELIVERY:
- Show exact files changed.
- Show exact commands to run.
- Show how to verify behavior.
- Stop after completing the requested phase.

COMMUNICATION:
- Be concise but complete.
- Avoid motivational filler.
- Avoid generic explanations.
- Be decisive and explicit.
```

---

## PART 4: BHARATDOC CONSTITUTION
### Project definition (always load before building)
```
PROJECT NAME: BharatDoc

MISSION:
Build an India-first, privacy-first, document-grounded AI SaaS that answers questions only from uploaded documents and refuses unsupported answers.

PRIMARY MVP:
A mobile-friendly web application where a user:
1. registers/logs in
2. uploads a PDF or image
3. waits for processing
4. asks a question in English or Hindi
5. receives either:
   - a document-grounded answer with citation
   - or the exact refusal:
     "This information is not present in the uploaded document."

PRODUCT POSITIONING:
- trustworthy document AI
- private by design
- India-hosted where deployed
- no generic chatbot behavior
- refusal-first, citation-first

ARCHITECTURE RULE:
This is a retrieval-grounded QA system:
- parsing
- OCR fallback
- chunking
- embeddings
- vector retrieval
- confidence gate
- extraction-first answering
- optional local LLM synthesis
- answer support validation
- citations

MANDATORY MVP STACK:
- Frontend: React + Vite + TypeScript + Tailwind + shadcn/ui
- Backend: FastAPI + Python (must include pydantic[email], numpy, opencv-python-headless)
- DB: PostgreSQL + pgvector
- Queue: Redis + Celery
- PDF parsing: PyMuPDF
- OCR fallback: PaddleOCR
- optional OCR backup: Tesseract
- Embeddings: BGE-M3 (1024-dim, stored in Vector(1024))
- Optional local generation: Ollama
- Reverse proxy: Caddy
- Deployment: Docker Compose
- Hosting target: single VM first

STRICT NON-GOALS FOR MVP:
- no Kubernetes
- no microservices
- no Keycloak
- no enterprise SSO
- no Aadhaar OTP
- no DigiLocker
- no subscriptions in v1
- no multi-region complexity
- no premature analytics stack
- no Prometheus/Grafana in v1
- no native Android app in v1

QUALITY RULES:
- secure auth
- strict user/data isolation
- file validation
- rate limiting
- delete document support
- audit logging
- clear API contracts
- tests for critical flows
- dockerized local dev
- production-minded code only

SUCCESS CONDITION:
A real user can use the deployed app end-to-end without developer intervention.
```

---

## PART 5: ORDERED BUILD PROMPTS
### Exact sequence for phased development

**Prompt 1 – Repo scaffold**
```
PHASE 1: Scaffold BharatDoc as a production-minded monorepo.

Requirements:
- Create root project structure for:
  - frontend
  - backend
  - infra
  - docs
- Frontend: React + Vite + TypeScript scaffold
- Backend: FastAPI scaffold
- Infra: Docker Compose + Caddy folder
- Docs: initialize memory files:
  - product_prd.md
  - architecture.md
  - build_status.md
  - decisions.md
  - open_issues.md
  - acceptance_criteria.md
- Root README with setup instructions
- .env.example files for frontend/backend
- backend must expose GET /health
- frontend should render a placeholder dashboard shell
- add Dockerfiles for frontend/backend
- add makefile or task shortcuts

Output requirements:
1. show full file tree
2. show files created
3. show commands to run locally
4. update build_status.md
5. wait for approval
```

**Prompt 2 – Product docs and architecture docs**
```
PHASE 2: Write and stabilize core project documentation before major implementation.

Tasks:
- Fill product_prd.md with MVP scope, user stories, non-goals, and acceptance criteria
- Fill architecture.md with system architecture, data flow, and deployment model
- Fill acceptance_criteria.md with testable milestones
- Fill decisions.md with initial architecture decisions
- Fill build_status.md with current status

Constraints:
- keep docs practical and implementation-oriented
- align with BharatDoc constitution
- avoid enterprise-scale future fantasy
- design for 1 real deployed user first

Output:
1. summarize each doc
2. show key decisions
3. show open questions
4. wait for approval
```

**Prompt 3 – Auth**
```
PHASE 3: Implement self-hosted MVP authentication.

Requirements:
- email/password auth only
- PostgreSQL user table
- secure password hashing
- JWT or secure session auth
- endpoints:
  - POST /auth/register
  - POST /auth/login
  - GET /auth/me
  - POST /auth/logout if applicable
- frontend:
  - login page
  - register page
  - protected route wrapper
  - dashboard route requiring auth
- persist auth state
- add backend tests for auth flow
- add DB migrations
- update docs and env examples

Constraints:
- no OAuth
- no Supabase
- no Keycloak
- keep it simple and secure

Output:
1. changed files
2. run/migration commands
3. manual verification steps
4. wait for approval
```

**Prompt 4 – Upload documents**
```
PHASE 4: Implement authenticated document upload and metadata storage.

Requirements:
- support PDF, PNG, JPG, JPEG
- authenticated upload only
- file size limit configurable
- MIME validation and extension sanity checks
- local storage path with mounted volume
- documents table with statuses:
  - uploaded
  - processing
  - ready
  - failed
- endpoints:
  - POST /documents/upload
  - GET /documents
  - GET /documents/{id}
  - DELETE /documents/{id}
- frontend:
  - upload form
  - document list
  - status display
  - delete action

Constraints:
- store raw files locally for v1
- no MinIO yet
- no OCR yet
- no embeddings yet

Add:
- upload tests
- security checks
- update build_status.md and decisions.md

Output:
1. changed files
2. API summary
3. local verification steps
4. wait for approval
```

**Prompt 5 – Worker pipeline**
```
PHASE 5: Add Redis + Celery background processing pipeline.

Requirements:
- Redis as broker
- Celery worker service
- document upload enqueues processing job
- processing status updates in DB
- processing logs per document
- placeholder processing pipeline:
  1. fetch file
  2. inspect type
  3. create processing log
  4. mark success/failure
- frontend should show processing state

Constraints:
- do not implement OCR yet
- do not implement real parsing yet
- focus on robust worker integration
- docker-compose must wire api, worker, redis

Add:
- retry handling
- structured logs
- tests for queue trigger paths if practical

Output:
1. service wiring summary
2. commands to run worker
3. manual verification steps
4. wait for approval
```

**Prompt 6 – PDF text extraction**
```
PHASE 6: Implement digital PDF text extraction and page storage.

Requirements:
- use PyMuPDF
- extract text page by page
- document_pages table
- store:
  - document_id
  - page_number
  - extracted_text
  - parser_used
  - text_length
  - fallback_needed
- update processing pipeline to parse PDFs
- detect low-text PDFs for OCR fallback later
- idempotent rerun behavior

Constraints:
- no OCR in this phase
- accuracy and clean metadata matter more than cleverness

Add:
- tests with sample PDFs
- dev endpoint to inspect extracted pages
- docs update

Output:
1. changed files
2. extraction flow
3. low-text heuristic
4. wait for approval
```

**Prompt 7 – OCR fallback**
```
PHASE 7: Implement OCR fallback for scanned PDFs and images.

Requirements:
- use PaddleOCR as primary OCR engine
- fallback to Tesseract only if needed
- support scanned PDFs and image uploads
- store OCR page text in document_pages
- preserve page references
- record OCR engine used and quality metadata if available
- processing pipeline decides between direct extraction and OCR

Constraints:
- support English and Hindi first
- fail gracefully if OCR dependencies missing
- keep implementation practical for local/server use

Add:
- dependency/setup instructions
- verification fixtures if possible
- docs updates

Output:
1. system dependency list
2. changed files
3. user-visible behavior
4. wait for approval
```

**Prompt 8 – Chunking**
```
PHASE 8: Implement citation-friendly chunking.

Requirements:
- create chunks table
- chunk page text with overlap
- fields:
  - document_id
  - page_number
  - chunk_index
  - text
  - start_offset
  - end_offset
- configurable chunk size and overlap via env vars
- idempotent rebuild behavior
- admin/dev endpoint to inspect chunks

Constraints:
- do not embed yet
- optimize for citation accuracy
- do not merge chunks across pages

Add:
- tests for chunk boundaries
- docs update
- examples in build_status.md

Output:
1. chunking policy summary
2. changed files
3. verification steps
4. wait for approval
```

**Prompt 9 – Embeddings + retrieval**
```
PHASE 9: Implement BGE-M3 embeddings and pgvector retrieval.

Requirements:
- enable pgvector
- store embedding vector per chunk
- generate query embedding
- retrieve top-k chunks for a given user question
- strict scoping by current user and document_id
- modular embedding provider abstraction
- command to backfill embeddings for existing documents

Constraints:
- no separate vector DB
- no cross-user leakage
- no cross-document retrieval unless explicitly requested

Add:
- retrieval tests
- index/performance notes
- docs update

Output:
1. retrieval flow
2. changed files
3. local model setup notes
4. wait for approval
```

**Prompt 10 – Confidence gate**
```
PHASE 10: Implement refusal-first confidence gate.

Requirements:
- create deterministic gating module
- inputs may include:
  - top retrieval score
  - avg top-k score
  - lexical overlap
  - optional direct answer-span signal
- if confidence below threshold, refuse exactly:
  "This information is not present in the uploaded document."
- thresholds configurable via env vars
- do not call answer generator when gate fails
- return safe external confidence and internal diagnostics

Add:
- unit tests for pass/fail scenarios
- docs update
- examples of supported and refused cases

Output:
1. scoring logic summary
2. changed files
3. tuning instructions
4. wait for approval
```

**Prompt 11 – Answer engine**
```
PHASE 11: Build the answer engine with extraction-first, local-LLM-second design.

Requirements:
- if answer can be extracted directly from chunks, return extractive answer with citation
- if synthesis is needed, use context-only generation
- optional Ollama integration for local generation
- system prompt must enforce:
  - answer only from context
  - refuse if unsupported
  - never invent citations
- if Ollama unavailable, system still works using extractive mode + refusal
- every answer returns:
  - answer
  - confidence
  - citations
  - status

Constraints:
- no cloud LLM APIs required
- no dependence on external paid APIs
- keep prompts short and strict

Add:
- tests for extractive and refusal behavior
- prompt template in code/docs
- docs update

Output:
1. decision tree
2. changed files
3. fallback behavior
4. wait for approval
```

**Prompt 12 – Support validator**
```
PHASE 12: Add a support validator for generated answers.

Requirements:
- validate generated answer against retrieved chunks
- if unsupported, replace final answer with exact refusal:
  "This information is not present in the uploaded document."
- support labels:
  - supported
  - partially_supported
  - unsupported
- log reasons for rejection
- ensure citations only point to retrieved supporting chunks

Constraints:
- deterministic where possible
- practical reliability over complexity

Add:
- tests with intentionally unsupported answers
- docs update

Output:
1. validator strategy
2. changed files
3. trust impact summary
4. wait for approval
```

**Prompt 13 – Main QA UI**
```
PHASE 13: Build the main BharatDoc document Q&A user interface.

Requirements:
- document detail page
- question input
- answer card
- confidence display
- citations list
- refusal state UI
- query history
- loading/error/empty states
- responsive design for mobile and desktop

Constraints:
- focus on clarity and trust
- no unnecessary chat gimmicks
- keep UI polished but simple

Add:
- API integration layer
- typed frontend models
- docs update

Output:
1. component/page structure
2. changed files
3. manual UI verification checklist
4. wait for approval
```

**Prompt 14 – Security hardening**
```
PHASE 14: Apply MVP security hardening.

Requirements:
- request size limits
- file validation review
- rate limiting on auth and query endpoints
- safe auth defaults
- strict data isolation in queries
- CORS configuration
- trusted host configuration
- audit logging for register/login/upload/query/delete
- safe delete flow for document and derived artifacts
- tests for unauthorized access attempts

Constraints:
- no enterprise compliance theater
- focus on realistic protections for 1-VM MVP

Add:
- security section in README
- deferred risk list in open_issues.md

Output:
1. threat summary
2. implemented mitigations
3. changed files
4. wait for approval
```

**Prompt 15 – Deployment pack**
```
PHASE 15: Prepare single-VM production deployment.

Requirements:
- production docker-compose
- Caddy config
- persistent volumes
- health checks
- frontend production build
- backend production config
- worker service
- postgres and redis
- env.production.example
- deployment README with exact commands

Constraints:
- single VM only
- no Kubernetes
- keep deployment simple and reproducible

Add:
- backup and restore notes
- rollback notes
- post-deploy verification checklist

Output:
1. exact deploy steps
2. changed files
3. troubleshooting notes
4. wait for approval
```

**Prompt 16 – CI/CD**
```
PHASE 16: Add practical CI/CD with GitHub Actions.

Requirements:
- run backend tests
- run frontend build/test if available
- build Docker images
- optional SSH deploy workflow
- post-deploy health check
- clear secrets list
- fail deployment on failing tests

Constraints:
- keep workflow simple
- avoid fragile complexity

Add:
- CI/CD section in README
- required secrets checklist
- rollback strategy notes

Output:
1. workflow summary
2. changed files
3. setup checklist for human supervisor
4. wait for approval
```

**Prompt 17 – Final launch audit**
```
PHASE 17: Perform final launch audit for 1 real deployed user.

Review:
- auth
- upload
- processing
- extraction/OCR
- retrieval
- gate/refusal behavior
- answer correctness
- citation correctness
- UI quality
- deployment readiness
- logs/debuggability
- backup basics

Deliver:
- go/no-go recommendation
- blocker list
- known limitations
- day-1 operations guide
- launch checklist
- top 10 next improvements after first user

Constraints:
- be brutally honest
- do not hide unfinished areas
- separate blockers from nice-to-haves

Output:
1. audit report
2. ship/no-ship decision
3. final checklist
```

---

## PART 6: REVIEW / REPAIR PROMPTS
### Run after every major phase

**Self‑critic prompt**
```
Review the code you just produced like a ruthless principal engineer.

Check for:
- broken imports
- inconsistent types
- incomplete wiring
- migration mismatches
- auth bypass risks
- user/data isolation bugs
- race conditions
- bad env var handling
- weak error handling
- missing tests
- over-engineering

Return:
1. issues found
2. severity
3. exact fixes needed
4. whether implementation is safe to proceed
```

**Adversarial QA prompt**
```
Act as an adversarial QA and security engineer.

For the current phase, enumerate:
- happy path tests
- edge case tests
- abuse tests
- unauthorized access tests
- data leakage tests
- failure recovery tests

Then identify:
- automated tests present
- manual tests needed
- missing critical coverage
```

**No‑scope‑creep prompt**
```
Review the implementation and identify any scope creep, unnecessary abstractions, or premature complexity.

For each item:
- explain why it is unnecessary now
- recommend removal, simplification, or deferral
```

---

## PART 7: HUMAN SUPERVISOR PROMPTS
### For credentials, deployment, and go‑live

**Credentials checklist**
```
List every credential, account, and external setup item required for BharatDoc MVP.

For each item specify:
- name
- required now or later
- why needed
- where to obtain it
- where to store it
- exact env var name if relevant

Keep this list limited to true MVP needs.
```

**Deployment supervisor**
```
Assume I am the human supervisor preparing production deployment.

Give exact step-by-step instructions for:
1. creating the VM
2. installing Docker and Docker Compose
3. cloning repo
4. creating env files
5. attaching domain
6. configuring DNS
7. starting services
8. verifying health
9. inspecting logs
10. restarting or rolling back
```

**Go‑live dry run**
```
Simulate a full user journey and expected system behavior:
1. register
2. login
3. upload digital PDF
4. upload scanned PDF
5. processing complete
6. ask supported question
7. ask unsupported question
8. delete document

For each step provide:
- expected UI behavior
- expected backend behavior
- expected DB changes
- likely failure points
- exact verification commands/logs
```

---

## PART 8: BUSINESS & MONEY PROMPTS
### Revenue, pricing, and go‑to‑market

**Business strategy prompt**
```
Act as a startup strategist and B2B SaaS operator.

Using the current BharatDoc product, develop:
1. ideal customer profiles for India
2. top 5 highest-value use cases
3. pricing strategy for MVP
4. low-cost acquisition strategy
5. sales script for first 20 customers
6. website messaging
7. differentiation from generic AI chatbots
8. roadmap from MVP to revenue to 100 paying users

Constraints:
- optimize for a solo founder
- optimize for first revenue, not vanity growth
- focus on realistic India-first niches
- prefer high-trust workflows over generic mass-market positioning
```

**Revenue model prompt**
```
Create a practical BharatDoc revenue model with:
- free plan
- starter plan
- pro plan
- business/custom plan
- onboarding service package
- private deployment package
- support retainers
- usage limits
- document limits
- query limits
- upsell path

Then estimate:
- first ₹10,000/month path
- first ₹50,000/month path
- first ₹1 lakh/month path
- assumptions and risks
```

**Go‑to‑market prompt**
```
Design a zero-budget go-to-market plan for BharatDoc in India for the first 90 days.

Include:
- target segment order
- outreach channels
- WhatsApp/email outreach script
- demo script
- landing page CTA strategy
- first-case-study strategy
- referral loop
- founder-led sales workflow
- what metrics to track manually
```

---

## HOW TO SAVE AND CONVERT TO PDF
1. Copy the entire content from this Markdown block.
2. Paste it into a file named `Master_Prompts.md`.
3. Convert to PDF using one of the following free methods:
   - **Pandoc** (if installed): `pandoc Master_Prompts.md -o Master_Prompts.pdf`
   - **Online converter** (e.g., markdowntopdf.com)
   - **VS Code** with a Markdown PDF extension
   - **Print to PDF** from any Markdown preview (e.g., Typora, Obsidian, or Chrome after rendering)
