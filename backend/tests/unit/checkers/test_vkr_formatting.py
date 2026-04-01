from __future__ import annotations

import pytest

from app.checkers.plugins.vkr_template.formatting import FontRule, PageSizeRule
from app.core.domain.value_objects import CheckStatus


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
