from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.adapters.driven.auth.dev_auth_provider import DevAuthProvider
from app.adapters.driven.auth.itmo_id_provider import ItmoIdAuthProvider
from app.adapters.driven.observability import configure_logging, get_logger, kv
from app.adapters.driven.persistence.database.session import async_session_factory, get_db_session
from app.adapters.driven.persistence.repositories.check_result_repository import PgCheckResultRepository
from app.adapters.driven.persistence.repositories.check_rule_repository import PgCheckRuleRepository
from app.adapters.driven.persistence.repositories.document_repository import PgDocumentRepository
from app.adapters.driven.persistence.repositories.user_repository import PgUserRepository
from app.adapters.driven.security.pdf_validator import PDFValidator
from app.adapters.driven.storage.s3_storage import S3Storage
from app.adapters.driving.internal.router import router as internal_router
from app.adapters.driving.web.middleware import RequestLoggingMiddleware
from app.adapters.driving.web.v1.router import api_router
from app.checkers.registry import RuleRegistry
from app.config import settings

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from sqlalchemy.ext.asyncio import AsyncSession

    from app.core.ports.driven.auth_provider import AuthProviderPort


def _build_services(app: FastAPI) -> None:
    storage = S3Storage()
    pdf_validator = PDFValidator()

    registry = RuleRegistry.instance()
    registry.discover_plugins()

    async def get_upload_service(
        session: AsyncSession = Depends(get_db_session),
    ):
        from app.core.services.document_service import DocumentService

        doc_repo = PgDocumentRepository(session)
        rule_repo = PgCheckRuleRepository(session)
        yield DocumentService(doc_repo, storage, rule_repo, pdf_validator.validate)

    async def get_check_service(
        session: AsyncSession = Depends(get_db_session),
    ):
        from app.checkers.engine import CheckerEngine
        from app.core.services.check_service import CheckService

        doc_repo = PgDocumentRepository(session)
        result_repo = PgCheckResultRepository(session)
        rule_repo = PgCheckRuleRepository(session)
        engine = CheckerEngine(registry, rule_repo)
        yield CheckService(doc_repo, result_repo, storage, engine)

    async def get_query_service(
        session: AsyncSession = Depends(get_db_session),
    ):
        from app.core.services.document_service import DocumentService

        doc_repo = PgDocumentRepository(session)
        rule_repo = PgCheckRuleRepository(session)
        yield DocumentService(doc_repo, storage, rule_repo, pdf_validator.validate)

    async def get_rule_service(
        session: AsyncSession = Depends(get_db_session),
    ):
        from app.core.services.document_service import DocumentService

        doc_repo = PgDocumentRepository(session)
        rule_repo = PgCheckRuleRepository(session)
        yield DocumentService(doc_repo, storage, rule_repo, pdf_validator.validate)

    async def get_auth_service(
        session: AsyncSession = Depends(get_db_session),
    ):
        from app.core.services.user_service import UserService

        user_repo = PgUserRepository(session)
        auth_provider: AuthProviderPort
        auth_provider = ItmoIdAuthProvider(user_repo) if settings.AUTH_MODE == "itmo_id" else DevAuthProvider(user_repo)
        yield UserService(auth_provider, user_repo)

    from app.adapters.driving.web import dependencies

    app.dependency_overrides[dependencies.get_upload_service] = get_upload_service
    app.dependency_overrides[dependencies.get_check_service] = get_check_service
    app.dependency_overrides[dependencies.get_query_service] = get_query_service
    app.dependency_overrides[dependencies.get_rule_service] = get_rule_service
    app.dependency_overrides[dependencies.get_auth_service] = get_auth_service


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    _build_services(app)
    registry = RuleRegistry.instance()
    async with async_session_factory() as session:
        rule_repo = PgCheckRuleRepository(session)
        await rule_repo.sync_from_registry(registry)
        await session.commit()
    yield


@asynccontextmanager
async def _noop_lifespan(app: FastAPI) -> AsyncGenerator[None]:
    yield


def create_app(*, use_default_services: bool = True) -> FastAPI:
    configure_logging(settings.LOG_LEVEL)
    logger = get_logger(__name__)

    app = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        lifespan=lifespan if use_default_services else _noop_lifespan,
    )

    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        # nosemgrep: python.fastapi.security.wildcard-cors.wildcard-cors
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api/v1")
    app.include_router(internal_router, prefix="/internal")

    @app.exception_handler(HTTPException)
    async def on_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
        logger.warning(
            "http_exception %s",
            kv(path=request.url.path, method=request.method, status_code=exc.status_code, detail=exc.detail),
        )
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(Exception)
    async def on_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "unhandled_exception %s",
            kv(path=request.url.path, method=request.method, error_type=type(exc).__name__),
        )
        return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
