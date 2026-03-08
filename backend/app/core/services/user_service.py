from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from app.core.domain.entities.user import User
from app.core.domain.value_objects import UserId, UserRole
from app.core.ports.driving.auth import AuthUseCase

if TYPE_CHECKING:
    from app.core.ports.driven.auth_provider import AuthProviderPort
    from app.core.ports.driven.user_repository import UserRepository


class UserService(AuthUseCase):
    def __init__(
        self,
        auth_provider: AuthProviderPort,
        user_repo: UserRepository,
    ) -> None:
        self._auth_provider = auth_provider
        self._user_repo = user_repo

    async def get_login_url(self) -> str:
        state = uuid.uuid4().hex
        return await self._auth_provider.get_login_url(state)

    async def handle_oauth_callback(self, code: str, state: str) -> User:
        token = await self._auth_provider.exchange_code(code)
        return await self._auth_provider.get_user_info(token)

    async def dev_login(self, email: str, name: str) -> User:
        existing = await self._user_repo.get_by_email(email)
        if existing is not None:
            return existing
        user = User(
            id=UserId(uuid.uuid4()),
            email=email,
            name=name,
            role=UserRole.STUDENT,
            itmo_id=None,
            created_at=datetime.now(UTC),
        )
        return await self._user_repo.create(user)

    async def get_current_user(self, token: str) -> User:
        return await self._auth_provider.get_user_info(token)
