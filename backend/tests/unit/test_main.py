from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.adapters.driving.web import dependencies
from app.main import _build_services, _noop_lifespan, create_app, lifespan

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


def test_create_app_health_and_exception_handlers() -> None:
    app = create_app(use_default_services=False)

    @app.get("/raise-http")
    async def raise_http() -> None:
        raise HTTPException(status_code=418, detail="teapot")

    @app.get("/raise-error")
    async def raise_error() -> None:
        raise RuntimeError("boom")

    with TestClient(app, raise_server_exceptions=False) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json() == {"status": "ok"}

        resp_http = client.get("/raise-http")
        assert resp_http.status_code == 418
        assert resp_http.json() == {"detail": "teapot"}

        resp_error = client.get("/raise-error")
        assert resp_error.status_code == 500
        assert resp_error.json() == {"detail": "Internal Server Error"}


@pytest.mark.asyncio
async def test_noop_lifespan_context_manager() -> None:
    app = FastAPI()
    async with _noop_lifespan(app):
        assert True


@pytest.mark.asyncio
async def test_build_services_registers_dependency_overrides_and_generators_work() -> None:
    app = FastAPI()
    _build_services(app)

    required = [
        dependencies.get_upload_service,
        dependencies.get_check_service,
        dependencies.get_query_service,
        dependencies.get_rule_service,
        dependencies.get_auth_service,
    ]
    for dep in required:
        assert dep in app.dependency_overrides

    for dep in required:
        provider = app.dependency_overrides[dep]
        gen = provider(session=object())
        service = await anext(gen)
        assert service is not None
        await gen.aclose()


@pytest.mark.asyncio
async def test_lifespan_syncs_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    app = FastAPI()

    class DummyRegistry:
        pass

    fake_registry = DummyRegistry()

    class DummyRuleRepo:
        def __init__(self, session: object) -> None:
            self.session = session
            self.sync_from_registry = AsyncMock()

    dummy_repo = DummyRuleRepo(session=object())
    dummy_session = AsyncMock()

    @asynccontextmanager
    async def fake_session_factory() -> AsyncIterator[AsyncMock]:
        yield dummy_session

    monkeypatch.setattr("app.main._build_services", lambda _app: None)
    monkeypatch.setattr("app.main.async_session_factory", fake_session_factory)
    monkeypatch.setattr("app.main.PgCheckRuleRepository", lambda session: dummy_repo)
    monkeypatch.setattr("app.main.RuleRegistry.instance", lambda: fake_registry)

    async with lifespan(app):
        pass

    dummy_repo.sync_from_registry.assert_awaited_once_with(fake_registry)
    dummy_session.commit.assert_awaited_once()
