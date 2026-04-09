from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime

    from app.core.domain.value_objects import UserId, UserRole


@dataclass
class User:
    id: UserId
    email: str
    name: str
    role: UserRole
    itmo_id: str | None
    created_at: datetime
    password_hash: str | None = None
    itmo_refresh_token: str | None = None
