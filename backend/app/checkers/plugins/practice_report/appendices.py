from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.checkers.base import BaseRule, rule
from app.checkers.plugins.common.appendices import check_appendix_labeling
from app.core.domain.value_objects import DocumentType, Severity

if TYPE_CHECKING:
    from app.checkers.base import RuleResult
    from app.checkers.pdf_parser import ParsedPDF


@rule(
    code="practice.appendices.labeling",
    name="Обозначение приложений",
    document_type=DocumentType.PRACTICE_REPORT,
    severity=Severity.WARNING,
    description="Проверка обозначения приложений буквами",
)
class AppendixLabelingRule(BaseRule):
    async def check(self, pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
        return await check_appendix_labeling(pdf, config)
