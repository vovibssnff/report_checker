from __future__ import annotations

import pytest

from app.checkers.plugins.vkr_template.headings import StructuralElementsRule
from app.core.domain.value_objects import CheckStatus

pytest.skip("VKR reports are disabled in this deployment", allow_module_level=True)


class TestStructuralElementsRule:
    @pytest.fixture()
    def rule(self) -> StructuralElementsRule:
        return StructuralElementsRule()

    @pytest.mark.asyncio
    async def test_ignores_inline_appendix_mentions(self, rule, make_text_block, make_parsed_page, make_parsed_pdf):
        blocks = [
            make_text_block(
                text="Подтверждения приведены в приложении А и приложении Б.",
                is_bold=False,
                bbox=(85.0, 100.0, 510.0, 114.0),
            )
        ]
        page = make_parsed_page(number=1, text_blocks=blocks)
        pdf = make_parsed_pdf(pages=[page])

        results = await rule.check(pdf, {})

        assert len(results) == 1
        assert results[0].status == CheckStatus.PASSED
        assert results[0].message == "structural_elements_ok"

    @pytest.mark.asyncio
    async def test_ignores_inline_introduction_and_conclusion_mentions(
        self, rule, make_text_block, make_parsed_page, make_parsed_pdf
    ):
        blocks = [
            make_text_block(
                text="Заключение по главе показывает рост показателей.",
                is_bold=False,
                bbox=(85.0, 100.0, 510.0, 114.0),
            ),
            make_text_block(
                text="Введение в методику изложено в начале документа.",
                is_bold=False,
                bbox=(85.0, 120.0, 510.0, 134.0),
            ),
        ]
        page = make_parsed_page(number=1, text_blocks=blocks)
        pdf = make_parsed_pdf(pages=[page])

        results = await rule.check(pdf, {})

        assert len(results) == 1
        assert results[0].status == CheckStatus.PASSED
        assert results[0].message == "structural_elements_ok"

    @pytest.mark.asyncio
    async def test_appendix_must_be_right_aligned(self, rule, make_text_block, make_parsed_page, make_parsed_pdf):
        # Centered appendix heading should be flagged (must be right aligned).
        centered_appendix = make_text_block(
            text="ПРИЛОЖЕНИЕ А",
            is_bold=True,
            bbox=(220.0, 100.0, 360.0, 114.0),
        )
        page = make_parsed_page(number=1, text_blocks=[centered_appendix])
        pdf = make_parsed_pdf(pages=[page])

        results = await rule.check(pdf, {})

        assert len(results) == 1
        assert results[0].status == CheckStatus.FAILED
        assert results[0].message == "structural_elements_invalid"
        assert "not_right_aligned" in results[0].details["violations"][0]["issues"]

    @pytest.mark.asyncio
    async def test_right_aligned_appendix_passes(self, rule, make_text_block, make_parsed_page, make_parsed_pdf):
        # A4 width in points ~595; right edge near page edge should pass.
        right_aligned_appendix = make_text_block(
            text="ПРИЛОЖЕНИЕ Б",
            is_bold=True,
            bbox=(430.0, 100.0, 585.0, 114.0),
        )
        page = make_parsed_page(number=1, text_blocks=[right_aligned_appendix])
        pdf = make_parsed_pdf(pages=[page])

        results = await rule.check(pdf, {})

        assert len(results) == 1
        assert results[0].status == CheckStatus.PASSED
        assert results[0].message == "structural_elements_ok"
