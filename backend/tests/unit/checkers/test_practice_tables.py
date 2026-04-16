from __future__ import annotations

import pytest

from app.checkers.plugins.practice_report.tables import TableCaptionFormatRule, TableNumberingRule
from app.core.domain.value_objects import CheckStatus


@pytest.mark.asyncio
async def test_practice_table_caption_invalid_without_dash(make_text_block, make_parsed_page, make_parsed_pdf):
    page = make_parsed_page(text_blocks=[make_text_block(text="Таблица 1 Название")])
    results = await TableCaptionFormatRule().check(make_parsed_pdf(pages=[page]), {})
    assert results[0].status == CheckStatus.FAILED


@pytest.mark.asyncio
async def test_practice_table_numbering_runs(make_parsed_pdf):
    results = await TableNumberingRule().check(make_parsed_pdf(pages=[]), {})
    assert results[0].status == CheckStatus.PASSED
