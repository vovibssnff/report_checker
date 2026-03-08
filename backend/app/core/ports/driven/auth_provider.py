from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.domain.entities.user import User


class AuthProviderPort(ABC):
    @abstractmethod
    async def get_login_url(self, state: str) -> str: ...

    @abstractmethod
    async def exchange_code(self, code: str) -> str:
        """
        Exchange an OAuth2 authorization code for an access token.
        Returns the raw access token string.
        """

    @abstractmethod
    async def get_user_info(self, token: str) -> User:
        """
        Map an external identity (e.g. itmo.id) to an internal User,
        creating it if necessary.
        """
