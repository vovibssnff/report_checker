from __future__ import annotations

import pytest

from app.checkers.pdf_parser import ParsedPage, TableInfo
from app.checkers.plugins.vkr_template.formatting import AlignmentRule, FontRule, PageSizeRule, ParagraphIndentRule
from app.core.domain.value_objects import CheckStatus

pytest.skip("VKR reports are disabled in this deployment", allow_module_level=True)


class TestPageSizeRule:
    @pytest.fixture()
    def rule(self):
        return PageSizeRule()

    @pytest.mark.asyncio
    async def test_correct_a4_passes(self, rule, make_parsed_page, make_parsed_pdf):
        pages = [
            make_parsed_page(number=1, width_mm=210.0, height_mm=297.0),
            make_parsed_page(number=2, width_mm=210.0, height_mm=297.0),
        ]
        pdf = make_parsed_pdf(pages=pages)

        results = await rule.check(pdf, {"tolerance_mm": 5})

        assert len(results) == 1
        assert results[0].status == CheckStatus.PASSED

    @pytest.mark.asyncio
    async def test_within_tolerance_passes(self, rule, make_parsed_page, make_parsed_pdf):
        pages = [make_parsed_page(number=1, width_mm=212.0, height_mm=295.0)]
        pdf = make_parsed_pdf(pages=pages)

        results = await rule.check(pdf, {"tolerance_mm": 5})

        assert results[0].status == CheckStatus.PASSED

    @pytest.mark.asyncio
    async def test_wrong_dimensions_fails(self, rule, make_parsed_page, make_parsed_pdf):
        pages = [make_parsed_page(number=1, width_mm=180.0, height_mm=250.0)]
        pdf = make_parsed_pdf(pages=pages)

        results = await rule.check(pdf, {"tolerance_mm": 5})

        assert len(results) == 1
        assert results[0].status == CheckStatus.FAILED
        assert results[0].details["pages"] == [1]

    @pytest.mark.asyncio
    async def test_mixed_pages(self, rule, make_parsed_page, make_parsed_pdf):
        pages = [
            make_parsed_page(number=1, width_mm=210.0, height_mm=297.0),
            make_parsed_page(number=2, width_mm=150.0, height_mm=200.0),
            make_parsed_page(number=3, width_mm=210.0, height_mm=297.0),
        ]
        pdf = make_parsed_pdf(pages=pages)

        results = await rule.check(pdf, {"tolerance_mm": 5})

        assert results[0].status == CheckStatus.FAILED
        assert results[0].details["pages"] == [2]

    @pytest.mark.asyncio
    async def test_empty_pdf_passes(self, rule, make_parsed_pdf):
        pdf = make_parsed_pdf(pages=[])
        results = await rule.check(pdf, {"tolerance_mm": 5})
        assert results[0].status == CheckStatus.PASSED


