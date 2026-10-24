# Architecture Decisions

## D1: Repository Structure
- **Monorepo** with `frontend/` (Next.js + TypeScript + Tailwind) and `backend/` (Python + FastAPI).
- Shared config via `.env` files.

## D2: Background Work
- **FastAPI BackgroundTasks** for ingestion pipeline. Chosen over Celery for simplicity and fewer infrastructure dependencies. A `processing_jobs` table tracks state. Upgrade path to Celery/Redis documented.

## D3: Password Hashing
- **bcrypt** via `passlib[bcrypt]`. Argon2 requires system-level deps that complicate Docker builds.

## D4: Embedding Fallback
- When no embedding provider is configured, the system uses a **local sentence-transformers model** (`all-MiniLM-L6-v2`, 384 dims) as the default. This avoids a hard dependency on external APIs for development.

## D5: LLM Fallback
- When no LLM provider is available, the system returns a structured "LLM unavailable" response with retrieved passages so the user still gets search results.

## D6: File Storage
- Local filesystem at `./storage/uploads/{user_id}/{doc_id}/` behind a `StorageBackend` interface. S3-compatible implementation can be swapped in.

## D7: Chunking Strategy
- Structure-aware chunking: respect headings (Markdown `#`, PDF outline, DOCX styles), tables, and code blocks. Target ~800 tokens with ~120 token overlap. Never split tables or code blocks.

## D8: Reranker
- Optional cross-encoder reranker (`cross-encoder/ms-marco-MiniLM-L-6-v2`). Falls back to RRF ordering if unavailable. Controlled by `RERANKER_ENABLED` env var.

## D9: Frontend Styling
- Tailwind CSS as explicitly requested. Enterprise SaaS dark theme with navy/white/teal accent.

## D10: Database
- PostgreSQL 16 + pgvector extension. HNSW index for vector similarity search. GIN index for tsvector full-text search.

## D11: CORS
- Restricted to `CORS_ORIGINS` env var, defaulting to `http://localhost:3000`.

## D12: Rate Limiting
- `slowapi` for rate limiting on auth and QA endpoints. Configurable via env vars.
