from __future__ import annotations

import pytest

from app.checkers.pdf_parser import ParsedPage, TableInfo
from app.checkers.plugins.vkr_template.tables import TableNumberingRule
from app.core.domain.value_objects import CheckStatus


class TestTableNumberingRule:
    @pytest.fixture()
    def rule(self) -> TableNumberingRule:
        return TableNumberingRule()

    @pytest.mark.asyncio
    async def test_does_not_return_not_found_when_layout_tables_exist(self, rule, make_parsed_pdf) -> None:
        page = ParsedPage(
            number=1,
            width_mm=210.0,
            height_mm=297.0,
            text_blocks=[],
            tables=[TableInfo(page_number=1, bbox=(80.0, 100.0, 520.0, 220.0), rows=4, cols=3)],
            lines=[],
        )
        pdf = make_parsed_pdf(pages=[page])

        results = await rule.check(pdf, {})

        assert len(results) == 1
        assert results[0].status == CheckStatus.PASSED
        assert results[0].message == "table_numbering_ok"

    @pytest.mark.asyncio
    async def test_spaced_letters_caption_is_detected(self, rule, make_parsed_page, make_parsed_pdf) -> None:
        page = make_parsed_page(
            number=1,
            lines=["Т А Б Л И Ц А 1 — Итоги эксперимента"],
        )
        pdf = make_parsed_pdf(pages=[page])

        results = await rule.check(pdf, {})

        assert len(results) == 1
        assert results[0].status == CheckStatus.PASSED
        assert results[0].message == "table_numbering_ok"
