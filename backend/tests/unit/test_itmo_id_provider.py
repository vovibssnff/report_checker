from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.adapters.driven.auth.itmo_id_provider import ItmoIdAuthProvider
from app.core.domain.entities.user import User
from app.core.domain.value_objects import UserId, UserRole


class _FakeResponse:
    def __init__(self, payload: dict, ok: bool = True) -> None:
        self._payload = payload
        self._ok = ok

    def raise_for_status(self) -> None:
        if not self._ok:
            raise RuntimeError("http error")

    def json(self) -> dict:
        return self._payload


class _FakeClient:
    def __init__(self, post_payload: dict | None = None, get_payload: dict | None = None, ok: bool = True) -> None:
        self._post_payload = post_payload or {}
        self._get_payload = get_payload or {}
        self._ok = ok

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, *args, **kwargs):
        return _FakeResponse(self._post_payload, ok=self._ok)

    async def get(self, *args, **kwargs):
        return _FakeResponse(self._get_payload, ok=self._ok)


@pytest.fixture()
def user_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.get_by_itmo_id.return_value = None
    repo.get_by_email.return_value = None
    return repo


@pytest.mark.asyncio
async def test_get_login_url_returns_itmo_auth_url(user_repo: AsyncMock) -> None:
    provider = ItmoIdAuthProvider(user_repo)
    url = await provider.get_login_url("state123")
    assert "id.itmo.ru" in url
    assert "state=state123" in url


@pytest.mark.asyncio
async def test_exchange_code_posts_to_token_endpoint(monkeypatch, user_repo: AsyncMock) -> None:
    monkeypatch.setattr(
        "app.adapters.driven.auth.itmo_id_provider.httpx.AsyncClient",
        lambda: _FakeClient(post_payload={"access_token": "tok", "refresh_token": "ref"}),
    )
    provider = ItmoIdAuthProvider(user_repo)
    token = await provider.exchange_code("code")
    assert token == "tok"
    assert provider._last_refresh_token == "ref"


@pytest.mark.asyncio
async def test_exchange_code_raises_on_http_error(monkeypatch, user_repo: AsyncMock) -> None:
    monkeypatch.setattr("app.adapters.driven.auth.itmo_id_provider.httpx.AsyncClient", lambda: _FakeClient(ok=False))
    provider = ItmoIdAuthProvider(user_repo)
    with pytest.raises(RuntimeError):
        await provider.exchange_code("bad")


@pytest.mark.asyncio
async def test_get_user_info_creates_new_user(monkeypatch, user_repo: AsyncMock) -> None:
    payload = {"sub": "itmo-sub", "email": "user@test.com", "name": "Test", "edu": {"x": "y"}}
    monkeypatch.setattr(
        "app.adapters.driven.auth.itmo_id_provider.httpx.AsyncClient",
        lambda: _FakeClient(get_payload=payload),
    )
    created_user = User(
        id=UserId(uuid4()),
        email="user@test.com",
        name="Test",
        role=UserRole.STUDENT,
        itmo_id="itmo-sub",
        created_at=datetime.now(UTC),
    )
    user_repo.create.return_value = created_user
    provider = ItmoIdAuthProvider(user_repo)
    result = await provider.get_user_info("tok")
    assert result == created_user
    user_repo.create.assert_awaited()


@pytest.mark.asyncio
async def test_get_user_info_updates_existing_user(monkeypatch, user_repo: AsyncMock) -> None:
    payload = {"sub": "itmo-sub", "email": "new@test.com", "name": "New Name", "work": {"dep": "x"}}
    monkeypatch.setattr(
        "app.adapters.driven.auth.itmo_id_provider.httpx.AsyncClient",
        lambda: _FakeClient(get_payload=payload),
    )
    existing = User(
        id=UserId(uuid4()),
        email="old@test.com",
        name="Old Name",
        role=UserRole.STUDENT,
        itmo_id="itmo-sub",
        created_at=datetime.now(UTC),
    )
    user_repo.get_by_itmo_id.return_value = existing
    updated = existing.__class__(
        **{**existing.__dict__, "email": "new@test.com", "name": "New Name", "role": UserRole.TEACHER}
    )
    user_repo.update.return_value = updated
    provider = ItmoIdAuthProvider(user_repo)
    result = await provider.get_user_info("tok")
    assert result.role == UserRole.TEACHER
    user_repo.update.assert_awaited()


def test_detect_role_helpers(user_repo: AsyncMock) -> None:
    provider = ItmoIdAuthProvider(user_repo)
    assert provider._detect_role({"work": {"x": 1}}) == UserRole.TEACHER
    assert provider._detect_role({"edu": {"x": 1}}) == UserRole.STUDENT
    assert provider._detect_role({"foo": "bar"}) == UserRole.STUDENT
