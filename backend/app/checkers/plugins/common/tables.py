from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.checkers.plugins.vkr_template.tables import TableCaptionFormatRule, TableNumberingRule

if TYPE_CHECKING:
    from app.checkers.base import RuleResult
    from app.checkers.pdf_parser import ParsedPDF


async def check_table_caption_format(pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
    return await TableCaptionFormatRule().check(pdf, config)


async def check_table_numbering(pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
    return await TableNumberingRule().check(pdf, config)
