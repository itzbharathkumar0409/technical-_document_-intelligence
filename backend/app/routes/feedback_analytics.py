"""Feedback, Analytics, and Settings API routes."""

import json
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, func, select, text as sql_text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_admin_user, get_current_user
from app.config import get_settings
from app.database import get_db
from app.models import (
    Conversation,
    Document,
    DocumentChunk,
    Feedback,
    Message,
    ModelConfig,
    User,
)
from app.schemas import (
    AnalyticsResponse,
    ConnectionTestResult,
    FeedbackCreate,
    FeedbackResponse,
    SettingsResponse,
    SettingsUpdate,
)

feedback_router = APIRouter(prefix="/feedback", tags=["Feedback"])
analytics_router = APIRouter(prefix="/analytics", tags=["Analytics"])
settings_router = APIRouter(prefix="/settings", tags=["Settings"])


# ─── Feedback ────────────────────────────────────────────────────────────────

@feedback_router.post("/", response_model=FeedbackResponse, status_code=201)
async def submit_feedback(
    data: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit feedback (thumbs up/down) for a message."""
    # Verify message belongs to user's conversation
    result = await db.execute(
        select(Message)
        .join(Conversation)
        .where(
            and_(
                Message.id == data.message_id,
                Conversation.user_id == current_user.id,
            )
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Message not found")

    # Check for existing feedback
    result = await db.execute(
        select(Feedback).where(
            and_(
                Feedback.message_id == data.message_id,
                Feedback.user_id == current_user.id,
            )
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.rating = data.rating
        existing.comment = data.comment
        await db.flush()
        return FeedbackResponse.model_validate(existing)

    feedback = Feedback(
        user_id=current_user.id,
        message_id=data.message_id,
        rating=data.rating,
        comment=data.comment,
    )
    db.add(feedback)
    await db.flush()
    return FeedbackResponse.model_validate(feedback)


@feedback_router.get("/")
async def list_feedback(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's feedback."""
    result = await db.execute(
        select(Feedback)
        .where(Feedback.user_id == current_user.id)
        .order_by(Feedback.created_at.desc())
        .limit(100)
    )
    items = result.scalars().all()
    return [FeedbackResponse.model_validate(f) for f in items]


# ─── Analytics ───────────────────────────────────────────────────────────────

@analytics_router.get("/", response_model=AnalyticsResponse)
async def get_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get analytics dashboard data. All metrics are MEASURED from real data."""
    user_id = current_user.id

    # Total documents
    total_docs = (await db.execute(
        select(func.count()).select_from(
            select(Document).where(Document.user_id == user_id).subquery()
        )
    )).scalar() or 0

    # Total chunks
    total_chunks = (await db.execute(
        select(func.count()).select_from(
            select(DocumentChunk).where(DocumentChunk.user_id == user_id).subquery()
        )
    )).scalar() or 0

    # Total conversations
    total_convs = (await db.execute(
        select(func.count()).select_from(
            select(Conversation).where(Conversation.user_id == user_id).subquery()
        )
    )).scalar() or 0

    # Total messages
    total_msgs = (await db.execute(
        select(func.count()).select_from(
            select(Message)
            .join(Conversation)
            .where(Conversation.user_id == user_id)
            .subquery()
        )
    )).scalar() or 0

    # Feedback counts
    total_fb = (await db.execute(
        select(func.count()).select_from(
            select(Feedback).where(Feedback.user_id == user_id).subquery()
        )
    )).scalar() or 0

    pos_fb = (await db.execute(
        select(func.count()).select_from(
            select(Feedback).where(
                and_(Feedback.user_id == user_id, Feedback.rating == 1)
            ).subquery()
        )
    )).scalar() or 0

    neg_fb = (await db.execute(
        select(func.count()).select_from(
            select(Feedback).where(
                and_(Feedback.user_id == user_id, Feedback.rating == -1)
            ).subquery()
        )
    )).scalar() or 0

    # Average latency
    avg_latency = (await db.execute(
        select(func.avg(Message.latency_ms))
        .join(Conversation)
        .where(
            and_(
                Conversation.user_id == user_id,
                Message.role == "assistant",
                Message.latency_ms.isnot(None),
            )
        )
    )).scalar()

    # Documents by status
    status_result = await db.execute(
        select(Document.status, func.count())
        .where(Document.user_id == user_id)
        .group_by(Document.status)
    )
    docs_by_status = {row[0]: row[1] for row in status_result.fetchall()}

    # Queries in last 7 days
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    queries_7d = (await db.execute(
        select(func.count()).select_from(
            select(Message)
            .join(Conversation)
            .where(
                and_(
                    Conversation.user_id == user_id,
                    Message.role == "user",
                    Message.created_at >= seven_days_ago,
                )
            )
            .subquery()
        )
    )).scalar() or 0

    return AnalyticsResponse(
        total_documents=total_docs,
        total_chunks=total_chunks,
        total_conversations=total_convs,
        total_messages=total_msgs,
        total_feedback=total_fb,
        positive_feedback=pos_fb,
        negative_feedback=neg_fb,
        avg_latency_ms=float(avg_latency) if avg_latency else None,
        documents_by_status=docs_by_status,
        queries_last_7_days=queries_7d,
        metric_type="MEASURED",
    )


# ─── Settings ────────────────────────────────────────────────────────────────

@settings_router.get("/", response_model=SettingsResponse)
async def get_settings_api(
    current_user: User = Depends(get_admin_user),
):
    """Get current model and retrieval settings (admin only). Secrets excluded."""
    settings = get_settings()
    return SettingsResponse(
        llm_provider=settings.llm_provider,
        llm_model=settings.llm_model,
        embedding_provider=settings.embedding_provider,
        embedding_model=settings.embedding_model,
        embedding_dimension=settings.embedding_dimension,
        retrieval_vector_top_k=settings.retrieval_vector_top_k,
        retrieval_keyword_top_k=settings.retrieval_keyword_top_k,
        retrieval_final_top_k=settings.retrieval_final_top_k,
        relevance_threshold=settings.relevance_threshold,
        reranker_enabled=settings.reranker_enabled,
        chunk_size_tokens=settings.chunk_size_tokens,
        chunk_overlap_tokens=settings.chunk_overlap_tokens,
    )


@settings_router.put("/", response_model=SettingsResponse)
async def update_settings(
    data: SettingsUpdate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Update model and retrieval settings (admin only). Requires re-login to take effect."""
    # Store in database
    for key, value in data.model_dump(exclude_none=True).items():
        result = await db.execute(
            select(ModelConfig).where(ModelConfig.key == key)
        )
        config = result.scalar_one_or_none()
        if config:
            config.value = json.dumps(value)
            config.updated_by = current_user.id
        else:
            config = ModelConfig(
                key=key,
                value=json.dumps(value),
                updated_by=current_user.id,
            )
            db.add(config)

    await db.flush()

    settings = get_settings()
    return SettingsResponse(
        llm_provider=settings.llm_provider,
        llm_model=settings.llm_model,
        embedding_provider=settings.embedding_provider,
        embedding_model=settings.embedding_model,
        embedding_dimension=settings.embedding_dimension,
        retrieval_vector_top_k=settings.retrieval_vector_top_k,
        retrieval_keyword_top_k=settings.retrieval_keyword_top_k,
        retrieval_final_top_k=settings.retrieval_final_top_k,
        relevance_threshold=settings.relevance_threshold,
        reranker_enabled=settings.reranker_enabled,
        chunk_size_tokens=settings.chunk_size_tokens,
        chunk_overlap_tokens=settings.chunk_overlap_tokens,
    )


@settings_router.post("/test-connection", response_model=ConnectionTestResult)
async def test_connection(
    current_user: User = Depends(get_admin_user),
):
    """Test connection to the configured LLM provider."""
    import time
    import httpx

    settings = get_settings()
    start = time.time()

    try:
        if settings.llm_provider == "ollama":
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{settings.llm_base_url}/api/tags")
                response.raise_for_status()
                models = response.json().get("models", [])
                model_names = [m["name"] for m in models]
                latency = (time.time() - start) * 1000
                return ConnectionTestResult(
                    provider="ollama",
                    model=settings.llm_model,
                    success=True,
                    message=f"Connected. Available models: {', '.join(model_names[:5])}",
                    latency_ms=latency,
                )

        elif settings.llm_provider == "openai":
            api_key = settings.openai_api_key or settings.llm_api_key
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{settings.openai_base_url}/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                )
                response.raise_for_status()
                latency = (time.time() - start) * 1000
                return ConnectionTestResult(
                    provider="openai",
                    model=settings.openai_model,
                    success=True,
                    message="Connected successfully",
                    latency_ms=latency,
                )

        else:
            return ConnectionTestResult(
                provider=settings.llm_provider,
                model=settings.llm_model,
                success=False,
                message=f"Unknown provider: {settings.llm_provider}",
            )

    except Exception as e:
        latency = (time.time() - start) * 1000
        return ConnectionTestResult(
            provider=settings.llm_provider,
            model=settings.llm_model,
            success=False,
            message=f"Connection failed: {str(e)[:200]}",
            latency_ms=latency,
        )
