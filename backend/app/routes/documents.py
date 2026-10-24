"""Document management API routes: upload, list, detail, delete, status."""

import hashlib
import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.config import get_settings
from app.database import get_db
from app.models import Document, DocumentChunk, ProcessingJob, User
from app.schemas import DocumentListResponse, DocumentResponse, DocumentStatusResponse

router = APIRouter(prefix="/documents", tags=["Documents"])

# Allowed file types and their MIME types
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "text/markdown",
    "text/x-markdown",
    "application/octet-stream",  # Fallback for some file types
}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal."""
    # Remove directory components
    filename = os.path.basename(filename)
    # Remove null bytes and other dangerous characters
    filename = filename.replace("\x00", "").replace("/", "_").replace("\\", "_")
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:250] + ext
    return filename


def validate_file_extension(filename: str) -> str:
    """Validate file extension and return it."""
    _, ext = os.path.splitext(filename.lower())
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )
    return ext


def get_file_type(ext: str) -> str:
    """Map extension to file type."""
    mapping = {".pdf": "pdf", ".docx": "docx", ".txt": "txt", ".md": "md"}
    return mapping.get(ext, "unknown")


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a document for processing."""
    settings = get_settings()

    # Validate filename and extension
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    safe_filename = sanitize_filename(file.filename)
    ext = validate_file_extension(safe_filename)
    file_type = get_file_type(ext)

    # Read file content
    content = await file.read()

    # Validate size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB",
        )

    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    # Validate MIME type by sniffing content
    try:
        import magic
        detected_mime = magic.from_buffer(content, mime=True)
        # Allow detected MIME or common fallbacks
        if detected_mime not in ALLOWED_MIME_TYPES and not detected_mime.startswith("text/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File content does not match an allowed document type (detected: {detected_mime})",
            )
    except ImportError:
        # python-magic not available, skip sniffing (documented fallback)
        pass

    # Compute content hash
    content_hash = hashlib.sha256(content).hexdigest()

    # Check for duplicate (same content + same user)
    result = await db.execute(
        select(Document).where(
            and_(
                Document.content_hash == content_hash,
                Document.user_id == current_user.id,
            )
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        # Idempotent: return existing document if same content
        return DocumentResponse.model_validate(existing)

    # Store file
    doc_id = uuid.uuid4()
    storage_dir = Path(settings.storage_local_path) / str(current_user.id) / str(doc_id)
    storage_dir.mkdir(parents=True, exist_ok=True)
    storage_path = storage_dir / safe_filename

    with open(storage_path, "wb") as f:
        f.write(content)

    # Create document record
    document = Document(
        id=doc_id,
        user_id=current_user.id,
        filename=safe_filename,
        original_filename=file.filename,
        file_type=file_type,
        file_size=len(content),
        content_hash=content_hash,
        storage_path=str(storage_path),
        status="pending",
    )
    db.add(document)

    # Create processing job
    job = ProcessingJob(
        document_id=doc_id,
        status="pending",
    )
    db.add(job)
    await db.commit()
    await db.refresh(document)

    # Trigger background processing
    from app.services.ingestion import process_document
    background_tasks.add_task(process_document, str(doc_id))

    return DocumentResponse.model_validate(document)


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List documents for the current user."""
    query = select(Document).where(Document.user_id == current_user.id)

    if status_filter:
        query = query.where(Document.status == status_filter)

    if search:
        query = query.where(Document.original_filename.ilike(f"%{search}%"))

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Paginate
    query = query.order_by(Document.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    documents = result.scalars().all()

    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(d) for d in documents],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get document details. Only accessible by the document owner."""
    result = await db.execute(
        select(Document).where(
            and_(Document.id == document_id, Document.user_id == current_user.id)
        )
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResponse.model_validate(document)


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get document processing status."""
    result = await db.execute(
        select(Document).where(
            and_(Document.id == document_id, Document.user_id == current_user.id)
        )
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Get latest processing job
    job_result = await db.execute(
        select(ProcessingJob)
        .where(ProcessingJob.document_id == document_id)
        .order_by(ProcessingJob.created_at.desc())
        .limit(1)
    )
    job = job_result.scalar_one_or_none()

    return DocumentStatusResponse(
        id=document.id,
        status=document.status,
        step=job.step if job else None,
        progress=job.progress if job else 0.0,
        error_message=document.error_message,
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a document and all associated data. Only the owner can delete."""
    result = await db.execute(
        select(Document).where(
            and_(Document.id == document_id, Document.user_id == current_user.id)
        )
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete file from storage
    try:
        storage_path = Path(document.storage_path)
        if storage_path.exists():
            storage_path.unlink()
        # Remove directory if empty
        parent = storage_path.parent
        if parent.exists() and not list(parent.iterdir()):
            parent.rmdir()
    except Exception:
        pass  # Non-critical: file cleanup can fail

    # Delete from database (cascades to chunks, citations, etc.)
    await db.delete(document)


@router.get("/{document_id}/chunks")
async def get_document_chunks(
    document_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get document chunks for source viewing."""
    # Verify ownership
    result = await db.execute(
        select(Document).where(
            and_(Document.id == document_id, Document.user_id == current_user.id)
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Document not found")

    query = (
        select(DocumentChunk)
        .where(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index)
    )

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar() or 0

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    chunks = result.scalars().all()

    return {
        "chunks": [
            {
                "id": str(c.id),
                "chunk_index": c.chunk_index,
                "content": c.content,
                "page_number": c.page_number,
                "section_path": c.section_path,
                "token_count": c.token_count,
            }
            for c in chunks
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
