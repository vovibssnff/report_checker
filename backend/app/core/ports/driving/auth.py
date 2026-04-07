from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.domain.entities.user import User


class AuthUseCase(ABC):
    @abstractmethod
    async def get_login_url(self) -> str: ...

    @abstractmethod
    async def handle_oauth_callback(self, code: str, state: str) -> User: ...

    @abstractmethod
    async def dev_register(self, email: str, name: str, password: str, role: str) -> User: ...

    @abstractmethod
    async def dev_login(self, email: str, password: str) -> User: ...

    @abstractmethod
    async def get_current_user(self, token: str) -> User: ...
