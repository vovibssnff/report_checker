from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.checkers.plugins.vkr_template.headings import NewPageRule, SectionNumberingRule, StructuralElementsRule

if TYPE_CHECKING:
    from app.checkers.base import RuleResult
    from app.checkers.pdf_parser import ParsedPDF


async def check_structural_elements(pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
    return await StructuralElementsRule().check(pdf, config)


async def check_new_page(pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
    return await NewPageRule().check(pdf, config)


async def check_section_numbering(pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
    return await SectionNumberingRule().check(pdf, config)
