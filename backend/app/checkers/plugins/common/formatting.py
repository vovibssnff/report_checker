from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.checkers.plugins.vkr_template.formatting import (
    AlignmentRule,
    FontRule,
    LineSpacingRule,
    MarginsRule,
    PageSizeRule,
    ParagraphIndentRule,
)

if TYPE_CHECKING:
    from app.checkers.base import RuleResult
    from app.checkers.pdf_parser import ParsedPDF


async def check_page_size(pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
    return await PageSizeRule().check(pdf, config)


async def check_margins(pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
    return await MarginsRule().check(pdf, config)


async def check_font(pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
    return await FontRule().check(pdf, config)


async def check_line_spacing(pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
    return await LineSpacingRule().check(pdf, config)


async def check_paragraph_indent(pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
    return await ParagraphIndentRule().check(pdf, config)


async def check_alignment(pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
    return await AlignmentRule().check(pdf, config)
