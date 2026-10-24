"""Hybrid retrieval: vector search + keyword search + RRF fusion + optional reranking."""

import logging
import time
import uuid
from typing import Optional

from sqlalchemy import and_, text as sql_text, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import DocumentChunk, Document
from app.services.ingestion import compute_embeddings

logger = logging.getLogger(__name__)


async def vector_search(
    db: AsyncSession,
    query_embedding: list[float],
    user_id: uuid.UUID,
    document_ids: Optional[list[uuid.UUID]] = None,
    top_k: int = 20,
) -> list[dict]:
    """Perform vector similarity search. Ownership filter applied in the query."""
    if not query_embedding:
        return []

    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

    doc_filter = ""
    params = {"user_id": str(user_id), "top_k": top_k, "embedding": embedding_str}

    if document_ids:
        doc_id_list = ",".join(f"'{str(d)}'" for d in document_ids)
        doc_filter = f"AND dc.document_id IN ({doc_id_list})"

    query = sql_text(f"""
        SELECT dc.id, dc.document_id, dc.content, dc.page_number,
               dc.section_path, dc.chunk_index, dc.token_count,
               d.original_filename,
               1 - (dc.embedding <=> :embedding::vector) as similarity
        FROM document_chunks dc
        JOIN documents d ON d.id = dc.document_id
        WHERE dc.user_id = :user_id
        {doc_filter}
        AND dc.embedding IS NOT NULL
        ORDER BY dc.embedding <=> :embedding::vector
        LIMIT :top_k
    """)

    result = await db.execute(query, params)
    rows = result.fetchall()

    return [
        {
            "chunk_id": str(row[0]),
            "document_id": str(row[1]),
            "content": row[2],
            "page_number": row[3],
            "section_path": row[4],
            "chunk_index": row[5],
            "token_count": row[6],
            "filename": row[7],
            "score": float(row[8]) if row[8] else 0.0,
            "source": "vector",
        }
        for row in rows
    ]


async def keyword_search(
    db: AsyncSession,
    query: str,
    user_id: uuid.UUID,
    document_ids: Optional[list[uuid.UUID]] = None,
    top_k: int = 20,
) -> list[dict]:
    """Perform PostgreSQL full-text search. Ownership filter applied in the query."""
    # Normalize query for tsquery
    query_words = query.strip().split()
    ts_query = " & ".join(w for w in query_words if w.isalnum())

    if not ts_query:
        return []

    doc_filter = ""
    params = {"user_id": str(user_id), "top_k": top_k, "query": ts_query}

    if document_ids:
        doc_id_list = ",".join(f"'{str(d)}'" for d in document_ids)
        doc_filter = f"AND dc.document_id IN ({doc_id_list})"

    sql = sql_text(f"""
        SELECT dc.id, dc.document_id, dc.content, dc.page_number,
               dc.section_path, dc.chunk_index, dc.token_count,
               d.original_filename,
               ts_rank_cd(dc.search_vector, plainto_tsquery('english', :query)) as rank
        FROM document_chunks dc
        JOIN documents d ON d.id = dc.document_id
        WHERE dc.user_id = :user_id
        {doc_filter}
        AND dc.search_vector @@ plainto_tsquery('english', :query)
        ORDER BY rank DESC
        LIMIT :top_k
    """)

    result = await db.execute(sql, params)
    rows = result.fetchall()

    return [
        {
            "chunk_id": str(row[0]),
            "document_id": str(row[1]),
            "content": row[2],
            "page_number": row[3],
            "section_path": row[4],
            "chunk_index": row[5],
            "token_count": row[6],
            "filename": row[7],
            "score": float(row[8]) if row[8] else 0.0,
            "source": "keyword",
        }
        for row in rows
    ]


def reciprocal_rank_fusion(
    vector_results: list[dict],
    keyword_results: list[dict],
    k: int = 60,
) -> list[dict]:
    """Fuse results using Reciprocal Rank Fusion (RRF)."""
    scores: dict[str, float] = {}
    chunks: dict[str, dict] = {}

    for rank, result in enumerate(vector_results):
        chunk_id = result["chunk_id"]
        scores[chunk_id] = scores.get(chunk_id, 0) + 1.0 / (k + rank + 1)
        chunks[chunk_id] = result

    for rank, result in enumerate(keyword_results):
        chunk_id = result["chunk_id"]
        scores[chunk_id] = scores.get(chunk_id, 0) + 1.0 / (k + rank + 1)
        if chunk_id not in chunks:
            chunks[chunk_id] = result

    # Sort by fused score
    sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

    fused = []
    for chunk_id in sorted_ids:
        result = chunks[chunk_id].copy()
        result["rrf_score"] = scores[chunk_id]
        fused.append(result)

    return fused


