from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.checkers.plugins.vkr_template.pagination import ArabicNumbersRule, PageNumberPositionRule

if TYPE_CHECKING:
    from app.checkers.base import RuleResult
    from app.checkers.pdf_parser import ParsedPDF


async def check_arabic_numbers(pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
    return await ArabicNumbersRule().check(pdf, config)


async def check_page_number_position(pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
    return await PageNumberPositionRule().check(pdf, config)
