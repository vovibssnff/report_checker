from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.checkers.plugins.vkr_template.formulas import FormulaNumberingRule

if TYPE_CHECKING:
    from app.checkers.base import RuleResult
    from app.checkers.pdf_parser import ParsedPDF


async def check_formula_numbering(pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
    return await FormulaNumberingRule().check(pdf, config)
