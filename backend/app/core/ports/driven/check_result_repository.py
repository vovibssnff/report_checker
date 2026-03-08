from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    from app.core.domain.entities.check_result import CheckResult
    from app.core.domain.value_objects import CheckResultId, DocumentId


class CheckResultRepository(ABC):
    @abstractmethod
    async def replace_for_document(
        self,
        document_id: DocumentId,
        results: Iterable[CheckResult],
    ) -> list[CheckResult]:
        """Replace all existing results for the given document."""

    @abstractmethod
    async def list_for_document(self, document_id: DocumentId) -> list[CheckResult]: ...

    @abstractmethod
    async def get_by_id(self, result_id: CheckResultId) -> CheckResult: ...