def deduplicate_results(results: list[dict], similarity_threshold: float = 0.9) -> list[dict]:
    """Remove near-duplicate chunks based on content overlap."""
    seen_content = []
    deduped = []

    for result in results:
        content = result["content"].strip().lower()
        is_dup = False
        for seen in seen_content:
            # Simple Jaccard similarity on word sets
            words_a = set(content.split())
            words_b = set(seen.split())
            if not words_a or not words_b:
                continue
            intersection = len(words_a & words_b)
            union = len(words_a | words_b)
            if union > 0 and intersection / union > similarity_threshold:
                is_dup = True
                break

        if not is_dup:
            deduped.append(result)
            seen_content.append(content)

    return deduped


async def hybrid_retrieve(
    db: AsyncSession,
    query: str,
    user_id: uuid.UUID,
    document_ids: Optional[list[uuid.UUID]] = None,
    top_k: Optional[int] = None,
) -> tuple[list[dict], dict]:
    """
    Full hybrid retrieval pipeline:
    1. Embed query
    2. Vector search + Keyword search
    3. RRF fusion
    4. Deduplication
    5. Optional reranking
    6. Select top-K within context budget

    Returns (results, timing_info).
    """
    settings = get_settings()
    if top_k is None:
        top_k = settings.retrieval_final_top_k

    timings = {}
    start_total = time.time()

    # 1. Embed query
    t0 = time.time()
    try:
        query_embeddings = compute_embeddings([query])
        query_embedding = query_embeddings[0] if query_embeddings else []
    except Exception as e:
        logger.warning(f"Embedding failed: {e}")
        query_embedding = []
    timings["embedding_ms"] = int((time.time() - t0) * 1000)

    # 2. Parallel searches
    t0 = time.time()
    vector_results = []
    keyword_results = []

    if query_embedding:
        vector_results = await vector_search(
            db, query_embedding, user_id, document_ids, settings.retrieval_vector_top_k
        )
    timings["vector_search_ms"] = int((time.time() - t0) * 1000)

    t0 = time.time()
    keyword_results = await keyword_search(
        db, query, user_id, document_ids, settings.retrieval_keyword_top_k
    )
    timings["keyword_search_ms"] = int((time.time() - t0) * 1000)

    # 3. RRF fusion
    t0 = time.time()
    fused = reciprocal_rank_fusion(vector_results, keyword_results)
    timings["fusion_ms"] = int((time.time() - t0) * 1000)

    # 4. Deduplication
    deduped = deduplicate_results(fused)

    # 5. Reranking (optional)
    if settings.reranker_enabled:
        t0 = time.time()
        try:
            deduped = rerank_results(query, deduped)
            timings["rerank_ms"] = int((time.time() - t0) * 1000)
        except Exception as e:
            logger.warning(f"Reranking failed, using RRF order: {e}")
            timings["rerank_ms"] = 0

    # 6. Select top-K
    final_results = deduped[:top_k]

    timings["total_retrieval_ms"] = int((time.time() - start_total) * 1000)
    timings["vector_count"] = len(vector_results)
    timings["keyword_count"] = len(keyword_results)
    timings["fused_count"] = len(fused)
    timings["final_count"] = len(final_results)

    return final_results, timings


def rerank_results(query: str, results: list[dict]) -> list[dict]:
    """Rerank using cross-encoder model."""
    settings = get_settings()
    try:
        from sentence_transformers import CrossEncoder
        model = CrossEncoder(settings.reranker_model)
        pairs = [(query, r["content"]) for r in results]
        scores = model.predict(pairs)

        for i, score in enumerate(scores):
            results[i]["rerank_score"] = float(score)

        results.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)
        return results
    except Exception as e:
        logger.warning(f"Reranker failed: {e}")
        return results
