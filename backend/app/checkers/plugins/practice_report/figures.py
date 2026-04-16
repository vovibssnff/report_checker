from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.checkers.base import BaseRule, rule
from app.checkers.plugins.common.figures import check_figure_caption_format, check_figure_numbering
from app.core.domain.value_objects import DocumentType, Severity

if TYPE_CHECKING:
    from app.checkers.base import RuleResult
    from app.checkers.pdf_parser import ParsedPDF


@rule(
    code="practice.figures.caption_format",
    name="Формат подписей рисунков",
    document_type=DocumentType.PRACTICE_REPORT,
    severity=Severity.ERROR,
    description="Проверка формата подписей рисунков",
)
class FigureCaptionFormatRule(BaseRule):
    async def check(self, pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
        return await check_figure_caption_format(pdf, config)


@rule(
    code="practice.figures.numbering",
    name="Нумерация рисунков",
    document_type=DocumentType.PRACTICE_REPORT,
    severity=Severity.WARNING,
    description="Проверка последовательной нумерации рисунков",
)
class FigureNumberingRule(BaseRule):
    async def check(self, pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
        return await check_figure_numbering(pdf, config)
