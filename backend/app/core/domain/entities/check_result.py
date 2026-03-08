from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from datetime import datetime

    from app.core.domain.value_objects import CheckResultId, CheckStatus, DocumentId, Severity


@dataclass
class CheckResult:
    id: CheckResultId
    document_id: DocumentId
    rule_code: str
    severity: Severity
    status: CheckStatus
    message: str
    details: dict[str, Any] | None
    created_at: datetime
