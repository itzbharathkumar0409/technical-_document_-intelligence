"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings with environment variable binding."""

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://dociq:dociq_secret@localhost:5432/dociq",
        alias="DATABASE_URL",
    )
    database_url_sync: str = Field(
        default="postgresql://dociq:dociq_secret@localhost:5432/dociq",
        alias="DATABASE_URL_SYNC",
    )

    # Auth
    secret_key: str = Field(default="change-me-to-a-random-64-char-string-in-production", alias="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=60, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    bcrypt_rounds: int = Field(default=12, alias="BCRYPT_ROUNDS")

    # CORS
    cors_origins: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")

    # Storage
    storage_backend: str = Field(default="local", alias="STORAGE_BACKEND")
    storage_local_path: str = Field(default="./storage/uploads", alias="STORAGE_LOCAL_PATH")

    # LLM
    llm_provider: str = Field(default="ollama", alias="LLM_PROVIDER")
    llm_model: str = Field(default="llama3.1", alias="LLM_MODEL")
    llm_base_url: str = Field(default="http://localhost:11434", alias="LLM_BASE_URL")
    llm_api_key: Optional[str] = Field(default=None, alias="LLM_API_KEY")

    # OpenAI-compatible
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_base_url: str = Field(default="https://api.openai.com/v1", alias="OPENAI_BASE_URL")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")

    # Embedding
    embedding_provider: str = Field(default="local", alias="EMBEDDING_PROVIDER")
    embedding_model: str = Field(default="all-MiniLM-L6-v2", alias="EMBEDDING_MODEL")
    embedding_dimension: int = Field(default=384, alias="EMBEDDING_DIMENSION")
    embedding_base_url: Optional[str] = Field(default=None, alias="EMBEDDING_BASE_URL")

    # Reranker
    reranker_enabled: bool = Field(default=False, alias="RERANKER_ENABLED")
    reranker_model: str = Field(default="cross-encoder/ms-marco-MiniLM-L-6-v2", alias="RERANKER_MODEL")

    # Retrieval
    retrieval_vector_top_k: int = Field(default=20, alias="RETRIEVAL_VECTOR_TOP_K")
    retrieval_keyword_top_k: int = Field(default=20, alias="RETRIEVAL_KEYWORD_TOP_K")
    retrieval_final_top_k: int = Field(default=8, alias="RETRIEVAL_FINAL_TOP_K")
    relevance_threshold: float = Field(default=0.3, alias="RELEVANCE_THRESHOLD")

    # Chunking
    chunk_size_tokens: int = Field(default=800, alias="CHUNK_SIZE_TOKENS")
    chunk_overlap_tokens: int = Field(default=120, alias="CHUNK_OVERLAP_TOKENS")

    # Rate limiting
    rate_limit_auth: str = Field(default="10/minute", alias="RATE_LIMIT_AUTH")
    rate_limit_qa: str = Field(default="20/minute", alias="RATE_LIMIT_QA")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def storage_path(self) -> Path:
        p = Path(self.storage_local_path)
        p.mkdir(parents=True, exist_ok=True)
        return p

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
        "populate_by_name": True,
    }


# Singleton
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
