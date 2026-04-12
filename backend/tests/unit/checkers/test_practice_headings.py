from __future__ import annotations

import pytest

from app.checkers.plugins.practice_report.headings import NewPageRule, SectionNumberingRule, StructuralElementsRule
from app.core.domain.value_objects import CheckStatus


@pytest.mark.asyncio
async def test_practice_structural_elements_runs(make_parsed_pdf):
    results = await StructuralElementsRule().check(make_parsed_pdf(pages=[]), {})
    assert results[0].status == CheckStatus.PASSED


@pytest.mark.asyncio
async def test_practice_new_page_rule_runs(make_parsed_pdf):
    results = await NewPageRule().check(make_parsed_pdf(pages=[]), {})
    assert results[0].status == CheckStatus.PASSED


@pytest.mark.asyncio
async def test_practice_section_numbering_accepts_top_level(make_text_block, make_parsed_page, make_parsed_pdf):
    page = make_parsed_page(text_blocks=[make_text_block(text="1 НАЗВАНИЕ", is_bold=True)])
    results = await SectionNumberingRule().check(make_parsed_pdf(pages=[page]), {})
    assert results[0].status == CheckStatus.PASSED


@pytest.mark.asyncio
async def test_practice_structural_elements_skips_toc_page_for_appendix(
    make_text_block,
    make_parsed_page,
    make_parsed_pdf,
):
    toc_page = make_parsed_page(
        lines=["СОДЕРЖАНИЕ", "ПРИЛОЖЕНИЕ А .......... 12"],
        text_blocks=[make_text_block(text="ПРИЛОЖЕНИЕ А", is_bold=True, bbox=(80, 100, 180, 115))],
    )
    results = await StructuralElementsRule().check(make_parsed_pdf(pages=[toc_page]), {})
    assert results[0].status == CheckStatus.PASSED
