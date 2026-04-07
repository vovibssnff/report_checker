from __future__ import annotations

import pytest

from app.checkers.plugins.vkr_template.headings import SectionNumberingRule
from app.core.domain.value_objects import CheckStatus


class TestSectionNumberingRule:
    @pytest.fixture()
    def rule(self) -> SectionNumberingRule:
        return SectionNumberingRule()

    @pytest.mark.asyncio
    async def test_fails_when_heading_number_has_no_dot(self, rule, make_text_block, make_parsed_page, make_parsed_pdf):
        blocks = [
            make_text_block(text="1 НАЗВАНИЕ", is_bold=True),
            make_text_block(text="2. НАЗВАНИЕ", is_bold=True, bbox=(85.0, 130.0, 510.0, 144.0)),
        ]
        page = make_parsed_page(number=1, text_blocks=blocks)
        pdf = make_parsed_pdf(pages=[page])

        results = await rule.check(pdf, {})

        assert len(results) == 1
        assert results[0].status == CheckStatus.FAILED
        assert results[0].message == "section_numbering_invalid"
        assert any(issue["type"] == "missing_dot_after_number" for issue in results[0].details["issues"])

    @pytest.mark.asyncio
    async def test_accepts_heading_number_with_dot(self, rule, make_text_block, make_parsed_page, make_parsed_pdf):
        blocks = [
            make_text_block(text="1. НАЗВАНИЕ", is_bold=True),
            make_text_block(text="2. НАЗВАНИЕ", is_bold=True, bbox=(85.0, 130.0, 510.0, 144.0)),
        ]
        page = make_parsed_page(number=1, text_blocks=blocks)
        pdf = make_parsed_pdf(pages=[page])

        results = await rule.check(pdf, {})

        assert len(results) == 1
        assert results[0].status == CheckStatus.PASSED
        assert results[0].message == "section_numbering_ok"
