from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from jose import jwt
from starlette.requests import Request

from app.adapters.driving.web.dependencies import (
    get_auth_service,
    get_check_service,
    get_current_user,
    get_query_service,
    get_rule_service,
    get_upload_service,
)
from app.config import settings
from app.core.domain.entities.user import User
from app.core.domain.value_objects import UserId, UserRole


def _request_with_token(token: str | None) -> Request:
    headers: list[tuple[bytes, bytes]] = []
    if token:
        headers.append((b"cookie", f"access_token={token}".encode()))
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/v1/me",
        "headers": headers,
    }
    return Request(scope)


@pytest.mark.asyncio
async def test_current_user_missing_cookie_raises_401() -> None:
    auth_service = AsyncMock()
    request = _request_with_token(None)

    with pytest.raises(Exception) as exc:
        await get_current_user(request, auth_service)

    assert getattr(exc.value, "status_code", None) == 401
    auth_service.get_current_user.assert_not_awaited()


@pytest.mark.asyncio
async def test_current_user_invalid_token_raises_401() -> None:
    auth_service = AsyncMock()
    request = _request_with_token("definitely-not-a-jwt")

    with pytest.raises(Exception) as exc:
        await get_current_user(request, auth_service)

    assert getattr(exc.value, "status_code", None) == 401
    auth_service.get_current_user.assert_not_awaited()


@pytest.mark.asyncio
async def test_current_user_missing_subject_raises_401() -> None:
    auth_service = AsyncMock()
    token = jwt.encode({"foo": "bar"}, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    request = _request_with_token(token)

    with pytest.raises(Exception) as exc:
        await get_current_user(request, auth_service)

    assert getattr(exc.value, "status_code", None) == 401
    auth_service.get_current_user.assert_not_awaited()


@pytest.mark.asyncio
async def test_current_user_success_returns_user() -> None:
    user_id = UserId(uuid4())
    token = jwt.encode({"sub": str(user_id)}, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    request = _request_with_token(token)
    user = User(
        id=user_id,
        email="user@test.com",
        name="Test User",
        role=UserRole.STUDENT,
        itmo_id=None,
        created_at=datetime.now(UTC),
    )
    auth_service = SimpleNamespace(get_current_user=AsyncMock(return_value=user))

    resolved = await get_current_user(request, auth_service)

    assert resolved == user
    auth_service.get_current_user.assert_awaited_once_with(token)


@pytest.mark.asyncio
async def test_current_user_value_error_from_service_maps_to_401() -> None:
    user_id = UserId(uuid4())
    token = jwt.encode({"sub": str(user_id)}, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    request = _request_with_token(token)
    auth_service = SimpleNamespace(get_current_user=AsyncMock(side_effect=ValueError("not found")))

    with pytest.raises(Exception) as exc:
        await get_current_user(request, auth_service)

    assert getattr(exc.value, "status_code", None) == 401


def test_service_dependency_placeholders_raise_not_implemented() -> None:
    with pytest.raises(NotImplementedError):
        get_upload_service()
    with pytest.raises(NotImplementedError):
        get_check_service()
    with pytest.raises(NotImplementedError):
        get_query_service()
    with pytest.raises(NotImplementedError):
        get_rule_service()
    with pytest.raises(NotImplementedError):
        get_auth_service()
