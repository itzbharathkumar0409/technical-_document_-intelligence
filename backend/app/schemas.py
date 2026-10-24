"""Pydantic schemas for request/response validation."""

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ─── Auth Schemas ─────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: str = Field(..., max_length=255, pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    username: str = Field(..., min_length=3, max_length=100, pattern=r'^[a-zA-Z0-9_-]+$')
    password: str = Field(..., min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    username: str
    is_active: bool
    is_admin: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ─── Document Schemas ────────────────────────────────────────────────────────

class DocumentResponse(BaseModel):
    id: uuid.UUID
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    page_count: Optional[int] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
    items: Optional[list[DocumentResponse]] = None
    total: int
    page: int
    page_size: int

    def model_post_init(self, __context):
        if self.items is None:
            self.items = self.documents


class DocumentStatusResponse(BaseModel):
    id: uuid.UUID
    status: str
    step: Optional[str] = None
    progress: float = 0.0
    error_message: Optional[str] = None


# ─── Conversation Schemas ────────────────────────────────────────────────────

class ConversationCreate(BaseModel):
    title: str = "New Conversation"
    document_ids: Optional[list[uuid.UUID]] = None  # Scope to specific documents


class ConversationResponse(BaseModel):
    id: uuid.UUID
    title: str
    document_scope: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationListResponse(BaseModel):
    conversations: list[ConversationResponse]
    total: int


# ─── Message / Q&A Schemas ───────────────────────────────────────────────────

class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=5000)
    conversation_id: Optional[uuid.UUID] = None
    document_ids: Optional[list[uuid.UUID]] = None  # Override scope for this question


class CitationDetail(BaseModel):
    citation_label: str  # [S1], [S2]
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    filename: str
    page_number: Optional[int] = None
    section_path: Optional[str] = None
    excerpt: str
    retrieval_score: Optional[float] = None
    retrieval_rank: int


class AnswerResponse(BaseModel):
    message_id: uuid.UUID
    conversation_id: uuid.UUID
    answer: str
    citations: list[CitationDetail]
    insufficient_evidence: bool = False
    latency_breakdown: dict  # total_ms, retrieval_ms, generation_ms
    model_config_dict: ConfigDict = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    citations: list[CitationDetail] = []
    insufficient_evidence: bool = False
    latency_ms: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ─── Feedback Schemas ────────────────────────────────────────────────────────

class FeedbackCreate(BaseModel):
    message_id: uuid.UUID
    rating: int = Field(..., ge=-1, le=1)  # -1 thumbs down, 1 thumbs up
    comment: Optional[str] = Field(None, max_length=2000)


class FeedbackResponse(BaseModel):
    id: uuid.UUID
    message_id: uuid.UUID
    rating: int
    comment: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ─── Analytics Schemas ───────────────────────────────────────────────────────

class AnalyticsResponse(BaseModel):
    total_documents: int
    total_chunks: int
    total_conversations: int
    total_messages: int
    total_feedback: int
    positive_feedback: int
    negative_feedback: int
    avg_latency_ms: Optional[float] = None
    documents_by_status: dict[str, int]
    queries_last_7_days: int
    metric_type: str = "MEASURED"  # MEASURED, ESTIMATED, UNAVAILABLE


# ─── Settings Schemas ────────────────────────────────────────────────────────

class SettingsUpdate(BaseModel):
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    embedding_provider: Optional[str] = None
    embedding_model: Optional[str] = None
    embedding_dimension: Optional[int] = None
    retrieval_vector_top_k: Optional[int] = None
    retrieval_keyword_top_k: Optional[int] = None
    retrieval_final_top_k: Optional[int] = None
    relevance_threshold: Optional[float] = None
    reranker_enabled: Optional[bool] = None
    chunk_size_tokens: Optional[int] = None
    chunk_overlap_tokens: Optional[int] = None


class SettingsResponse(BaseModel):
    llm_provider: str
    llm_model: str
    embedding_provider: str
    embedding_model: str
    embedding_dimension: int
    retrieval_vector_top_k: int
    retrieval_keyword_top_k: int
    retrieval_final_top_k: int
    relevance_threshold: float
    reranker_enabled: bool
    chunk_size_tokens: int
    chunk_overlap_tokens: int


class ConnectionTestResult(BaseModel):
    provider: str
    model: str
    success: bool
    message: str
    latency_ms: Optional[float] = None


# ─── Health Check ─────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    database: str
    llm_provider: str
    embedding_provider: str
    version: str = "0.1.0"


# ─── Error Schema ─────────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
