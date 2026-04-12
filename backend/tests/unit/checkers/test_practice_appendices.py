from __future__ import annotations

import pytest

from app.checkers.plugins.practice_report.appendices import AppendixLabelingRule
from app.core.domain.value_objects import CheckStatus


@pytest.mark.asyncio
async def test_practice_appendices_runs(make_parsed_page, make_parsed_pdf):
    page = make_parsed_page(lines=["ПРИЛОЖЕНИЕ А"])
    results = await AppendixLabelingRule().check(make_parsed_pdf(pages=[page]), {})
    assert results[0].status == CheckStatus.PASSED
