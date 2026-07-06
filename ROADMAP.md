# RecallAI Roadmap
 
This document tracks what RecallAI actually does today and what's planned next. It's kept in sync with the codebase — if something is checked off here, it's shipped and covered by tests, not just designed.
 
> Last reviewed against the codebase on 2026-07-06.
 
## ✅ Current Status (Shipped)
 
The project has moved well past prototype stage — it's an async FastAPI service with a real background processing pipeline, not a request/response wrapper around an LLM call.
 
**Core platform**
- [x] Async FastAPI app with structured startup/shutdown lifecycle (job recovery → Qdrant init → worker start)
- [x] PostgreSQL via SQLModel + `asyncpg`, with Alembic migrations
- [x] JWT authentication (register/login/logout) with bcrypt hashing and a real token blocklist so logout invalidates tokens server-side
- [x] Per-route rate limiting on auth endpoints (`slowapi`)
- [x] CORS, structured JSON logging (`structlog`), optional Sentry integration, global exception handler
**Ingestion pipeline**
- [x] Secure PDF upload — content-type check, magic-byte validation, path-traversal-safe storage
- [x] Durable job queue backed by Postgres (`ProcessingJob`), claimed atomically via `FOR UPDATE SKIP LOCKED`
- [x] Background worker daemon with instant wake-up on new uploads
- [x] Zombie-job recovery on boot — jobs stuck `PROCESSING` from a crash are reverted to `PENDING`
- [x] Streaming PDF text extraction (PyMuPDF) through a backpressured queue, decoupled from the event loop via a producer thread
- [x] Parent/child chunking strategy (1000/200 parent, 250 child) for wide context + precise retrieval
- [x] Batched embedding generation (Gemini `text-embedding-004`) with retry/backoff that distinguishes fatal vs. transient API errors
- [x] Idempotent teardown on failure — partial chunks are wiped so retries never leave orphans
**Retrieval & generation**
- [x] Vector search in Qdrant scoped to `user_id` at query time
- [x] Second, independent ownership check against Postgres before any chunk is used as context (defense in depth against a stale/forged filter)
- [x] Structured, cited answer generation via Groq (`llama-3.1-8b-instant`) — typed `answer_found` / `answer` / `citations[]` response, explicit anti-hallucination system prompt
- [x] Conversation history (last 20 messages) replayed for follow-up questions
**Lifecycle & ops**
- [x] Multi-step deletion saga (`DELETING` status → Qdrant wipe → chunk cleanup → row + file delete), safe to retry
- [x] Streaming ASGI middleware enforcing max upload size without buffering the payload into memory
- [x] Multi-stage Docker build, non-root runtime user, Docker Compose for local Postgres + Qdrant
- [x] CI pipeline: tests against real Postgres/Qdrant service containers, `pip-audit` dependency scan, Docker build — on every push and PR
- [x] Test suite covering API, database, ingestion, retrieval, generation, worker recovery, and dedicated security/audit benchmarks
## 🔴 Known Limitations
 
Being upfront about these rather than letting them surface as surprises:
 
- **Citations always say "Page 1."** Chunking currently buffers text across page boundaries before splitting, so the original PDF page number isn't tracked per chunk (`DocumentChunk.page_number` is hardcoded). Citations are accurate about *which document*, not yet *which page*.
- **Local disk storage only.** Uploaded files live on the container's filesystem (`UPLOAD_DIR`). This works for a single instance but doesn't survive horizontal scaling or ephemeral containers without a shared volume.
- **No retry path for `FAILED` documents.** If ingestion fails, the document is marked `FAILED` with no built-in way to re-trigger processing short of re-uploading.
- **List endpoints are unpaginated.** `GET /documents` and `GET /conversations` return the full result set — fine at small scale, not at large scale.
- **PDF only.** No support yet for `.docx`, `.txt`, `.md`, or other common document formats.
- **No LICENSE file** is currently published in the repo.
## 🗺️ Planned Work
 
### Phase 1 — Fix the sharp edges
- [ ] Track real page numbers per chunk so citations point to the correct page
- [ ] Add a `POST /documents/{id}/reprocess` endpoint to retry `FAILED` ingestion without re-uploading
- [ ] Paginate `GET /documents`, `GET /conversations`, and `GET /conversations/{id}/messages`
- [ ] Add a `LICENSE` file
### Phase 2 — Storage & scale
- [ ] Move uploaded files from local disk to object storage (S3-compatible), decoupling the API/worker from a specific filesystem
- [ ] Support running multiple worker replicas behind the same job queue (already safe via `SKIP LOCKED`; needs docs + a stress test to confirm)
- [ ] Add Prometheus-compatible metrics (queue depth, ingestion latency, retrieval latency, LLM error rate)
### Phase 3 — Product surface
- [ ] Additional document formats: `.docx`, `.txt`, `.md`
- [ ] Streamed chat responses (SSE) instead of waiting for the full generation to complete
- [ ] Refresh-token rotation alongside the current short-lived access token
- [ ] Per-document reprocessing when the embedding model changes (the `embedding_model_version` column already exists on `Document` — currently written but not yet acted on)
### Phase 4 — Frontend & deployment
- [ ] Minimal web client (upload + chat UI) against the existing API
- [ ] Managed deployment guide beyond `render.yaml` (e.g. Fly.io, AWS ECS)
- [ ] Load-testing baseline and documented throughput numbers for ingestion and Q&A
## Contributing to the Roadmap
 
Have a use case this doesn't cover yet, or disagree with a priority above? Open an issue — this roadmap is meant to reflect real usage, not a wishlist.
