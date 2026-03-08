from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    document_type: str
    name: str
    description: str
    enabled: bool
    config: dict[str, Any] | None


class RuleUpdateRequest(BaseModel):
    enabled: bool | None = None
    config: dict[str, Any] | None = None
