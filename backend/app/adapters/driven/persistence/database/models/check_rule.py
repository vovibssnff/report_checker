from __future__ import annotations

from typing import Any

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.adapters.driven.persistence.database.models.base import Base, UUIDPrimaryKeyMixin


class CheckRuleModel(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "check_rules"

    code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    document_type: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    config: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
