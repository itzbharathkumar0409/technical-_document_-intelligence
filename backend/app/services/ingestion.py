"""Document ingestion pipeline: parse, chunk, embed, index."""

import hashlib
import logging
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import tiktoken
from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.config import get_settings
from app.models import Document, DocumentChunk, ProcessingJob

logger = logging.getLogger(__name__)

# Tokenizer for chunk size estimation
try:
    _enc = tiktoken.get_encoding("cl100k_base")
except Exception:
    _enc = None


def count_tokens(text: str) -> int:
    """Count tokens in text."""
    if _enc:
        return len(_enc.encode(text))
    # Fallback: rough estimate of 4 chars per token
    return len(text) // 4


# ─── Document Parsers ────────────────────────────────────────────────────────

def parse_pdf(file_path: str) -> tuple[str, list[dict], int]:
    """Parse PDF file. Returns (full_text, sections, page_count)."""
    from pypdf import PdfReader

    reader = PdfReader(file_path)
    page_count = len(reader.pages)
    sections = []
    full_text_parts = []

    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if text.strip():
            sections.append({
                "content": text,
                "page": i + 1,
                "section_path": f"Page {i + 1}",
            })
            full_text_parts.append(text)

    return "\n\n".join(full_text_parts), sections, page_count


def parse_docx(file_path: str) -> tuple[str, list[dict], int]:
    """Parse DOCX file. Returns (full_text, sections, page_count)."""
    from docx import Document as DocxDocument

    doc = DocxDocument(file_path)
    sections = []
    current_section = {"content": "", "page": 1, "section_path": "Document"}
    heading_stack = []

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue

        # Detect headings
        if para.style and para.style.name and para.style.name.startswith("Heading"):
            # Save current section
            if current_section["content"].strip():
                sections.append(current_section.copy())

            # Update heading stack
            try:
                level = int(para.style.name.split()[-1])
            except (ValueError, IndexError):
                level = 1

            while len(heading_stack) >= level:
                heading_stack.pop()
            heading_stack.append(text)

            current_section = {
                "content": text + "\n",
                "page": 1,  # DOCX doesn't have reliable page numbers
                "section_path": " > ".join(heading_stack),
            }
        else:
            current_section["content"] += text + "\n"

    if current_section["content"].strip():
        sections.append(current_section)

    full_text = "\n".join(s["content"] for s in sections)
    # Rough page estimate
    page_count = max(1, len(full_text) // 3000)

    return full_text, sections, page_count


def parse_markdown(file_path: str) -> tuple[str, list[dict], int]:
    """Parse Markdown file. Returns (full_text, sections, page_count)."""
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    sections = []
    current_section = {"content": "", "page": 1, "section_path": "Document"}
    heading_stack = []

    for line in content.split("\n"):
        stripped = line.strip()
        if stripped.startswith("#"):
            # Count heading level
            level = 0
            for c in stripped:
                if c == "#":
                    level += 1
                else:
                    break
            heading_text = stripped[level:].strip()

            # Save current section
            if current_section["content"].strip():
                sections.append(current_section.copy())

            # Update heading stack
            while len(heading_stack) >= level:
                heading_stack.pop()
            heading_stack.append(heading_text)

            current_section = {
                "content": heading_text + "\n",
                "page": 1,
                "section_path": " > ".join(heading_stack),
            }
        else:
            current_section["content"] += line + "\n"

    if current_section["content"].strip():
        sections.append(current_section)

    full_text = content
    page_count = max(1, len(content) // 3000)

    return full_text, sections, page_count


def parse_txt(file_path: str) -> tuple[str, list[dict], int]:
    """Parse plain text file. Returns (full_text, sections, page_count)."""
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    # Split into paragraph-based sections
    paragraphs = content.split("\n\n")
    sections = []
    for i, para in enumerate(paragraphs):
        if para.strip():
            sections.append({
                "content": para.strip(),
                "page": 1,
                "section_path": f"Section {i + 1}",
            })

    if not sections:
        sections = [{"content": content, "page": 1, "section_path": "Document"}]

    page_count = max(1, len(content) // 3000)
    return content, sections, page_count


PARSERS = {
    "pdf": parse_pdf,
    "docx": parse_docx,
    "md": parse_markdown,
    "txt": parse_txt,
}


# ─── Structure-Aware Chunking ────────────────────────────────────────────────

def is_code_block_or_table(text: str) -> bool:
    """Check if text looks like a code block or table."""
    lines = text.strip().split("\n")
    if len(lines) < 2:
        return False
    # Code block markers
    if lines[0].startswith("```") or lines[0].startswith("~~~"):
        return True
    # Table detection (pipe-delimited)
    pipe_lines = sum(1 for l in lines if "|" in l and l.strip().startswith("|"))
    return pipe_lines > len(lines) * 0.5


def chunk_section(
    section_content: str,
    section_path: str,
    page_number: int,
    max_tokens: int = 800,
    overlap_tokens: int = 120,
) -> list[dict]:
    """Chunk a section with structure awareness."""
    chunks = []
    paragraphs = section_content.split("\n\n")

    current_chunk = ""
    current_tokens = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        para_tokens = count_tokens(para)

        # Never split code blocks or tables
        if is_code_block_or_table(para):
            if current_chunk.strip():
                chunks.append({
                    "content": current_chunk.strip(),
                    "page": page_number,
                    "section_path": section_path,
                    "token_count": current_tokens,
                })
            chunks.append({
                "content": para,
                "page": page_number,
                "section_path": section_path,
                "token_count": para_tokens,
            })
            current_chunk = ""
            current_tokens = 0
            continue

        # Check if adding this paragraph exceeds the limit
        if current_tokens + para_tokens > max_tokens and current_chunk.strip():
            chunks.append({
                "content": current_chunk.strip(),
                "page": page_number,
                "section_path": section_path,
                "token_count": current_tokens,
            })

            # Overlap: keep last portion of current chunk
            if overlap_tokens > 0:
                overlap_text = _get_overlap(current_chunk, overlap_tokens)
                current_chunk = overlap_text + "\n\n" + para
                current_tokens = count_tokens(current_chunk)
            else:
                current_chunk = para
                current_tokens = para_tokens
        else:
            if current_chunk:
                current_chunk += "\n\n" + para
            else:
                current_chunk = para
            current_tokens += para_tokens

    if current_chunk.strip():
        chunks.append({
            "content": current_chunk.strip(),
            "page": page_number,
            "section_path": section_path,
            "token_count": count_tokens(current_chunk.strip()),
        })

    return chunks


def _get_overlap(text: str, overlap_tokens: int) -> str:
    """Get the last overlap_tokens tokens worth of text."""
    words = text.split()
    # Rough: 1 token ≈ 0.75 words
    word_count = int(overlap_tokens * 0.75)
    if word_count >= len(words):
        return text
    return " ".join(words[-word_count:])


# ─── Embedding ───────────────────────────────────────────────────────────────

_embedding_model = None


def get_embedding_model():
    """Load the local embedding model (lazy singleton)."""
    global _embedding_model
    if _embedding_model is None:
        settings = get_settings()
        if settings.embedding_provider == "local":
            try:
                from sentence_transformers import SentenceTransformer
                _embedding_model = SentenceTransformer(settings.embedding_model)
                logger.info(f"Loaded embedding model: {settings.embedding_model}")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                return None
    return _embedding_model


def compute_embeddings(texts: list[str]) -> list[list[float]]:
    """Compute embeddings for a list of texts."""
    settings = get_settings()

    if settings.embedding_provider == "local":
        model = get_embedding_model()
        if model is None:
            logger.warning("Embedding model unavailable, returning empty embeddings")
            return [[] for _ in texts]
        embeddings = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
        return embeddings.tolist()

    elif settings.embedding_provider == "openai":
        import httpx
        response = httpx.post(
            f"{settings.openai_base_url}/embeddings",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={"model": settings.embedding_model, "input": texts},
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        return [item["embedding"] for item in data["data"]]

    else:
        logger.warning(f"Unknown embedding provider: {settings.embedding_provider}")
        return [[] for _ in texts]


# ─── Main Pipeline ───────────────────────────────────────────────────────────

async def process_document(document_id: str):
    """Main ingestion pipeline: parse → chunk → embed → store."""
    settings = get_settings()

    # Create a new engine/session for this background task
    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as db:
        try:
            # Get document
            result = await db.execute(select(Document).where(Document.id == uuid.UUID(document_id)))
            document = result.scalar_one_or_none()
            if not document:
                logger.error(f"Document {document_id} not found")
                return

            # Get or create processing job
            job_result = await db.execute(
                select(ProcessingJob)
                .where(ProcessingJob.document_id == document.id)
                .order_by(ProcessingJob.created_at.desc())
                .limit(1)
            )
            job = job_result.scalar_one_or_none()
            if not job:
                job = ProcessingJob(document_id=document.id)
                db.add(job)

            # Update status
            document.status = "processing"
            job.status = "running"
            job.started_at = datetime.now(timezone.utc)
            await db.commit()

            # Step 1: Parse
            job.step = "extract"
            job.progress = 0.1
            await db.commit()

            parser = PARSERS.get(document.file_type)
            if not parser:
                raise ValueError(f"No parser for file type: {document.file_type}")

            full_text, sections, page_count = parser(document.storage_path)
            document.page_count = page_count

            if not full_text.strip():
                raise ValueError("No text could be extracted from the document")

            job.progress = 0.3
            await db.commit()

            # Step 2: Chunk
            job.step = "chunk"
            job.progress = 0.4
            await db.commit()

            all_chunks = []
            for section in sections:
                section_chunks = chunk_section(
                    section["content"],
                    section["section_path"],
                    section["page"],
                    max_tokens=settings.chunk_size_tokens,
                    overlap_tokens=settings.chunk_overlap_tokens,
                )
                all_chunks.extend(section_chunks)

            if not all_chunks:
                raise ValueError("No chunks generated from the document")

            # Delete old chunks (idempotent reprocessing)
            await db.execute(
                delete(DocumentChunk).where(DocumentChunk.document_id == document.id)
            )

            job.progress = 0.5
            await db.commit()

            # Step 3: Embed
            job.step = "embed"
            job.progress = 0.6
            await db.commit()

            chunk_texts = [c["content"] for c in all_chunks]

            # Batch embedding (process in batches of 32)
            batch_size = 32
            all_embeddings = []
            for i in range(0, len(chunk_texts), batch_size):
                batch = chunk_texts[i : i + batch_size]
                embeddings = compute_embeddings(batch)
                all_embeddings.extend(embeddings)

            job.progress = 0.8
            await db.commit()

            # Step 4: Store chunks with embeddings and tsvector
            job.step = "index"
            job.progress = 0.85
            await db.commit()

            from sqlalchemy import text as sql_text

            for idx, (chunk_data, embedding) in enumerate(zip(all_chunks, all_embeddings)):
                chunk = DocumentChunk(
                    document_id=document.id,
                    user_id=document.user_id,
                    chunk_index=idx,
                    content=chunk_data["content"],
                    page_number=chunk_data.get("page"),
                    section_path=chunk_data.get("section_path"),
                    token_count=chunk_data.get("token_count", count_tokens(chunk_data["content"])),
                    embedding=embedding if embedding else None,
                )
                db.add(chunk)

            await db.flush()

            # Update tsvector for all chunks using SQL
            await db.execute(
                sql_text(
                    "UPDATE document_chunks SET search_vector = to_tsvector('english', content) "
                    "WHERE document_id = :doc_id"
                ),
                {"doc_id": str(document.id)},
            )

            # Finish
            document.status = "completed"
            job.status = "completed"
            job.step = "done"
            job.progress = 1.0
            job.completed_at = datetime.now(timezone.utc)
            await db.commit()

            logger.info(
                f"Document {document_id} processed: {len(all_chunks)} chunks, "
                f"{page_count} pages"
            )

        except Exception as e:
            logger.exception(f"Error processing document {document_id}: {e}")
            try:
                document.status = "failed"
                document.error_message = str(e)[:500]
                if job:
                    job.status = "failed"
                    job.error_message = str(e)[:500]
                await db.commit()
            except Exception:
                pass

    await engine.dispose()
