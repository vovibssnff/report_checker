from __future__ import annotations

import pytest

from app.checkers.pdf_parser import HeadingInfo
from app.checkers.plugins.practice_report.toc import TOCContentRule
from app.core.domain.value_objects import CheckStatus


@pytest.mark.asyncio
async def test_practice_toc_content_valid(make_parsed_page, make_parsed_pdf):
    toc_page = make_parsed_page(lines=["СОДЕРЖАНИЕ", "ВВЕДЕНИЕ .......... 2"])
    body_page = make_parsed_page(number=2, lines=["ВВЕДЕНИЕ"])
    pdf = make_parsed_pdf(pages=[toc_page, body_page], headings=[HeadingInfo(text="ВВЕДЕНИЕ", level=1, page_number=2)])
    results = await TOCContentRule().check(pdf, {})
    assert results[0].status == CheckStatus.PASSED


@pytest.mark.asyncio
async def test_practice_toc_unicode_ellipsis_and_no_headings(make_parsed_page, make_parsed_pdf):
    """Leaders may be U+2026; headings list may be empty if fonts do not match heuristics."""
    toc_page = make_parsed_page(lines=["СОДЕРЖАНИЕ", "ВВЕДЕНИЕ … 2"])
    body_page = make_parsed_page(number=2, lines=["ВВЕДЕНИЕ", "Some body text"])
    pdf = make_parsed_pdf(pages=[toc_page, body_page], headings=[])
    results = await TOCContentRule().check(pdf, {})
    assert results[0].status == CheckStatus.PASSED


@pytest.mark.asyncio
async def test_practice_toc_long_space_gap_instead_of_dots(make_parsed_page, make_parsed_pdf):
    toc_page = make_parsed_page(lines=["СОДЕРЖАНИЕ", "ЗАКЛЮЧЕНИЕ     11"])
    body_page = make_parsed_page(number=3, lines=["ЗАКЛЮЧЕНИЕ", "text"])
    pdf = make_parsed_pdf(pages=[toc_page, body_page], headings=[])
    results = await TOCContentRule().check(pdf, {})
    assert results[0].status == CheckStatus.PASSED
