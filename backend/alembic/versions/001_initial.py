"""Initial schema with all tables

Revision ID: 001_initial
Revises: 
Create Date: 2026-10-24
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR
from pgvector.sqlalchemy import Vector

revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # Users
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('username', sa.String(100), unique=True, nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_admin', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_username', 'users', ['username'])

    # Documents
    op.create_table(
        'documents',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('filename', sa.String(500), nullable=False),
        sa.Column('original_filename', sa.String(500), nullable=False),
        sa.Column('file_type', sa.String(20), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('content_hash', sa.String(64), nullable=False),
        sa.Column('page_count', sa.Integer(), nullable=True),
        sa.Column('storage_path', sa.String(1000), nullable=False),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_documents_user_id', 'documents', ['user_id'])
    op.create_index('ix_documents_status', 'documents', ['status'])
    op.create_index('ix_documents_content_hash', 'documents', ['content_hash'])
    op.create_index('ix_documents_user_status', 'documents', ['user_id', 'status'])
    op.create_index('ix_documents_content_hash_user', 'documents', ['content_hash', 'user_id'])

    # Document Chunks
    op.create_table(
        'document_chunks',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('document_id', UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('section_path', sa.String(1000), nullable=True),
        sa.Column('token_count', sa.Integer(), nullable=False),
        sa.Column('embedding', Vector(384), nullable=True),
        sa.Column('search_vector', TSVECTOR, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_chunks_document_id', 'document_chunks', ['document_id'])
    op.create_index('ix_chunks_user_id', 'document_chunks', ['user_id'])
    op.create_index('ix_chunks_document_index', 'document_chunks', ['document_id', 'chunk_index'])
    op.create_index('ix_chunks_user_document', 'document_chunks', ['user_id', 'document_id'])
    op.create_index('ix_chunks_search_vector', 'document_chunks', ['search_vector'], postgresql_using='gin')

    # HNSW index for vector similarity
    op.execute(
        'CREATE INDEX ix_chunks_embedding_hnsw ON document_chunks '
        'USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64)'
    )

    # Conversations
    op.create_table(
        'conversations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(500), default='New Conversation'),
        sa.Column('document_scope', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_conversations_user_id', 'conversations', ['user_id'])

    # Messages
    op.create_table(
        'messages',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', UUID(as_uuid=True), sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('citations_json', sa.Text(), nullable=True),
        sa.Column('insufficient_evidence', sa.Boolean(), default=False),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('retrieval_latency_ms', sa.Integer(), nullable=True),
        sa.Column('generation_latency_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_messages_conversation_id', 'messages', ['conversation_id'])

    # Citations
    op.create_table(
        'citations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('message_id', UUID(as_uuid=True), sa.ForeignKey('messages.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chunk_id', UUID(as_uuid=True), sa.ForeignKey('document_chunks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('document_id', UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('citation_label', sa.String(10), nullable=False),
        sa.Column('excerpt', sa.Text(), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('section_path', sa.String(1000), nullable=True),
        sa.Column('retrieval_score', sa.Float(), nullable=True),
        sa.Column('retrieval_rank', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_citations_message_id', 'citations', ['message_id'])

    # Feedback
    op.create_table(
        'feedback',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('message_id', UUID(as_uuid=True), sa.ForeignKey('messages.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_feedback_user_id', 'feedback', ['user_id'])
    op.create_index('ix_feedback_message_id', 'feedback', ['message_id'])

    # Processing Jobs
    op.create_table(
        'processing_jobs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('document_id', UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('step', sa.String(50), nullable=True),
        sa.Column('progress', sa.Float(), default=0.0),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_processing_jobs_document_id', 'processing_jobs', ['document_id'])

    # Model Config
    op.create_table(
        'model_config',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('key', sa.String(100), unique=True, nullable=False),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('updated_by', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_model_config_key', 'model_config', ['key'])

    # Audit Events
    op.create_table(
        'audit_events',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=True),
        sa.Column('resource_id', sa.String(100), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_audit_events_user_id', 'audit_events', ['user_id'])
    op.create_index('ix_audit_events_action', 'audit_events', ['action'])
    op.create_index('ix_audit_events_created_at', 'audit_events', ['created_at'])


def downgrade() -> None:
    op.drop_table('audit_events')
    op.drop_table('model_config')
    op.drop_table('processing_jobs')
    op.drop_table('feedback')
    op.drop_table('citations')
    op.drop_table('messages')
    op.drop_table('conversations')
    op.drop_table('document_chunks')
    op.drop_table('documents')
    op.drop_table('users')
    op.execute('DROP EXTENSION IF EXISTS vector')
