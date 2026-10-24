"""Integration tests for Auth API endpoints and protected route guards."""

from datetime import datetime, timezone
import uuid
from unittest.mock import AsyncMock, MagicMock
import pytest
from httpx import ASGITransport, AsyncClient

from app.auth import create_access_token, hash_password
from app.database import get_db
from app.main import app
from app.models import User


class TestAuthRoutesAndProtectedAccess:
    """Test auth routes and protected endpoints with and without JWT tokens."""

    @pytest.fixture
    def test_user(self):
        now = datetime.now(timezone.utc)
        return User(
            id=uuid.uuid4(),
            email="testuser@example.com",
            username="testuser",
            hashed_password=hash_password("ValidPassword123!"),
            is_active=True,
            is_admin=False,
            created_at=now,
            updated_at=now,
        )

    @pytest.mark.asyncio
    async def test_protected_route_without_token_returns_401(self):
        """Calling protected route without token must return 401 Unauthorized."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/auth/me")
            assert response.status_code == 401
            assert "Not authenticated" in response.text or "detail" in response.json()

    @pytest.mark.asyncio
    async def test_protected_route_with_invalid_token_returns_401(self):
        """Calling protected route with an invalid bearer token must return 401."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            headers = {"Authorization": "Bearer completely-invalid-token"}
            response = await client.get("/api/auth/me", headers=headers)
            assert response.status_code == 401
            assert "Invalid or expired token" in response.json().get("detail", "")

    @pytest.mark.asyncio
    async def test_protected_route_with_valid_token_returns_profile(self, test_user):
        """Calling protected route with a valid token returns user profile."""
        valid_token = create_access_token(user_id=test_user.id, is_admin=False)

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = test_user
        mock_db.execute.return_value = mock_result

        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                headers = {"Authorization": f"Bearer {valid_token}"}
                response = await client.get("/api/auth/me", headers=headers)
                assert response.status_code == 200
                data = response.json()
                assert data["email"] == test_user.email
                assert data["username"] == test_user.username
                assert "hashed_password" not in data
        finally:
            app.dependency_overrides.pop(get_db, None)

    @pytest.mark.asyncio
    async def test_register_duplicate_email_returns_409(self, test_user):
        """Registering with an already existing email returns 409 Conflict."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = test_user
        mock_db.execute.return_value = mock_result

        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                payload = {
                    "email": test_user.email,
                    "username": "newusername",
                    "password": "Password123!",
                }
                response = await client.post("/api/auth/register", json=payload)
                assert response.status_code == 409
                assert "Email already registered" in response.json().get("detail", "")
        finally:
            app.dependency_overrides.pop(get_db, None)

    @pytest.mark.asyncio
    async def test_login_invalid_password_returns_401(self, test_user):
        """Logging in with invalid password returns 401 Unauthorized."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = test_user
        mock_db.execute.return_value = mock_result

        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                payload = {
                    "email": test_user.email,
                    "password": "WrongPassword!",
                }
                response = await client.post("/api/auth/login", json=payload)
                assert response.status_code == 401
                assert "Invalid email or password" in response.json().get("detail", "")
        finally:
            app.dependency_overrides.pop(get_db, None)

    @pytest.mark.asyncio
    async def test_login_success_returns_jwt_and_user(self, test_user):
        """Logging in with correct credentials returns 200 and access_token."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = test_user
        mock_db.execute.return_value = mock_result

        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                payload = {
                    "email": test_user.email,
                    "password": "ValidPassword123!",
                }
                response = await client.post("/api/auth/login", json=payload)
                assert response.status_code == 200
                data = response.json()
                assert "access_token" in data
                assert data["token_type"] == "bearer"
                assert data["user"]["email"] == test_user.email
        finally:
            app.dependency_overrides.pop(get_db, None)
