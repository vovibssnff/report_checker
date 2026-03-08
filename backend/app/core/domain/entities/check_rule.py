from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.core.domain.value_objects import CheckRuleId, DocumentType


@dataclass
class CheckRule:
    id: CheckRuleId
    code: str
    document_type: DocumentType
    name: str
    description: str
    enabled: bool
    config: dict[str, Any] | None
