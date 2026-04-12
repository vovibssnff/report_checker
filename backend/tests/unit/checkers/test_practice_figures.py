from __future__ import annotations

import pytest

from app.checkers.plugins.practice_report.figures import FigureCaptionFormatRule, FigureNumberingRule
from app.core.domain.value_objects import CheckStatus


@pytest.mark.asyncio
async def test_practice_figure_caption_invalid_without_dash(make_text_block, make_parsed_page, make_parsed_pdf):
    page = make_parsed_page(text_blocks=[make_text_block(text="Рисунок 1 Название")])
    results = await FigureCaptionFormatRule().check(make_parsed_pdf(pages=[page]), {})
    assert results[0].status == CheckStatus.FAILED


@pytest.mark.asyncio
async def test_practice_figure_numbering_runs(make_parsed_pdf):
    results = await FigureNumberingRule().check(make_parsed_pdf(pages=[]), {})
    assert results[0].status == CheckStatus.PASSED
