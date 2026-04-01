from __future__ import annotations

from time import perf_counter
from typing import TYPE_CHECKING
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware

from app.adapters.driven.observability import get_logger, kv
from app.adapters.driving.web.request_context import reset_request_id, set_request_id

if TYPE_CHECKING:
    from fastapi import Request

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        token = set_request_id(request_id)
        started = perf_counter()
        client_ip = request.client.host if request.client else None

        logger.info(
            "request_started %s",
            kv(method=request.method, path=request.url.path, client_ip=client_ip),
        )

        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = round((perf_counter() - started) * 1000, 2)
            logger.exception(
                "request_failed %s",
                kv(method=request.method, path=request.url.path, duration_ms=elapsed_ms),
            )
            reset_request_id(token)
            raise

        elapsed_ms = round((perf_counter() - started) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request_completed %s",
            kv(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=elapsed_ms,
            ),
        )
        reset_request_id(token)
        return response
