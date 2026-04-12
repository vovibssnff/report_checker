from __future__ import annotations

from datetime import datetime

import pytest

from app.checkers.plugins.practice_report.title_page import TitlePageContentRule
from app.core.domain.value_objects import CheckStatus


@pytest.mark.asyncio
async def test_practice_title_page_content_valid(make_parsed_page, make_parsed_pdf):
    year = datetime.now().year
    page = make_parsed_page(lines=[f"ОТЧЕТ об учебной, ознакомительной практике {year}"])
    results = await TitlePageContentRule().check(make_parsed_pdf(pages=[page]), {})
    assert results[0].status == CheckStatus.PASSED
