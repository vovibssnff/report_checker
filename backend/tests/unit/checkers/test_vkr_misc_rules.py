from __future__ import annotations

import pytest

from app.checkers.plugins.vkr_template.appendices import AppendixLabelingRule
from app.checkers.plugins.vkr_template.formulas import FormulaNumberingRule
from app.core.domain.value_objects import CheckStatus


class TestAppendixLabelingRule:
    @pytest.fixture()
    def rule(self) -> AppendixLabelingRule:
        return AppendixLabelingRule()

    @pytest.mark.asyncio
    async def test_passes_when_no_appendices(self, rule, make_parsed_page, make_parsed_pdf) -> None:
        pdf = make_parsed_pdf(pages=[make_parsed_page(lines=["Введение", "Текст главы"])])

        results = await rule.check(pdf, {})

        assert results[0].status == CheckStatus.PASSED
        assert results[0].message == "appendices_not_found"

    @pytest.mark.asyncio
    async def test_fails_for_wrong_order(self, rule, make_parsed_page, make_parsed_pdf) -> None:
        pages = [
            make_parsed_page(number=1, lines=["Приложение А"]),
            make_parsed_page(number=2, lines=["Приложение В"]),
        ]
        pdf = make_parsed_pdf(pages=pages)

        results = await rule.check(pdf, {})

        assert results[0].status == CheckStatus.FAILED
        assert results[0].message == "appendices_labeling_invalid"
        assert results[0].details["issues"][0]["type"] == "wrong_order"

    @pytest.mark.asyncio
    async def test_fails_for_invalid_label(self, rule, make_parsed_page, make_parsed_pdf) -> None:
        pages = [make_parsed_page(number=1, lines=["Приложение Ё"])]
        pdf = make_parsed_pdf(pages=pages)

        results = await rule.check(pdf, {})

        assert results[0].status == CheckStatus.FAILED
        assert results[0].details["issues"][0]["type"] == "invalid_label"


class TestFormulaNumberingRule:
    @pytest.fixture()
    def rule(self) -> FormulaNumberingRule:
        return FormulaNumberingRule()

    @pytest.mark.asyncio
    async def test_passes_when_no_formulas(self, rule, make_parsed_page, make_parsed_pdf) -> None:
        pdf = make_parsed_pdf(pages=[make_parsed_page(lines=["обычный текст без нумерации"])])

        results = await rule.check(pdf, {})

        assert results[0].status == CheckStatus.PASSED
        assert results[0].message == "formulas_not_found"

    @pytest.mark.asyncio
    async def test_passes_when_numbering_sequential(self, rule, make_parsed_page, make_parsed_pdf) -> None:
        pages = [
            make_parsed_page(number=1, lines=["E = mc^2 (1)", "a+b=c (2)"]),
            make_parsed_page(number=2, lines=["x+y=z (3)"]),
        ]
        pdf = make_parsed_pdf(pages=pages)

        results = await rule.check(pdf, {})

        assert results[0].status == CheckStatus.PASSED
        assert results[0].message == "formula_numbering_ok"

    @pytest.mark.asyncio
    async def test_fails_when_numbering_has_gap(self, rule, make_parsed_page, make_parsed_pdf) -> None:
        pages = [
            make_parsed_page(number=1, lines=["f(x) (1)", "g(x) (3)"]),
        ]
        pdf = make_parsed_pdf(pages=pages)

        results = await rule.check(pdf, {})

        assert results[0].status == CheckStatus.FAILED
        assert results[0].message == "formula_numbering_invalid"
        assert results[0].details["gaps_at"] == [3]
