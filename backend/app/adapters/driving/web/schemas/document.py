from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CheckResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    rule_code: str
    severity: str
    status: str
    message: str
    details: dict[str, Any] | None


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_type: str
    filename: str
    file_size: int
    status: str
    source: str
    uploaded_at: datetime
    checked_at: datetime | None


class DocumentDetailResponse(DocumentResponse):
    check_results: list[CheckResultResponse]
