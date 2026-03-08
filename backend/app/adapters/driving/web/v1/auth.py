from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Response
from fastapi.responses import RedirectResponse
from starlette import status

from app.adapters.driving.web.dependencies import get_auth_service, get_current_user
from app.adapters.driving.web.schemas.auth import DevLoginRequest, UserResponse

if TYPE_CHECKING:
    from app.core.domain.entities.user import User
    from app.core.ports.driving.auth import AuthUseCase

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
async def login(
    auth_service: AuthUseCase = Depends(get_auth_service),
) -> dict[str, str]:
    url = await auth_service.get_login_url()
    return {"redirect_url": url}


@router.get("/callback")
async def callback(
    code: str,
    state: str,
    auth_service: AuthUseCase = Depends(get_auth_service),
) -> RedirectResponse:
    user = await auth_service.handle_oauth_callback(code, state)
    from jose import jwt

    from app.config import settings

    token = jwt.encode({"sub": str(user.id)}, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.set_cookie("access_token", token, httponly=True)
    return response


@router.post("/dev/login", response_model=UserResponse)
async def dev_login(
    body: DevLoginRequest,
    auth_service: AuthUseCase = Depends(get_auth_service),
) -> UserResponse:
    user = await auth_service.dev_login(body.email, body.name)
    from jose import jwt

    from app.config import settings

    token = jwt.encode({"sub": str(user.id)}, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    response = Response(
        content=UserResponse.model_validate(user, from_attributes=True).model_dump_json(),
        media_type="application/json",
        status_code=status.HTTP_200_OK,
    )
    response.set_cookie("access_token", token, httponly=True)
    return response  # type: ignore[return-value]


@router.get("/me", response_model=UserResponse)
async def me(
    user: User = Depends(get_current_user),
) -> UserResponse:
    return UserResponse.model_validate(user, from_attributes=True)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout() -> Response:
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie("access_token")
    return response
