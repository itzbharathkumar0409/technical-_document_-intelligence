# DocIQ - Technical Document Intelligence & Q&A Platform

DocIQ is an enterprise-grade technical document intelligence and grounded Q&A platform. It enables teams to upload technical specifications, architecture guides, and API documentation, search across them using hybrid retrieval, and receive grounded, citation-backed natural-language answers.

---

## Key Features

- **Multi-Format Ingestion**: Supports `.pdf`, `.docx`, `.md`, and `.txt` up to 50MB with structure-aware chunking (respects markdown headers, tables, code blocks).
- **Hybrid Retrieval**: Combines dense vector similarity via **pgvector** (`all-MiniLM-L6-v2`, 384 dimensions) with sparse full-text search via PostgreSQL `tsvector` and Reciprocal Rank Fusion (RRF).
- **Verifiable Citation Grounding**: Every answer is anchored by sentence-level citation labels (`[S1]`, `[S2]`) with verifiable excerpts, page numbers, and cosine similarity scores.
- **Hallucination Guardrails**: Detects low confidence and insufficient evidence before generating potentially inaccurate responses.
- **Enterprise Dark Dashboard**: Built with Next.js 16 (App Router), Tailwind CSS, and Lucide icons featuring a real-time Q&A workspace, document chunk inspector, and measured latency analytics.
- **Strict Data Isolation**: Multi-tenant database design with user ownership scoping on every query.

---

## Architecture

```
┌────────────────────────────────┐
│   DocIQ Frontend (Next.js 16)  │  ◄── Port 3000
└───────────────┬────────────────┘
                │ REST API / JWT
┌───────────────▼────────────────┐
│     FastAPI Backend Engine     │  ◄── Port 8000
└───────┬───────────────┬────────┘
        │               │
        ▼               ▼
┌───────────────┐ ┌────────────────────────────────────────┐
│ Ollama/OpenAI │ │ Supabase Managed PostgreSQL + pgvector │
│ (LLM / RAG)   │ │ (HNSW Cosine Index + TSVECTOR Search)  │
└───────────────┘ └────────────────────────────────────────┘
```

---

## Tech Stack

- **Frontend**: Next.js 16 (Turbopack), React 19, TypeScript, Tailwind CSS v4, Lucide React
- **Backend**: Python 3.12/3.14, FastAPI, SQLAlchemy 2.0 (asyncio + asyncpg), Alembic, Pydantic v2
- **Vector Database**: Supabase PostgreSQL 17 with `pgvector` (HNSW indexing)
- **Embeddings**: `sentence-transformers` (`all-MiniLM-L6-v2`) with local zero-API fallback
- **Authentication**: JWT Bearer tokens + direct `bcrypt` password hashing (12 rounds)

---

## Getting Started

### 1. Prerequisites
- Python 3.11+
- Node.js 20+
- PostgreSQL with `pgvector` extension (e.g. Supabase)

### 2. Configure Environment Variables
Copy `.env.example` to `.env` (and `backend/.env`):

```bash
DATABASE_URL=postgresql+asyncpg://<user>:<password>@<host>:5432/<database>
DATABASE_URL_SYNC=postgresql+psycopg2://<user>:<password>@<host>:5432/<database>
SECRET_KEY=your-secret-key-here
LLM_PROVIDER=ollama
LLM_MODEL=llama3.1
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

### 3. Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend Swagger UI will be available at: [http://localhost:8000/docs](http://localhost:8000/docs)

### 4. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

DocIQ Web App will be available at: [http://localhost:3000](http://localhost:3000)

---

## Running Backend Tests

```bash
cd backend
pytest tests
```

---

## License

MIT
