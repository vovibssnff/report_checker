from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.domain.entities.check_rule import CheckRule
    from app.core.domain.value_objects import CheckRuleId, DocumentType


class RuleManagementUseCase(ABC):
    @abstractmethod
    async def list_rules(
        self,
        *,
        document_type: DocumentType | None = None,
        enabled: bool | None = None,
    ) -> list[CheckRule]: ...

    @abstractmethod
    async def update_rule(
        self,
        rule_id: CheckRuleId,
        *,
        enabled: bool | None = None,
        config: dict | None = None,
    ) -> CheckRule: ...
