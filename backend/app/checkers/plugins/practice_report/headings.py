from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.checkers.base import BaseRule, rule
from app.checkers.plugins.common.headings import check_new_page, check_section_numbering, check_structural_elements
from app.core.domain.value_objects import DocumentType, Severity

if TYPE_CHECKING:
    from app.checkers.base import RuleResult
    from app.checkers.pdf_parser import ParsedPDF


@rule(
    code="practice.headings.structural_elements",
    name="Оформление структурных элементов",
    document_type=DocumentType.PRACTICE_REPORT,
    severity=Severity.ERROR,
    description="Проверка центрирования и верхнего регистра структурных элементов",
)
class StructuralElementsRule(BaseRule):
    async def check(self, pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
        return await check_structural_elements(pdf, config)


@rule(
    code="practice.headings.new_page",
    name="Начало разделов с новой страницы",
    document_type=DocumentType.PRACTICE_REPORT,
    severity=Severity.ERROR,
    description="Проверка что структурные элементы и главы начинаются с новой страницы",
)
class NewPageRule(BaseRule):
    async def check(self, pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
        return await check_new_page(pdf, config)


@rule(
    code="practice.headings.section_numbering",
    name="Нумерация разделов",
    document_type=DocumentType.PRACTICE_REPORT,
    severity=Severity.WARNING,
    description="Проверка иерархической нумерации (1, 1.1, 1.1.1)",
)
class SectionNumberingRule(BaseRule):
    async def check(self, pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
        return await check_section_numbering(pdf, config)
