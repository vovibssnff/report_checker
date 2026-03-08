from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from urllib.parse import urlencode
from uuid import uuid4

import httpx

from app.config import settings
from app.core.domain.entities.user import User
from app.core.domain.value_objects import UserId, UserRole
from app.core.ports.driven.auth_provider import AuthProviderPort

if TYPE_CHECKING:
    from app.core.ports.driven.user_repository import UserRepository

_TOKEN_URL = "https://id.itmo.ru/auth/realms/itmo/protocol/openid-connect/token"
_USERINFO_URL = "https://id.itmo.ru/auth/realms/itmo/protocol/openid-connect/userinfo"
_AUTH_URL = "https://id.itmo.ru/auth/realms/itmo/protocol/openid-connect/auth"


class ItmoIdAuthProvider(AuthProviderPort):
    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    async def get_login_url(self, state: str) -> str:
        params = {
            "client_id": settings.ITMO_ID_CLIENT_ID,
            "redirect_uri": settings.ITMO_ID_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid profile email",
            "state": state,
        }
        return f"{_AUTH_URL}?{urlencode(params)}"

    async def exchange_code(self, code: str) -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                _TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "client_id": settings.ITMO_ID_CLIENT_ID,
                    "client_secret": settings.ITMO_ID_CLIENT_SECRET,
                    "redirect_uri": settings.ITMO_ID_REDIRECT_URI,
                },
            )
            resp.raise_for_status()
            return resp.json()["access_token"]

    async def get_user_info(self, token: str) -> User:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                _USERINFO_URL,
                headers={"Authorization": f"Bearer {token}"},
            )
            resp.raise_for_status()
            info = resp.json()

        itmo_id = info.get("sub", "")
        email = info.get("email", "")
        name = info.get("name", info.get("preferred_username", ""))

        existing = await self._user_repo.get_by_itmo_id(itmo_id)
        if existing is not None:
            return existing

        user = User(
            id=UserId(uuid4()),
            email=email,
            name=name,
            role=UserRole.STUDENT,
            itmo_id=itmo_id,
            created_at=datetime.now(UTC),
        )
        return await self._user_repo.create(user)
