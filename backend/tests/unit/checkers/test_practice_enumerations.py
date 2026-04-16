from __future__ import annotations

import pytest

from app.checkers.plugins.practice_report.enumerations import EnumerationsFormatRule
from app.core.domain.value_objects import CheckStatus


@pytest.mark.asyncio
async def test_practice_enumerations_valid(make_parsed_page, make_parsed_pdf):
    page = make_parsed_page(lines=["— Первый пункт", "а) Второй пункт", "1) Третий пункт"])
    results = await EnumerationsFormatRule().check(make_parsed_pdf(pages=[page]), {})
    assert results[0].status == CheckStatus.PASSED
