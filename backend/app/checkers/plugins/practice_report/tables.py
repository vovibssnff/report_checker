from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.checkers.base import BaseRule, rule
from app.checkers.plugins.common.tables import check_table_caption_format, check_table_numbering
from app.core.domain.value_objects import DocumentType, Severity

if TYPE_CHECKING:
    from app.checkers.base import RuleResult
    from app.checkers.pdf_parser import ParsedPDF


@rule(
    code="practice.tables.caption_format",
    name="Формат подписей таблиц",
    document_type=DocumentType.PRACTICE_REPORT,
    severity=Severity.ERROR,
    description="Проверка формата подписей таблиц",
)
class TableCaptionFormatRule(BaseRule):
    async def check(self, pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
        return await check_table_caption_format(pdf, config)


@rule(
    code="practice.tables.numbering",
    name="Нумерация таблиц",
    document_type=DocumentType.PRACTICE_REPORT,
    severity=Severity.WARNING,
    description="Проверка последовательной нумерации таблиц",
)
class TableNumberingRule(BaseRule):
    async def check(self, pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
        return await check_table_numbering(pdf, config)
