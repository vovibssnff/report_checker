from __future__ import annotations

import io
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import httpx
import pikepdf
import pytest
from fastapi import Depends
from httpx import ASGITransport
from jose import jwt
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from testcontainers.minio import MinioContainer
from testcontainers.postgres import PostgresContainer

from app.adapters.driven.persistence.database import session as db_session
from app.adapters.driven.persistence.database.models import Base
from app.adapters.driven.persistence.database.models.user import UserModel
from app.adapters.driven.persistence.repositories.check_result_repository import (
    PgCheckResultRepository,
)
from app.adapters.driven.persistence.repositories.check_rule_repository import (
    PgCheckRuleRepository,
)
from app.adapters.driven.persistence.repositories.document_repository import (
    PgDocumentRepository,
)
from app.adapters.driven.persistence.repositories.user_repository import PgUserRepository
from app.adapters.driven.storage.s3_storage import S3Storage
from app.adapters.driving.web import dependencies
from app.checkers.engine import CheckerEngine
from app.checkers.registry import RuleRegistry
from app.config import settings
from app.core.domain.entities.user import User
from app.core.domain.value_objects import UserId, UserRole
from app.core.services.check_service import CheckService
from app.core.services.document_service import DocumentService, ValidationResult
from app.core.services.user_service import UserService

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


def make_minimal_pdf() -> bytes:
    pdf = pikepdf.Pdf.new()
    pdf.add_blank_page(page_size=(612, 792))
    buf = io.BytesIO()
    pdf.save(buf)
    return buf.getvalue()


INTEGRATION_PDF = make_minimal_pdf()


@pytest.fixture(scope="session")
def postgres_url() -> str:
    with PostgresContainer("postgres:16-alpine", driver="asyncpg") as pg:
        yield pg.get_connection_url()


@pytest.fixture(scope="session")
def minio_container():
    with MinioContainer() as minio:
        yield minio


@pytest.fixture(scope="session")
def s3_config(minio_container) -> dict[str, str]:
    client = minio_container.get_client()
    bucket = "test-documents"
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
    host = minio_container.get_config()["endpoint"]
    return {
        "endpoint_url": f"http://{host}",
        "access_key": minio_container.access_key,
        "secret_key": minio_container.secret_key,
        "bucket_name": bucket,
        "region": "us-east-1",
    }


@pytest.fixture()
def engine(postgres_url: str) -> AsyncEngine:
    """Function-scoped so the engine is used in the same event loop as the test."""
    return create_async_engine(postgres_url, echo=False)


@pytest.fixture(autouse=True)
async def _create_tables(engine: AsyncEngine) -> AsyncGenerator[None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture()
def session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture()
async def session(session_factory) -> AsyncGenerator[AsyncSession]:
    async with session_factory() as s:
        yield s
        await s.rollback()


@pytest.fixture()
def s3_storage(s3_config: dict[str, str]) -> S3Storage:
    return S3Storage(**s3_config)


@pytest.fixture()
def doc_repo(session: AsyncSession) -> PgDocumentRepository:
    return PgDocumentRepository(session)


@pytest.fixture()
def user_repo(session: AsyncSession) -> PgUserRepository:
    return PgUserRepository(session)


@pytest.fixture()
def check_result_repo(session: AsyncSession) -> PgCheckResultRepository:
    return PgCheckResultRepository(session)


@pytest.fixture()
def check_rule_repo(session: AsyncSession) -> PgCheckRuleRepository:
    return PgCheckRuleRepository(session)


@pytest.fixture()
async def test_user(session: AsyncSession) -> User:
    uid = UserId(uuid.uuid4())
    model = UserModel(
        id=uid,
        email=f"integ-{uuid.uuid4().hex[:8]}@test.com",
        name="Integration User",
        role="student",
        itmo_id=None,
        created_at=datetime.now(UTC),
    )
    session.add(model)
    await session.flush()
    await session.commit()
    return User(
        id=uid,
        email=model.email,
        name=model.name,
        role=UserRole.STUDENT,
        itmo_id=None,
        created_at=model.created_at,
    )


def _validate_pdf_ok(data: bytes) -> ValidationResult:
    return ValidationResult(valid=True)


@pytest.fixture()
async def integration_app(session_factory, s3_config: dict[str, str]):
    from app.adapters.driven.auth.dev_auth_provider import DevAuthProvider
    from app.main import create_app

    RuleRegistry.instance().discover_plugins()
    async with session_factory() as sync_sess:
        rr = PgCheckRuleRepository(sync_sess)
        await rr.sync_from_registry(RuleRegistry.instance())
        await sync_sess.commit()

    application = create_app(use_default_services=False)

    async def get_test_db_session():
        async with session_factory() as sess:
            try:
                yield sess
                await sess.commit()
            except Exception:
                await sess.rollback()
                raise

    async def _make_upload(sess: AsyncSession = Depends(db_session.get_db_session)):
        dr = PgDocumentRepository(sess)
        rr = PgCheckRuleRepository(sess)
        storage = S3Storage(**s3_config)
        yield DocumentService(dr, storage, rr, _validate_pdf_ok)

    async def _make_check(sess: AsyncSession = Depends(db_session.get_db_session)):
        dr = PgDocumentRepository(sess)
        cr = PgCheckResultRepository(sess)
        rr = PgCheckRuleRepository(sess)
        storage = S3Storage(**s3_config)
        registry = RuleRegistry.instance()
        engine = CheckerEngine(registry, rr)
        yield CheckService(dr, cr, storage, engine)

    async def _make_auth():
        async with session_factory() as sess:
            ur = PgUserRepository(sess)
            auth_provider = DevAuthProvider(ur)
            yield UserService(auth_provider, ur)

    application.dependency_overrides[db_session.get_db_session] = get_test_db_session
    application.dependency_overrides[dependencies.get_upload_service] = _make_upload
    application.dependency_overrides[dependencies.get_check_service] = _make_check
    application.dependency_overrides[dependencies.get_query_service] = _make_upload
    application.dependency_overrides[dependencies.get_rule_service] = _make_upload
    application.dependency_overrides[dependencies.get_auth_service] = _make_auth
    return application


@pytest.fixture()
async def integration_client(
    integration_app,
) -> AsyncGenerator[httpx.AsyncClient]:
    transport = ASGITransport(app=integration_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture()
async def auth_integration_client(integration_app, test_user) -> AsyncGenerator[httpx.AsyncClient]:
    token = jwt.encode(
        {"sub": str(test_user.id)},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    transport = ASGITransport(app=integration_app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
        cookies={"access_token": token},
    ) as c:
        yield c
