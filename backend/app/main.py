"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_engine
from app.routes.auth import router as auth_router
from app.routes.documents import router as documents_router
from app.routes.qa import router as qa_router
from app.routes.feedback_analytics import (
    analytics_router,
    feedback_router,
    settings_router,
)
from app.routes.health import router as health_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
    settings = get_settings()
    logger.info("Starting DocIQ Backend...")
    logger.info(f"  LLM Provider: {settings.llm_provider} ({settings.llm_model})")
    logger.info(f"  Embedding Provider: {settings.embedding_provider} ({settings.embedding_model})")
    logger.info(f"  CORS Origins: {settings.cors_origin_list}")

    # Initialize database engine
    init_engine()
    logger.info("Database engine initialized")

    yield

    logger.info("Shutting down DocIQ Backend...")


app = FastAPI(
    title="DocIQ - Technical Document Intelligence",
    description="Upload technical documents, search them, and ask natural-language questions with grounded, cited answers.",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router, prefix="/api")
app.include_router(documents_router, prefix="/api")
app.include_router(qa_router, prefix="/api")
app.include_router(feedback_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(settings_router, prefix="/api/admin")
app.include_router(health_router, prefix="/api")
app.include_router(health_router)


@app.get("/")
async def root():
    return {
        "name": "DocIQ - Technical Document Intelligence",
        "version": "0.1.0",
        "docs": "/docs",
    }