class TestFontRule:
    @pytest.fixture()
    def rule(self):
        return FontRule()

    @pytest.mark.asyncio
    async def test_times_new_roman_passes(self, rule, make_text_block, make_parsed_page, make_parsed_pdf):
        blocks = [
            make_text_block(
                text="A" * 100,
                font_name="TimesNewRomanPSMT",
                font_size=14.0,
            ),
        ]
        pages = [make_parsed_page(text_blocks=blocks)]
        pdf = make_parsed_pdf(pages=pages)

        results = await rule.check(pdf, {"expected_font": "Times", "min_size": 12})

        assert len(results) == 1
        assert results[0].status == CheckStatus.PASSED

    @pytest.mark.asyncio
    async def test_wrong_font_fails(self, rule, make_text_block, make_parsed_page, make_parsed_pdf):
        blocks = [
            make_text_block(
                text="A" * 100,
                font_name="Arial",
                font_size=14.0,
            ),
        ]
        pages = [make_parsed_page(text_blocks=blocks)]
        pdf = make_parsed_pdf(pages=pages)

        results = await rule.check(pdf, {"expected_font": "Times", "min_size": 12})

        failed = [r for r in results if r.status == CheckStatus.FAILED]
        assert len(failed) >= 1
        assert failed[0].message == "font_mismatch"
        assert failed[0].details["dominant_font"] == "Arial"

    @pytest.mark.asyncio
    async def test_small_font_detected(self, rule, make_text_block, make_parsed_page, make_parsed_pdf):
        blocks = [
            make_text_block(
                text="Normal text " * 20,
                font_name="TimesNewRomanPSMT",
                font_size=14.0,
            ),
            make_text_block(
                text="Small text here",
                font_name="TimesNewRomanPSMT",
                font_size=9.0,
            ),
        ]
        pages = [make_parsed_page(text_blocks=blocks)]
        pdf = make_parsed_pdf(pages=pages)

        results = await rule.check(pdf, {"expected_font": "Times", "min_size": 12})

        failed = [r for r in results if r.status == CheckStatus.FAILED]
        assert len(failed) >= 1

    @pytest.mark.asyncio
    async def test_empty_pdf_passes(self, rule, make_parsed_pdf):
        pdf = make_parsed_pdf(pages=[])
        results = await rule.check(pdf, {"expected_font": "Times", "min_size": 12})
        assert results[0].status == CheckStatus.PASSED

    @pytest.mark.asyncio
    async def test_default_config_used(self, rule, make_text_block, make_parsed_page, make_parsed_pdf):
        blocks = [
            make_text_block(
                text="A" * 100,
                font_name="TimesNewRomanPSMT",
                font_size=14.0,
            ),
        ]
        pages = [make_parsed_page(text_blocks=blocks)]
        pdf = make_parsed_pdf(pages=pages)

        results = await rule.check(pdf, {})

        assert results[0].status == CheckStatus.PASSED


class TestParagraphIndentRule:
    @pytest.fixture()
    def rule(self):
        return ParagraphIndentRule()

    @pytest.mark.asyncio
    async def test_ignores_blocks_inside_tables(self, rule, make_text_block, make_parsed_pdf):
        table_bbox = (80.0, 80.0, 520.0, 200.0)
        blocks = [
            make_text_block(
                text="Text in table row one long enough to be processed",
                bbox=(100.0, 100.0, 500.0, 114.0),
            ),
            make_text_block(
                text="Text in table row two long enough to be processed",
                bbox=(100.0, 125.0, 500.0, 139.0),
            ),
            make_text_block(
                text="Text in table row three long enough to be processed",
                bbox=(100.0, 150.0, 500.0, 164.0),
            ),
        ]
        page = ParsedPage(
            number=1,
            width_mm=210.0,
            height_mm=297.0,
            text_blocks=blocks,
            tables=[TableInfo(page_number=1, bbox=table_bbox, rows=3, cols=2)],
            lines=[],
        )
        pdf = make_parsed_pdf(pages=[page])

        results = await rule.check(pdf, {"indent_mm": 12.5, "tolerance_mm": 3})

        assert len(results) == 1
        assert results[0].status == CheckStatus.PASSED


class TestAlignmentRule:
    @pytest.fixture()
    def rule(self):
        return AlignmentRule()

    @pytest.mark.asyncio
    async def test_ignores_blocks_inside_tables(self, rule, make_text_block, make_parsed_pdf):
        table_bbox = (80.0, 80.0, 520.0, 220.0)
        blocks = [
            make_text_block(
                text="First table row content that is clearly longer than thirty chars",
                bbox=(100.0, 95.0, 430.0, 110.0),
            ),
            make_text_block(
                text="Second table row content that is clearly longer than thirty chars",
                bbox=(100.0, 125.0, 470.0, 140.0),
            ),
            make_text_block(
                text="Third table row content that is clearly longer than thirty chars",
                bbox=(100.0, 155.0, 390.0, 170.0),
            ),
        ]
        page = ParsedPage(
            number=1,
            width_mm=210.0,
            height_mm=297.0,
            text_blocks=blocks,
            tables=[TableInfo(page_number=1, bbox=table_bbox, rows=3, cols=2)],
            lines=[],
        )
        pdf = make_parsed_pdf(pages=[page])

        results = await rule.check(pdf, {})

        assert len(results) == 1
        assert results[0].status == CheckStatus.PASSED
