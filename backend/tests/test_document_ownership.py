"""Tests for user-ownership enforcement on documents."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi import HTTPException, status

from app.models import Document, User
from app.routes.documents import get_document, delete_document, get_document_status


class TestUserOwnership:
    """Verify document access is strictly scoped to the document owner."""

    @pytest.fixture
    def user_alice(self):
        return User(
            id=uuid.uuid4(),
            email="alice@example.com",
            username="alice",
            hashed_password="hash_alice",
            is_active=True,
            is_admin=False,
        )

    @pytest.fixture
    def user_bob(self):
        return User(
            id=uuid.uuid4(),
            email="bob@example.com",
            username="bob",
            hashed_password="hash_bob",
            is_active=True,
            is_admin=False,
        )

    @pytest.fixture
    def alice_document(self, user_alice):
        now = datetime.now(timezone.utc)
        return Document(
            id=uuid.uuid4(),
            user_id=user_alice.id,
            filename="alice_spec.pdf",
            original_filename="alice_spec.pdf",
            file_type="pdf",
            file_size=1024,
            content_hash="abc123hash",
            storage_path="./storage/uploads/alice_spec.pdf",
            status="completed",
            created_at=now,
            updated_at=now,
        )

    @pytest.mark.asyncio
    async def test_owner_can_get_document(self, user_alice, alice_document):
        """Alice can retrieve her own document."""
        db_mock = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = alice_document
        db_mock.execute.return_value = mock_result

        doc = await get_document(
            document_id=alice_document.id,
            current_user=user_alice,
            db=db_mock,
        )

        assert doc.id == alice_document.id
        assert doc.filename == alice_document.filename

    @pytest.mark.asyncio
    async def test_non_owner_cannot_get_document(self, user_bob, alice_document):
        """Bob attempting to get Alice's document receives 404 (no information leakage)."""
        db_mock = AsyncMock()
        # Query filters by Document.user_id == Bob.id, returning None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db_mock.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await get_document(
                document_id=alice_document.id,
                current_user=user_bob,
                db=db_mock,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Document not found"

    @pytest.mark.asyncio
    async def test_owner_can_delete_document(self, user_alice, alice_document):
        """Alice can delete her own document."""
        db_mock = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = alice_document
        db_mock.execute.return_value = mock_result

        response = await delete_document(
            document_id=alice_document.id,
            current_user=user_alice,
            db=db_mock,
        )

        assert response is None
        db_mock.delete.assert_called_once_with(alice_document)

    @pytest.mark.asyncio
    async def test_non_owner_cannot_delete_document(self, user_bob, alice_document):
        """Bob cannot delete Alice's document."""
        db_mock = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db_mock.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await delete_document(
                document_id=alice_document.id,
                current_user=user_bob,
                db=db_mock,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Document not found"
        db_mock.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_non_owner_cannot_get_document_status(self, user_bob, alice_document):
        """Bob cannot inspect the processing status of Alice's document."""
        db_mock = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db_mock.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await get_document_status(
                document_id=alice_document.id,
                current_user=user_bob,
                db=db_mock,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
