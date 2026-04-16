from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.checkers.base import BaseRule, rule
from app.checkers.plugins.common.formatting import (
    check_alignment,
    check_font,
    check_line_spacing,
    check_margins,
    check_page_size,
    check_paragraph_indent,
)
from app.core.domain.value_objects import DocumentType, Severity

if TYPE_CHECKING:
    from app.checkers.base import RuleResult
    from app.checkers.pdf_parser import ParsedPDF


@rule(
    code="practice.formatting.page_size",
    name="Формат страницы А4",
    document_type=DocumentType.PRACTICE_REPORT,
    severity=Severity.ERROR,
    description="Проверка формата страницы (А4)",
    default_config={"tolerance_mm": 5},
)
class PageSizeRule(BaseRule):
    async def check(self, pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
        return await check_page_size(pdf, config)


@rule(
    code="practice.formatting.margins",
    name="Поля страницы",
    document_type=DocumentType.PRACTICE_REPORT,
    severity=Severity.ERROR,
    description="Проверка размеров полей",
    default_config={"left_mm": 30, "right_mm": 15, "top_mm": 20, "bottom_mm": 20, "tolerance_mm": 5},
)
class MarginsRule(BaseRule):
    async def check(self, pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
        return await check_margins(pdf, config)


@rule(
    code="practice.formatting.font",
    name="Шрифт основного текста",
    document_type=DocumentType.PRACTICE_REPORT,
    severity=Severity.ERROR,
    description="Проверка основного шрифта (Times New Roman, черный, без bold в основном тексте)",
    default_config={"expected_font": "Times", "min_size": 12},
)
class FontRule(BaseRule):
    async def check(self, pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
        return await check_font(pdf, config)


@rule(
    code="practice.formatting.line_spacing",
    name="Межстрочный интервал",
    document_type=DocumentType.PRACTICE_REPORT,
    severity=Severity.WARNING,
    description="Проверка межстрочного интервала (1.5)",
    default_config={"expected_spacing": 1.5, "tolerance": 0.3},
)
class LineSpacingRule(BaseRule):
    async def check(self, pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
        return await check_line_spacing(pdf, config)


@rule(
    code="practice.formatting.paragraph_indent",
    name="Абзацный отступ",
    document_type=DocumentType.PRACTICE_REPORT,
    severity=Severity.WARNING,
    description="Проверка абзацного отступа (1.25 см)",
    default_config={"indent_mm": 12.5, "tolerance_mm": 3},
)
class ParagraphIndentRule(BaseRule):
    async def check(self, pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
        return await check_paragraph_indent(pdf, config)


@rule(
    code="practice.formatting.alignment",
    name="Выравнивание текста",
    document_type=DocumentType.PRACTICE_REPORT,
    severity=Severity.WARNING,
    description="Проверка выравнивания текста по ширине",
)
class AlignmentRule(BaseRule):
    async def check(self, pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
        return await check_alignment(pdf, config)
