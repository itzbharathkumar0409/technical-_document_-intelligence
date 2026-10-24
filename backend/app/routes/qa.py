"""Q&A and Conversation API routes."""

import json
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models import Conversation, Citation, Document, Message, User
from app.schemas import (
    AnswerResponse,
    CitationDetail,
    ConversationCreate,
    ConversationListResponse,
    ConversationResponse,
    MessageResponse,
    QuestionRequest,
)
from app.services.retrieval import hybrid_retrieve
from app.services.rag import generate_answer

router = APIRouter(tags=["Q&A"])


# ─── Conversations ───────────────────────────────────────────────────────────

@router.post("/conversations", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    data: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new conversation."""
    doc_scope = None
    if data.document_ids:
        # Verify ownership of all documents
        for doc_id in data.document_ids:
            result = await db.execute(
                select(Document).where(
                    and_(Document.id == doc_id, Document.user_id == current_user.id)
                )
            )
            if not result.scalar_one_or_none():
                raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")
        doc_scope = json.dumps([str(d) for d in data.document_ids])

    conversation = Conversation(
        user_id=current_user.id,
        title=data.title,
        document_scope=doc_scope,
    )
    db.add(conversation)
    await db.flush()
    return ConversationResponse.model_validate(conversation)


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all conversations for the current user."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
    )
    conversations = result.scalars().all()
    return ConversationListResponse(
        conversations=[ConversationResponse.model_validate(c) for c in conversations],
        total=len(conversations),
    )


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
async def get_conversation_messages(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all messages in a conversation."""
    # Verify conversation ownership
    result = await db.execute(
        select(Conversation).where(
            and_(
                Conversation.id == conversation_id,
                Conversation.user_id == current_user.id,
            )
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Conversation not found")

    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    messages = result.scalars().all()

    response = []
    for msg in messages:
        citations = []
        if msg.citations_json:
            try:
                citations = [CitationDetail(**c) for c in json.loads(msg.citations_json)]
            except Exception:
                pass

        response.append(MessageResponse(
            id=msg.id,
            role=msg.role,
            content=msg.content,
            citations=citations,
            insufficient_evidence=msg.insufficient_evidence,
            latency_ms=msg.latency_ms,
            created_at=msg.created_at,
        ))

    return response


@router.delete("/conversations/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a conversation."""
    result = await db.execute(
        select(Conversation).where(
            and_(
                Conversation.id == conversation_id,
                Conversation.user_id == current_user.id,
            )
        )
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await db.delete(conversation)


# ─── Question Answering ──────────────────────────────────────────────────────

@router.post("/ask", response_model=AnswerResponse)
async def ask_question(
    data: QuestionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Ask a question. Performs hybrid retrieval, generates a grounded answer with
    citation validation, and stores the conversation.
    """
    # Determine conversation
    conversation = None
    if data.conversation_id:
        result = await db.execute(
            select(Conversation).where(
                and_(
                    Conversation.id == data.conversation_id,
                    Conversation.user_id == current_user.id,
                )
            )
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        # Create new conversation
        conversation = Conversation(
            user_id=current_user.id,
            title=data.question[:100],
        )
        db.add(conversation)
        await db.flush()

    # Determine document scope
    document_ids = data.document_ids
    if not document_ids and conversation.document_scope:
        try:
            document_ids = [uuid.UUID(d) for d in json.loads(conversation.document_scope)]
        except Exception:
            pass

    # Verify document ownership if specific docs are scoped
    if document_ids:
        for doc_id in document_ids:
            result = await db.execute(
                select(Document).where(
                    and_(Document.id == doc_id, Document.user_id == current_user.id)
                )
            )
            if not result.scalar_one_or_none():
                raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")

    # Handle follow-up: get conversation history for query rewriting
    query = data.question
    if data.conversation_id:
        history_result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .order_by(Message.created_at.desc())
            .limit(5)
        )
        history = list(reversed(history_result.scalars().all()))
        if history:
            # Simple follow-up rewriting: include last exchange as context
            context = "\n".join(
                f"{'User' if m.role == 'user' else 'Assistant'}: {m.content[:200]}"
                for m in history[-4:]
            )
            query = f"Given this conversation context:\n{context}\n\nCurrent question: {data.question}"

    # Store user message
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=data.question,
    )
    db.add(user_message)
    await db.flush()

    # Hybrid retrieval
    retrieved_passages, retrieval_timings = await hybrid_retrieve(
        db, query, current_user.id, document_ids
    )

    # Generate grounded answer
    rag_result = await generate_answer(query, retrieved_passages, retrieval_timings)

    # Store assistant message
    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=rag_result["answer"],
        citations_json=json.dumps(rag_result["citations"]),
        insufficient_evidence=rag_result["insufficient_evidence"],
        latency_ms=rag_result["latency_breakdown"].get("total_ms"),
        retrieval_latency_ms=rag_result["latency_breakdown"].get("total_retrieval_ms"),
        generation_latency_ms=rag_result["latency_breakdown"].get("generation_ms"),
    )
    db.add(assistant_message)
    await db.flush()

    # Store citations in citation table
    for cit in rag_result["citations"]:
        citation_record = Citation(
            message_id=assistant_message.id,
            chunk_id=uuid.UUID(cit["chunk_id"]),
            document_id=uuid.UUID(cit["document_id"]),
            citation_label=cit["citation_label"],
            excerpt=cit["excerpt"],
            page_number=cit.get("page_number"),
            section_path=cit.get("section_path"),
            retrieval_score=cit.get("retrieval_score"),
            retrieval_rank=cit["retrieval_rank"],
        )
        db.add(citation_record)

    # Update conversation title if this is the first question
    msg_count = await db.execute(
        select(func.count()).select_from(
            select(Message).where(Message.conversation_id == conversation.id).subquery()
        )
    )
    if (msg_count.scalar() or 0) <= 2:
        conversation.title = data.question[:100]

    await db.flush()

    # Build response
    citations = [
        CitationDetail(
            citation_label=c["citation_label"],
            chunk_id=uuid.UUID(c["chunk_id"]),
            document_id=uuid.UUID(c["document_id"]),
            filename=c["filename"],
            page_number=c.get("page_number"),
            section_path=c.get("section_path"),
            excerpt=c["excerpt"],
            retrieval_score=c.get("retrieval_score"),
            retrieval_rank=c["retrieval_rank"],
        )
        for c in rag_result["citations"]
    ]

    return AnswerResponse(
        message_id=assistant_message.id,
        conversation_id=conversation.id,
        answer=rag_result["answer"],
        citations=citations,
        insufficient_evidence=rag_result["insufficient_evidence"],
        latency_breakdown=rag_result["latency_breakdown"],
    )


# ─── Citation Source Retrieval ───────────────────────────────────────────────

@router.get("/citations/{message_id}")
async def get_message_citations(
    message_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get citations for a specific message."""
    # Verify the message belongs to the user's conversation
    result = await db.execute(
        select(Message)
        .join(Conversation)
        .where(
            and_(
                Message.id == message_id,
                Conversation.user_id == current_user.id,
            )
        )
    )
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    result = await db.execute(
        select(Citation)
        .where(Citation.message_id == message_id)
        .order_by(Citation.retrieval_rank)
    )
    citations = result.scalars().all()

    return [
        {
            "citation_label": c.citation_label,
            "chunk_id": str(c.chunk_id),
            "document_id": str(c.document_id),
            "page_number": c.page_number,
            "section_path": c.section_path,
            "excerpt": c.excerpt,
            "retrieval_score": c.retrieval_score,
            "retrieval_rank": c.retrieval_rank,
        }
        for c in citations
    ]
