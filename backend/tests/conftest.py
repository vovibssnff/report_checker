from __future__ import annotations

import pytest

from app.checkers.pdf_parser import (
    HeadingInfo,
    ParsedPage,
    ParsedPDF,
    TextBlock,
)


@pytest.fixture()
def make_text_block():
    def _factory(
        text: str = "Sample text",
        font_name: str = "TimesNewRomanPSMT",
        font_size: float = 14.0,
        is_bold: bool = False,
        is_italic: bool = False,
        bbox: tuple[float, float, float, float] = (85.0, 100.0, 510.0, 114.0),
    ) -> TextBlock:
        return TextBlock(
            text=text,
            font_name=font_name,
            font_size=font_size,
            is_bold=is_bold,
            is_italic=is_italic,
            bbox=bbox,
        )

    return _factory


@pytest.fixture()
def make_parsed_page():
    def _factory(
        number: int = 1,
        width_mm: float = 210.0,
        height_mm: float = 297.0,
        text_blocks: list[TextBlock] | None = None,
        lines: list[str] | None = None,
    ) -> ParsedPage:
        return ParsedPage(
            number=number,
            width_mm=width_mm,
            height_mm=height_mm,
            text_blocks=text_blocks or [],
            lines=lines or [],
        )

    return _factory


@pytest.fixture()
def make_parsed_pdf():
    def _factory(
        pages: list[ParsedPage] | None = None,
        headings: list[HeadingInfo] | None = None,
        fonts_used: set[str] | None = None,
    ) -> ParsedPDF:
        page_list = pages or []
        return ParsedPDF(
            pages=page_list,
            metadata={},
            headings=headings or [],
            page_count=len(page_list),
            fonts_used=fonts_used or set(),
        )

    return _factory
