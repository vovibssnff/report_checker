from __future__ import annotations

import pytest

from app.checkers.plugins.vkr_template.appendices import AppendixLabelingRule
from app.checkers.plugins.vkr_template.formulas import FormulaNumberingRule
from app.core.domain.value_objects import CheckStatus

pytest.skip("VKR reports are disabled in this deployment", allow_module_level=True)


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

    @pytest.mark.asyncio
    async def test_detects_spaced_letters_appendix(self, rule, make_parsed_page, make_parsed_pdf) -> None:
        pages = [make_parsed_page(number=1, lines=["П Р И Л О Ж Е Н И Е   А"])]
        pdf = make_parsed_pdf(pages=pages)

        results = await rule.check(pdf, {})

        assert results[0].status == CheckStatus.PASSED
        assert results[0].message == "appendices_labeling_ok"

    @pytest.mark.asyncio
    async def test_detects_appendix_from_text_blocks_when_lines_empty(
        self, rule, make_text_block, make_parsed_page, make_parsed_pdf
    ) -> None:
        blocks = [make_text_block(text="ПРИЛОЖЕНИЕ А", is_bold=True)]
        page = make_parsed_page(number=1, text_blocks=blocks, lines=[])
        pdf = make_parsed_pdf(pages=[page])

        results = await rule.check(pdf, {})

        assert results[0].status == CheckStatus.PASSED
        assert results[0].message == "appendices_labeling_ok"

    @pytest.mark.asyncio
    async def test_ignores_appendix_mentions_in_plain_text(self, rule, make_parsed_page, make_parsed_pdf) -> None:
        pages = [
            make_parsed_page(
                number=1,
                lines=[
                    "В приложении А приведены дополнительные материалы.",
                    "См. приложение Б в конце работы.",
                ],
            )
        ]
        pdf = make_parsed_pdf(pages=pages)

        results = await rule.check(pdf, {})

        assert results[0].status == CheckStatus.PASSED
        assert results[0].message == "appendices_not_found"


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

    @pytest.mark.asyncio
    async def test_ignores_plain_text_references_in_parentheses(self, rule, make_parsed_page, make_parsed_pdf) -> None:
        pages = [
            make_parsed_page(
                number=1,
                lines=[
                    "Описание метода приведено в разделе (1)",
                    "Подробности см. в приложении (2)",
                ],
            ),
        ]
        pdf = make_parsed_pdf(pages=pages)

        results = await rule.check(pdf, {})

        assert results[0].status == CheckStatus.PASSED
        assert results[0].message == "formulas_not_found"
