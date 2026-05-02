# BharatDoc Product Requirements Document (PRD)

## MVP Scope
Build an India-first, privacy-first, document-grounded AI SaaS. It must answer questions exclusively from uploaded documents, refusing to answer if the information is unsupported.

## User Stories
1. As a user, I can register and log in with email and password so my documents remain private.
2. As a user, I can upload PDFs or images (PNG/JPG/JPEG) so they can be processed.
3. As a user, I can view the processing status of my documents.
4. As a user, I can ask questions in English or Hindi regarding my uploaded documents.
5. As a user, I receive a grounded answer with citations to the document.
6. As a user, I receive the exact refusal "This information is not present in the uploaded document." if the answer cannot be found in my document.
7. As a user, I can delete my documents to remove all derived artifacts (text, embeddings, files) completely from the system.

## Non-Goals
- No Kubernetes or microservices.
- No Keycloak, enterprise SSO, Aadhaar OTP, or DigiLocker.
- No subscriptions in v1.
- No multi-region complexity or Prometheus/Grafana in v1.
- No native Android app in v1.
- No relying on paid cloud LLM APIs (OpenAI, Anthropic).

## Acceptance Criteria
- End-to-end functionality verified: Register -> Upload -> Process -> Query -> View Answer/Citation or Refusal -> Delete.
- Strict user/data isolation preventing cross-user data leakage.
