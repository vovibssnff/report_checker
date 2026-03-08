from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING
from uuid import uuid4

from jose import jwt

from app.config import settings
from app.core.domain.entities.user import User
from app.core.domain.value_objects import UserId, UserRole
from app.core.ports.driven.auth_provider import AuthProviderPort

if TYPE_CHECKING:
    from app.core.ports.driven.user_repository import UserRepository


class DevAuthProvider(AuthProviderPort):
    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    async def get_login_url(self, state: str) -> str:
        return "/api/v1/auth/dev/login"

    async def exchange_code(self, code: str) -> str:
        return code

    async def get_user_info(self, token: str) -> User:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id = UserId(payload["sub"])
        return await self._user_repo.get_by_id(user_id)

    async def login(self, email: str, name: str) -> tuple[User, str]:
        user = await self._user_repo.get_by_email(email)
        if user is None:
            user = User(
                id=UserId(uuid4()),
                email=email,
                name=name,
                role=UserRole.STUDENT,
                itmo_id=None,
                created_at=datetime.now(UTC),
            )
            user = await self._user_repo.create(user)

        token = self._create_token(user)
        return user, token

    def _create_token(self, user: User) -> str:
        expire = datetime.now(UTC) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value,
            "exp": expire,
        }
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
