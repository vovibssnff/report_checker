from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.checkers.base import BaseRule, rule
from app.checkers.plugins.common.pagination import check_arabic_numbers, check_page_number_position
from app.core.domain.value_objects import DocumentType, Severity

if TYPE_CHECKING:
    from app.checkers.base import RuleResult
    from app.checkers.pdf_parser import ParsedPDF


@rule(
    code="practice.pagination.arabic_numbers",
    name="Наличие нумерации страниц",
    document_type=DocumentType.PRACTICE_REPORT,
    severity=Severity.ERROR,
    description="Проверка наличия арабских номеров страниц",
    default_config={"skip_first_pages": 2},
)
class ArabicNumbersRule(BaseRule):
    async def check(self, pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
        return await check_arabic_numbers(pdf, config)


@rule(
    code="practice.pagination.position",
    name="Положение номеров страниц",
    document_type=DocumentType.PRACTICE_REPORT,
    severity=Severity.WARNING,
    description="Проверка расположения номеров страниц (внизу по центру)",
    default_config={"skip_first_pages": 2},
)
class PageNumberPositionRule(BaseRule):
    async def check(self, pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
        return await check_page_number_position(pdf, config)
