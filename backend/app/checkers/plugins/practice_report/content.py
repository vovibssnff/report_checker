from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.checkers.base import BaseRule, RuleResult, rule
from app.core.domain.value_objects import CheckStatus, DocumentType, Severity

if TYPE_CHECKING:
    from app.checkers.pdf_parser import ParsedPDF


@rule(
    code="practice.content.min_pages",
    name="Минимальное количество страниц",
    document_type=DocumentType.PRACTICE_REPORT,
    severity=Severity.WARNING,
    description="Проверка минимального количества страниц отчёта",
    default_config={"min_pages": 10},
)
class MinPagesRule(BaseRule):
    async def check(self, pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
        min_pages = config.get("min_pages", 10)

        if pdf.page_count < min_pages:
            return [
                RuleResult(
                    status=CheckStatus.FAILED,
                    message="min_pages_insufficient",
                    details={"page_count": pdf.page_count, "min_pages": min_pages},
                )
            ]
        return [
            RuleResult(
                status=CheckStatus.PASSED,
                message="min_pages_ok",
                details={"page_count": pdf.page_count},
            )
        ]
