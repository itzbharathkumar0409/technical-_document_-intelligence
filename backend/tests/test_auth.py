"""Tests for authentication: password hashing, JWT tokens, protected routes."""

import uuid
from datetime import datetime, timedelta, timezone
import pytest
from fastapi import HTTPException, status
from jose import jwt

from app.auth import (
    create_access_token,
    decode_access_token,
    get_admin_user,
    hash_password,
    verify_password,
)
from app.config import get_settings
from app.models import User


class TestPasswordSecurity:
    """Tests for bcrypt password hashing and verification."""

    def test_password_hash_and_verify(self):
        password = "SecurePassword123!"
        hashed = hash_password(password)

        # Hash must not equal plain text
        assert hashed != password
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")

        # Verification must succeed for correct password
        assert verify_password(password, hashed) is True

        # Verification must fail for incorrect password
        assert verify_password("WrongPassword123!", hashed) is False
        assert verify_password("", hashed) is False

    def test_password_hash_uniqueness(self):
        password = "IdenticalPassword"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Each salt should be unique
        assert hash1 != hash2
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestTokenManagement:
    """Tests for JWT token creation, expiration, and decoding."""

    def test_create_and_decode_token(self):
        user_id = uuid.uuid4()
        token = create_access_token(user_id=user_id, is_admin=False)

        assert isinstance(token, str)
        assert len(token) > 20

        payload = decode_access_token(token)
        assert payload["sub"] == str(user_id)
        assert payload["admin"] is False
        assert "exp" in payload
        assert "iat" in payload

    def test_admin_claim_in_token(self):
        user_id = uuid.uuid4()
        token = create_access_token(user_id=user_id, is_admin=True)

        payload = decode_access_token(token)
        assert payload["sub"] == str(user_id)
        assert payload["admin"] is True

    def test_invalid_token_rejected(self):
        with pytest.raises(HTTPException) as exc_info:
            decode_access_token("not-a-valid-jwt-token")
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid or expired token" in exc_info.value.detail

    def test_expired_token_rejected(self):
        settings = get_settings()
        user_id = uuid.uuid4()
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        expired_payload = {
            "sub": str(user_id),
            "admin": False,
            "exp": past_time,
            "iat": past_time - timedelta(minutes=5),
        }
        expired_token = jwt.encode(expired_payload, settings.secret_key, algorithm="HS256")

        with pytest.raises(HTTPException) as exc_info:
            decode_access_token(expired_token)
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


class TestAdminDependency:
    """Tests for admin-only authorization dependency."""

    @pytest.mark.asyncio
    async def test_admin_access_allowed(self):
        admin_user = User(
            id=uuid.uuid4(),
            email="admin@example.com",
            username="admin",
            hashed_password="hash",
            is_active=True,
            is_admin=True,
        )
        result = await get_admin_user(current_user=admin_user)
        assert result == admin_user

    @pytest.mark.asyncio
    async def test_non_admin_access_forbidden(self):
        normal_user = User(
            id=uuid.uuid4(),
            email="user@example.com",
            username="user",
            hashed_password="hash",
            is_active=True,
            is_admin=False,
        )
        with pytest.raises(HTTPException) as exc_info:
            await get_admin_user(current_user=normal_user)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Admin access required" in exc_info.value.detail
