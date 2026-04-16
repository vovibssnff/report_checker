from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import httpx
import pytest
from httpx import ASGITransport

from app.adapters.driven.auth.itmo_id_provider import ItmoIdAuthProvider
from app.adapters.driving.web import dependencies
from app.config import settings
from app.core.domain.entities.user import User
from app.core.domain.value_objects import UserId, UserRole
from app.core.services.user_service import UserService


class _FakeItmoAuthProvider(ItmoIdAuthProvider):
    async def exchange_code(self, code: str) -> str:
        return "itmo-token"

    async def get_user_info(self, token: str) -> User:
        user = User(
            id=UserId(uuid4()),
            email="itmo@test.com",
            name="ITMO User",
            role=UserRole.STUDENT,
            itmo_id="itmo-sub",
            created_at=datetime.now(UTC),
        )
        created = await self._user_repo.create(user)
        return created


@pytest.fixture()
def itmo_user_repo(monkeypatch) -> AsyncMock:
    repo = AsyncMock()
    user = User(
        id=UserId(uuid4()),
        email="itmo@test.com",
        name="ITMO User",
        role=UserRole.STUDENT,
        itmo_id="itmo-sub",
        created_at=datetime.now(UTC),
    )
    repo.get_by_itmo_id.return_value = None
    repo.get_by_email.return_value = None
    repo.create.return_value = user
    repo.get_by_id.return_value = user
    monkeypatch.setattr(settings, "AUTH_MODE", "itmo_id")
    return repo


@pytest.fixture()
async def itmo_client(itmo_user_repo: AsyncMock):
    from app.main import create_app

    application = create_app()
    auth_service = UserService(_FakeItmoAuthProvider(itmo_user_repo), itmo_user_repo)
    application.dependency_overrides[dependencies.get_auth_service] = lambda: auth_service
    application.dependency_overrides[dependencies.get_user_repo] = lambda: itmo_user_repo
    transport = ASGITransport(app=application)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def test_auth_mode_returns_itmo_id(itmo_client: httpx.AsyncClient):
    resp = await itmo_client.get("/api/v1/auth/mode")
    assert resp.status_code == 200
    assert resp.json()["mode"] == "itmo_id"


async def test_login_returns_itmo_redirect_url(itmo_client: httpx.AsyncClient):
    resp = await itmo_client.get("/api/v1/auth/login")
    assert resp.status_code == 200
    assert "id.itmo.ru" in resp.json()["redirect_url"]


async def test_callback_sets_cookie_and_redirects(itmo_client: httpx.AsyncClient):
    resp = await itmo_client.get("/api/v1/auth/callback?code=abc&state=s")
    assert resp.status_code == 302
    assert "access_token" in resp.headers.get("set-cookie", "")


async def test_dev_endpoints_return_404_in_itmo_mode(itmo_client: httpx.AsyncClient):
    reg = await itmo_client.post(
        "/api/v1/auth/dev/register",
        json={"email": "x@test.com", "name": "X", "password": "qwerty123", "role": "student"},
    )
    login = await itmo_client.post("/api/v1/auth/dev/login", json={"email": "x@test.com", "password": "qwerty123"})
    assert reg.status_code == 404
    assert login.status_code == 404
