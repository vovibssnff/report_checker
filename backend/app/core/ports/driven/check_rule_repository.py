from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    from app.core.domain.entities.check_rule import CheckRule
    from app.core.domain.value_objects import CheckRuleId, DocumentType


class CheckRuleRepository(ABC):
    @abstractmethod
    async def list(
        self,
        *,
        document_type: DocumentType | None = None,
        enabled: bool | None = None,
    ) -> list[CheckRule]: ...

    @abstractmethod
    async def get_by_id(self, rule_id: CheckRuleId) -> CheckRule: ...

    @abstractmethod
    async def upsert_many(self, rules: Iterable[CheckRule]) -> None:
        """
        Upsert rules by code/document_type so DB stays in sync with plugin registry.
        """

    @abstractmethod
    async def update(self, rule: CheckRule) -> CheckRule: ...
