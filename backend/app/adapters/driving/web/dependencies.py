from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt

from app.config import settings

if TYPE_CHECKING:
    from app.core.domain.entities.user import User
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


async def get_current_user(
    request: Request,
    auth_service: AuthUseCase = Depends(get_auth_service),
) -> User:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except JWTError as err:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from err
    return await auth_service.get_current_user(token)


async def require_admin(
    user: User = Depends(get_current_user),
) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user
