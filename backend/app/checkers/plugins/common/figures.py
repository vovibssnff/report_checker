from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.checkers.plugins.vkr_template.figures import FigureCaptionFormatRule, FigureNumberingRule

if TYPE_CHECKING:
    from app.checkers.base import RuleResult
    from app.checkers.pdf_parser import ParsedPDF


async def check_figure_caption_format(pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
    return await FigureCaptionFormatRule().check(pdf, config)


async def check_figure_numbering(pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
    return await FigureNumberingRule().check(pdf, config)
