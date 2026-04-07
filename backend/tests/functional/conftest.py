from __future__ import annotations

import io
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import httpx
import pikepdf
import pytest
from httpx import ASGITransport
from jose import jwt

from app.adapters.driven.auth.dev_auth_provider import DevAuthProvider
from app.adapters.driving.web import dependencies
from app.checkers.engine import CheckerEngine
from app.config import settings
from app.core.domain.entities.user import User
from app.core.domain.value_objects import (
    CheckRuleId,
    DocumentId,
    DocumentStatus,
    DocumentType,
    UserId,
    UserRole,
)
from app.core.services.check_service import CheckService
from app.core.services.document_service import DocumentService, ValidationResult
from app.core.services.user_service import UserService

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from app.core.domain.entities.check_result import CheckResult
    from app.core.domain.entities.check_rule import CheckRule
    from app.core.domain.entities.document import Document


class _StrKeyDict(dict):
    def __setitem__(self, key, value):
        super().__setitem__(str(key), value)

    def __getitem__(self, key):
        return super().__getitem__(str(key))

    def __contains__(self, key):
        return super().__contains__(str(key))

    def get(self, key, default=None):
        return super().get(str(key), default)

    def pop(self, key, *args):
        return super().pop(str(key), *args)


def make_minimal_pdf() -> bytes:
    pdf = pikepdf.Pdf.new()
    pdf.add_blank_page(page_size=(612, 792))
    buf = io.BytesIO()
    pdf.save(buf)
    return buf.getvalue()


FAKE_PDF = make_minimal_pdf()


