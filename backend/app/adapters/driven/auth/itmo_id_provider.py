from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from urllib.parse import urlencode
from uuid import uuid4

import httpx

from app.adapters.driven.observability import get_logger, kv
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
        self._last_refresh_token: str | None = None

    async def get_login_url(self, state: str) -> str:
        params = {
            "client_id": settings.ITMO_ID_CLIENT_ID,
            "redirect_uri": settings.ITMO_ID_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid profile email edu work",
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
            token_data = resp.json()
            self._last_refresh_token = token_data.get("refresh_token")
            return token_data["access_token"]

    @staticmethod
    def _has_non_empty_claim(info: dict, claim_name: str) -> bool:
        value = info.get(claim_name)
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip())
        if isinstance(value, list):
            return len(value) > 0
        if isinstance(value, dict):
            return len(value) > 0
        return bool(value)

    def _detect_role(self, info: dict) -> UserRole:
        work_claim_names = (
            "work",
            "workplaces",
            "positions",
            "employment",
            "employee",
            "staff",
        )
        edu_claim_names = (
            "edu",
            "education",
            "student",
            "students",
            "study",
            "group",
        )
        if any(self._has_non_empty_claim(info, name) for name in work_claim_names):
            return UserRole.TEACHER
        if any(self._has_non_empty_claim(info, name) for name in edu_claim_names):
            return UserRole.STUDENT
        return UserRole.STUDENT

    async def get_user_info(self, token: str) -> User:
        logger = get_logger(__name__)
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                _USERINFO_URL,
                headers={"Authorization": f"Bearer {token}"},
            )
            resp.raise_for_status()
            info = resp.json()
        logger.debug("itmo_userinfo_received %s", kv(claims=info))

        itmo_id = info.get("sub", "")
        email = info.get("email", "")
        name = info.get("name", info.get("preferred_username", ""))
        role = self._detect_role(info)

        existing = await self._user_repo.get_by_itmo_id(itmo_id)
        if existing is None and email:
            existing = await self._user_repo.get_by_email(email)

        if existing is not None:
            if (
                existing.name != name
                or existing.email != email
                or existing.role != role
                or existing.itmo_id != itmo_id
                or existing.itmo_refresh_token != self._last_refresh_token
            ):
                updated = User(
                    id=existing.id,
                    email=email or existing.email,
                    name=name or existing.name,
                    role=role,
                    itmo_id=itmo_id or existing.itmo_id,
                    created_at=existing.created_at,
                    password_hash=existing.password_hash,
                    itmo_refresh_token=self._last_refresh_token,
                )
                return await self._user_repo.update(updated)
            return existing

        user = User(
            id=UserId(uuid4()),
            email=email,
            name=name,
            role=role,
            itmo_id=itmo_id,
            created_at=datetime.now(UTC),
            itmo_refresh_token=self._last_refresh_token,
        )
        return await self._user_repo.create(user)
