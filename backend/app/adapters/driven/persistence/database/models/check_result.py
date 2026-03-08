from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, Uuid
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.adapters.driven.persistence.database.models.base import Base, UUIDPrimaryKeyMixin


class CheckResultModel(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "check_results"

    document_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    rule_code: Mapped[str] = mapped_column(String, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    message: Mapped[str] = mapped_column(String, nullable=False)
    details: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
