from __future__ import annotations

import pytest

from app.checkers.plugins.practice_report.formulas import FormulaNumberingRule
from app.core.domain.value_objects import CheckStatus


@pytest.mark.asyncio
async def test_practice_formula_numbering_runs(make_parsed_page, make_parsed_pdf):
    page = make_parsed_page(lines=["f(x) = x + 1 (1)"])
    results = await FormulaNumberingRule().check(make_parsed_pdf(pages=[page]), {})
    assert results[0].status == CheckStatus.PASSED