def _make_token(user_id: uuid.UUID) -> str:
    return jwt.encode(
        {"sub": str(user_id)},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


@pytest.fixture()
def test_user() -> User:
    return User(
        id=UserId(uuid.uuid4()),
        email="student@test.com",
        name="Test Student",
        role=UserRole.STUDENT,
        itmo_id=None,
        created_at=datetime.now(UTC),
    )


@pytest.fixture()
def admin_user() -> User:
    return User(
        id=UserId(uuid.uuid4()),
        email="admin@test.com",
        name="Test Admin",
        role=UserRole.ADMIN,
        itmo_id=None,
        created_at=datetime.now(UTC),
    )


@pytest.fixture()
def user_repo() -> AsyncMock:
    repo = AsyncMock()
    _store: dict[str, User] = _StrKeyDict()

    async def _create(user: User) -> User:
        _store[user.id] = user
        return user

    async def _get_by_id(user_id: UserId) -> User:
        if user_id in _store:
            return _store[user_id]
        raise ValueError(f"User {user_id} not found")

    async def _get_by_email(email: str) -> User | None:
        for u in _store.values():
            if u.email == email:
                return u
        return None

    repo.create.side_effect = _create
    repo.get_by_id.side_effect = _get_by_id
    repo.get_by_email.side_effect = _get_by_email
    repo.get_by_itmo_id.return_value = None
    repo._store = _store
    return repo


@pytest.fixture()
def doc_repo() -> AsyncMock:
    repo = AsyncMock()
    _store: dict[str, Document] = _StrKeyDict()

    async def _create(doc: Document) -> Document:
        _store[doc.id] = doc
        return doc

    async def _get_by_id(doc_id: DocumentId) -> Document:
        if doc_id in _store:
            return _store[doc_id]
        raise ValueError(f"Document {doc_id} not found")

    async def _update(doc: Document) -> Document:
        _store[doc.id] = doc
        return doc

    async def _delete(doc_id: DocumentId) -> None:
        _store.pop(doc_id, None)

    async def _list_for_user(
        user_id: UserId,
        *,
        document_type: DocumentType | None = None,
        status: DocumentStatus | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        pagination=None,
    ) -> tuple[list[Document], int]:
        docs = [d for d in _store.values() if d.user_id == user_id]
        return docs, len(docs)

    repo.create.side_effect = _create
    repo.get_by_id.side_effect = _get_by_id
    repo.update.side_effect = _update
    repo.delete.side_effect = _delete
    repo.list_for_user.side_effect = _list_for_user
    repo._store = _store
    return repo


@pytest.fixture()
def check_result_repo() -> AsyncMock:
    repo = AsyncMock()
    _store: dict[str, list[CheckResult]] = _StrKeyDict()

    async def _replace(document_id: DocumentId, results) -> list[CheckResult]:
        saved = list(results)
        _store[document_id] = saved
        return saved

    async def _list_for_document(document_id: DocumentId) -> list[CheckResult]:
        return _store.get(document_id, [])

    repo.replace_for_document.side_effect = _replace
    repo.list_for_document.side_effect = _list_for_document
    return repo


@pytest.fixture()
def check_rule_repo() -> AsyncMock:
    repo = AsyncMock()
    _store: dict[str, CheckRule] = _StrKeyDict()

    async def _list(*, document_type: DocumentType | None = None, enabled: bool | None = None) -> list[CheckRule]:
        rules = list(_store.values())
        if document_type is not None:
            rules = [r for r in rules if r.document_type == document_type]
        if enabled is not None:
            rules = [r for r in rules if r.enabled == enabled]
        return rules

    async def _get_by_id(rule_id: CheckRuleId) -> CheckRule:
        if rule_id in _store:
            return _store[rule_id]
        raise ValueError(f"Rule {rule_id} not found")

    async def _update(rule: CheckRule) -> CheckRule:
        _store[rule.id] = rule
        return rule

    repo.list.side_effect = _list
    repo.get_by_id.side_effect = _get_by_id
    repo.update.side_effect = _update
    repo.upsert_many.return_value = None
    repo._store = _store
    return repo


@pytest.fixture()
def storage() -> AsyncMock:
    mock = AsyncMock()
    mock.upload_file.return_value = None
    mock.delete_file.return_value = None
    mock.file_exists.return_value = True

    def _download(key: str):
        async def _gen():
            yield FAKE_PDF

        return _gen()

    mock.download_file = _download
    return mock


@pytest.fixture()
def checker_engine() -> AsyncMock:
    engine = AsyncMock(spec=CheckerEngine)
    engine.run_checks.return_value = ([], 0)
    return engine


@pytest.fixture()
def validate_pdf() -> MagicMock:
    return MagicMock(return_value=ValidationResult(valid=True))


@pytest.fixture()
def app(
    doc_repo: AsyncMock,
    user_repo: AsyncMock,
    check_result_repo: AsyncMock,
    check_rule_repo: AsyncMock,
    storage: AsyncMock,
    checker_engine: AsyncMock,
    validate_pdf: MagicMock,
):
    from app.main import create_app

    doc_service = DocumentService(doc_repo, storage, check_rule_repo, validate_pdf)
    check_service = CheckService(doc_repo, check_result_repo, storage, checker_engine)
    auth_provider = DevAuthProvider(user_repo)
    user_service = UserService(auth_provider, user_repo)

    application = create_app()
    application.dependency_overrides[dependencies.get_upload_service] = lambda: doc_service
    application.dependency_overrides[dependencies.get_check_service] = lambda: check_service
    application.dependency_overrides[dependencies.get_query_service] = lambda: doc_service
    application.dependency_overrides[dependencies.get_rule_service] = lambda: doc_service
    application.dependency_overrides[dependencies.get_auth_service] = lambda: user_service
    return application


@pytest.fixture()
async def client(app) -> AsyncGenerator[httpx.AsyncClient]:
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture()
async def auth_client(app, test_user, user_repo) -> AsyncGenerator[httpx.AsyncClient]:
    user_repo._store[test_user.id] = test_user
    token = _make_token(test_user.id)
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
        cookies={"access_token": token},
    ) as c:
        yield c


@pytest.fixture()
async def admin_client(app, admin_user, user_repo) -> AsyncGenerator[httpx.AsyncClient]:
    user_repo._store[admin_user.id] = admin_user
    token = _make_token(admin_user.id)
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
        cookies={"access_token": token},
    ) as c:
        yield c
