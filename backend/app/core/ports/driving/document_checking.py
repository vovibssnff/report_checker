from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.domain.entities.check_result import CheckResult
    from app.core.domain.value_objects import DocumentId


class DocumentCheckUseCase(ABC):
    @abstractmethod
    async def run_checks_for_document(self, document_id: DocumentId) -> list[CheckResult]:
        """Run all enabled checks for the given document."""

    @abstractmethod
    async def get_results_for_document(self, document_id: DocumentId) -> list[CheckResult]:
        """Return previously stored check results for a document."""
