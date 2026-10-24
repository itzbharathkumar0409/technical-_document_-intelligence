# DocIQ Architecture Guide

## Overview

DocIQ is a technical document intelligence and Q&A platform that enables users to upload technical documents, search through them using natural language, and receive accurate, citation-backed answers.

## System Architecture

### Frontend (Next.js)
The frontend is built with Next.js 14 and uses the App Router pattern. It communicates with the backend via REST API calls.

### Backend (FastAPI)
The backend handles authentication, document management, ingestion, retrieval, and Q&A. It uses async SQLAlchemy for database operations.

### Database (PostgreSQL + pgvector)
PostgreSQL with the pgvector extension stores both relational data and vector embeddings. HNSW indexes enable fast similarity search.

## Ingestion Pipeline

1. **Upload**: Files are validated (extension, MIME type, size) and stored locally
2. **Parse**: Documents are parsed with format-specific parsers (PyPDF, python-docx, etc.)
3. **Chunk**: Text is split into ~800 token chunks with structure awareness
4. **Embed**: Chunks are converted to vector embeddings
5. **Index**: Embeddings stored in pgvector, tsvector built for keyword search

## Retrieval Pipeline

1. Query is embedded using the same model
2. Vector similarity search (top 20)
3. Keyword full-text search (top 20)
4. Reciprocal Rank Fusion
5. Deduplication
6. Optional cross-encoder reranking
7. Top 6-8 passages selected

## Configuration

All settings are configurable via environment variables:
- `LLM_PROVIDER`: Choose between "ollama" (local) and "openai" (cloud)
- `EMBEDDING_PROVIDER`: "local" uses sentence-transformers, "openai" uses API
- `RETRIEVAL_FINAL_TOP_K`: Number of passages sent to the LLM

## Security

- JWT-based authentication
- Per-user data isolation (ownership filters in every query)
- Prompt injection defense (retrieved text wrapped in delimiters)
- File validation and sanitization
- Parameterized queries only

## Troubleshooting

### Common Issues

**Embedding model fails to load**: Ensure you have enough RAM (at least 1GB for all-MiniLM-L6-v2).

**Database connection errors**: Check that PostgreSQL is running and the pgvector extension is installed.

**LLM timeout**: Increase `LLM_TIMEOUT` or try a smaller model with Ollama.
