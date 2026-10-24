"""Health check endpoint with DB and provider status."""

from fastapi import APIRouter
from sqlalchemy import text as sql_text

from app.config import get_settings
from app.database import get_engine
from app.schemas import HealthResponse
from sqlalchemy.ext.asyncio import create_async_engine

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check: database connectivity and provider availability."""
    settings = get_settings()

    # Check database
    db_status = "unknown"
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(sql_text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)[:100]}"

    # Check LLM provider
    llm_status = "unknown"
    try:
        import httpx
        if settings.llm_provider == "ollama":
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{settings.llm_base_url}/api/tags")
                llm_status = "connected" if resp.status_code == 200 else f"error: {resp.status_code}"
        elif settings.llm_provider == "openai":
            llm_status = "configured" if (settings.openai_api_key or settings.llm_api_key) else "no api key"
        else:
            llm_status = f"unknown provider: {settings.llm_provider}"
    except Exception as e:
        llm_status = f"unavailable: {str(e)[:100]}"

    # Check embedding provider
    emb_status = "unknown"
    if settings.embedding_provider == "local":
        try:
            from app.services.ingestion import get_embedding_model
            model = get_embedding_model()
            emb_status = "loaded" if model else "not loaded"
        except Exception as e:
            emb_status = f"error: {str(e)[:100]}"
    elif settings.embedding_provider == "openai":
        emb_status = "configured" if (settings.openai_api_key or settings.llm_api_key) else "no api key"

    overall = "healthy" if db_status == "connected" else "degraded"

    return HealthResponse(
        status=overall,
        database=db_status,
        llm_provider=llm_status,
        embedding_provider=emb_status,
    )
