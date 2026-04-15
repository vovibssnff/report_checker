from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import RedirectResponse
from jose import jwt
from starlette import status

from app.adapters.driving.web.dependencies import get_auth_service, get_current_user
from app.adapters.driving.web.schemas.auth import DevLoginRequest, DevRegisterRequest, UserResponse
from app.config import settings

if TYPE_CHECKING:
    from app.core.domain.entities.user import User
    from app.core.ports.driving.auth import AuthUseCase

router = APIRouter(prefix="/auth", tags=["auth"])


def _create_session_token(user_id: str) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": user_id, "exp": expire},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def _set_access_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        "access_token",
        token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=settings.JWT_EXPIRE_MINUTES * 60,
    )


@router.get("/login")
async def login(
    auth_service: AuthUseCase = Depends(get_auth_service),
) -> dict[str, str]:
    url = await auth_service.get_login_url()
    return {"redirect_url": url}


@router.get("/mode")
async def auth_mode() -> dict[str, str]:
    return {"mode": settings.AUTH_MODE}


@router.get("/callback")
async def callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
    auth_service: AuthUseCase = Depends(get_auth_service),
) -> RedirectResponse:
    if error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"OAuth error: {error} — {error_description or 'unknown'}",
        )
    if not code or not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing code or state parameter",
        )
    user = await auth_service.handle_oauth_callback(code, state)
    token = _create_session_token(str(user.id))
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    _set_access_cookie(response, token)
    return response


@router.post("/dev/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def dev_register(
    body: DevRegisterRequest,
    auth_service: AuthUseCase = Depends(get_auth_service),
) -> UserResponse:
    if settings.AUTH_MODE != "dev":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    try:
        user = await auth_service.dev_register(body.email, body.name, body.password, body.role)
    except ValueError as err:
        message = str(err)
        if message == "User with this email already exists":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=message) from err
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message) from err
    token = _create_session_token(str(user.id))
    response = Response(
        content=UserResponse.model_validate(user, from_attributes=True).model_dump_json(),
        media_type="application/json",
        status_code=status.HTTP_201_CREATED,
    )
    _set_access_cookie(response, token)
    return response  # type: ignore[return-value]


@router.post("/dev/login", response_model=UserResponse)
async def dev_login(
    body: DevLoginRequest,
    auth_service: AuthUseCase = Depends(get_auth_service),
) -> UserResponse:
    if settings.AUTH_MODE != "dev":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    try:
        user = await auth_service.dev_login(body.email, body.password)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(err)) from err
    token = _create_session_token(str(user.id))
    response = Response(
        content=UserResponse.model_validate(user, from_attributes=True).model_dump_json(),
        media_type="application/json",
        status_code=status.HTTP_200_OK,
    )
    _set_access_cookie(response, token)
    return response  # type: ignore[return-value]


@router.get("/me", response_model=UserResponse)
async def me(
    user: User = Depends(get_current_user),
) -> UserResponse:
    return UserResponse.model_validate(user, from_attributes=True)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout() -> Response:
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie("access_token", secure=True, samesite="lax")
    return response
