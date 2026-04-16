from __future__ import annotations

import pytest

from app.checkers.plugins.practice_report.pagination import ArabicNumbersRule, PageNumberPositionRule
from app.core.domain.value_objects import CheckStatus


@pytest.mark.asyncio
async def test_practice_arabic_pagination_runs(make_parsed_page, make_parsed_pdf):
    page = make_parsed_page(number=1, lines=["Text"])
    results = await ArabicNumbersRule().check(make_parsed_pdf(pages=[page]), {})
    assert results[0].status == CheckStatus.PASSED


@pytest.mark.asyncio
async def test_practice_pagination_position_runs(make_parsed_page, make_parsed_pdf):
    page = make_parsed_page(number=1, lines=["Text"])
    results = await PageNumberPositionRule().check(make_parsed_pdf(pages=[page]), {})
    assert results[0].status == CheckStatus.PASSED
