from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt

from app.adapters.driven.observability import get_logger, kv
from app.config import settings
from app.core.domain.value_objects import UserId, UserRole

if TYPE_CHECKING:
    from app.core.domain.entities.user import User
    from app.core.ports.driven.user_repository import UserRepository
    from app.core.ports.driving.auth import AuthUseCase
    from app.core.ports.driving.document_checking import DocumentCheckUseCase
    from app.core.ports.driving.document_querying import DocumentQueryUseCase
    from app.core.ports.driving.document_uploading import DocumentUploadUseCase
    from app.core.ports.driving.rule_managing import RuleManagementUseCase


def get_upload_service() -> DocumentUploadUseCase:
    raise NotImplementedError


def get_check_service() -> DocumentCheckUseCase:
    raise NotImplementedError


def get_query_service() -> DocumentQueryUseCase:
    raise NotImplementedError


def get_rule_service() -> RuleManagementUseCase:
    raise NotImplementedError


def get_auth_service() -> AuthUseCase:
    raise NotImplementedError


def get_user_repo() -> UserRepository:
    raise NotImplementedError


async def get_current_user(
    request: Request,
    user_repo: UserRepository = Depends(get_user_repo),
) -> User:
    logger = get_logger(__name__)
    token = request.cookies.get("access_token")
    if not token:
        logger.info("auth_missing_cookie %s", kv(path=request.url.path))
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except JWTError as err:
        logger.warning("auth_jwt_decode_failed %s", kv(path=request.url.path))
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from err
    try:
        return await user_repo.get_by_id(UserId(UUID(user_id)))
    except ValueError as err:
        # Stale/invalid token subject should be treated as unauthenticated, not 500.
        logger.warning("auth_user_not_found %s", kv(path=request.url.path))
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found") from err


async def require_admin(
    user: User = Depends(get_current_user),
) -> User:
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


def require_role(*roles: UserRole):
    async def _require(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user

    return _require
