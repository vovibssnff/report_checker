from __future__ import annotations

import pytest

from app.checkers.plugins.practice_report.structure import RequiredSectionsRule
from app.core.domain.value_objects import CheckStatus


class TestPracticeRequiredSectionsRule:
    @pytest.fixture()
    def rule(self) -> RequiredSectionsRule:
        return RequiredSectionsRule()

    @pytest.mark.asyncio
    async def test_detects_spaced_letters_toc_and_extended_names(
        self,
        rule,
        make_text_block,
        make_parsed_page,
        make_parsed_pdf,
    ) -> None:
        pages = [
            make_parsed_page(
                number=1,
                text_blocks=[make_text_block(text="ТИТУЛЬНЫЙ ЛИСТ ОТЧЕТА", bbox=(130.0, 80.0, 470.0, 96.0))],
                lines=["ТИТУЛЬНЫЙ ЛИСТ ОТЧЕТА"],
            ),
            make_parsed_page(number=2, lines=["ЗАДАНИЕ НА ПРАКТИКУ"]),
            make_parsed_page(number=3, lines=["С О Д Е Р Ж А Н И Е"]),
            make_parsed_page(
                number=4,
                text_blocks=[make_text_block(text="ВВЕДЕНИЕ В ПРЕДМЕТ ПРАКТИКИ", bbox=(120.0, 80.0, 490.0, 96.0))],
                lines=["ВВЕДЕНИЕ В ПРЕДМЕТ ПРАКТИКИ"],
            ),
            make_parsed_page(
                number=5,
                text_blocks=[make_text_block(text="ЗАКЛЮЧЕНИЕ ПО ИТОГАМ ПРАКТИКИ", bbox=(110.0, 80.0, 500.0, 96.0))],
                lines=["ЗАКЛЮЧЕНИЕ ПО ИТОГАМ ПРАКТИКИ"],
            ),
        ]
        pdf = make_parsed_pdf(pages=pages)

        results = await rule.check(pdf, {})

        assert len(results) == 1
        assert results[0].status == CheckStatus.PASSED
        assert results[0].message == "required_sections_ok"

    @pytest.mark.asyncio
    async def test_reports_format_error_not_missing_when_section_exists(
        self,
        rule,
        make_text_block,
        make_parsed_page,
        make_parsed_pdf,
    ) -> None:
        pages = [
            make_parsed_page(
                number=1,
                text_blocks=[make_text_block(text="Титульный лист", bbox=(100.0, 80.0, 360.0, 96.0))],
                lines=["Титульный лист"],
            ),
            make_parsed_page(
                number=2,
                text_blocks=[make_text_block(text="ЗАДАНИЕ", bbox=(180.0, 80.0, 410.0, 96.0))],
                lines=["ЗАДАНИЕ"],
            ),
            make_parsed_page(
                number=3,
                text_blocks=[make_text_block(text="СОДЕРЖАНИЕ", bbox=(180.0, 80.0, 410.0, 96.0))],
                lines=["СОДЕРЖАНИЕ"],
            ),
            make_parsed_page(
                number=4,
                text_blocks=[make_text_block(text="ВВЕДЕНИЕ", bbox=(180.0, 80.0, 410.0, 96.0))],
                lines=["ВВЕДЕНИЕ"],
            ),
            make_parsed_page(
                number=5,
                text_blocks=[make_text_block(text="ЗАКЛЮЧЕНИЕ", bbox=(170.0, 80.0, 420.0, 96.0))],
                lines=["ЗАКЛЮЧЕНИЕ"],
            ),
        ]
        pdf = make_parsed_pdf(pages=pages)

        results = await rule.check(pdf, {})

        assert len(results) == 1
        assert results[0].status == CheckStatus.FAILED
        assert results[0].message == "required_sections_format_invalid"
        assert "missing_sections" not in (results[0].details or {})
        assert results[0].details["violations"]

    @pytest.mark.asyncio
    async def test_ignores_inline_mentions_of_sections(self, rule, make_parsed_page, make_parsed_pdf) -> None:
        lines = [
            "В введении описана цель практики.",
            "В содержании перечислены этапы.",
            "В заключении отражены результаты.",
        ]
        page = make_parsed_page(number=1, lines=lines)
        pdf = make_parsed_pdf(pages=[page])

        results = await rule.check(pdf, {})

        assert len(results) == 1
        assert results[0].status == CheckStatus.FAILED
        assert results[0].message == "required_sections_missing"

    @pytest.mark.asyncio
    async def test_detects_title_page_by_university_markers(
        self, rule, make_text_block, make_parsed_page, make_parsed_pdf
    ) -> None:
        page1_lines = [
            "Министерство науки и высшего образования Российской Федерации",
            "Университет ИТМО",
            "Факультет инфокоммуникационных технологий",
        ]
        pages = [
            make_parsed_page(number=1, lines=page1_lines),
            make_parsed_page(
                number=2,
                text_blocks=[make_text_block(text="ЗАДАНИЕ", bbox=(180.0, 80.0, 410.0, 96.0))],
                lines=["ЗАДАНИЕ"],
            ),
            make_parsed_page(
                number=3,
                text_blocks=[make_text_block(text="СОДЕРЖАНИЕ", bbox=(180.0, 80.0, 410.0, 96.0))],
                lines=["СОДЕРЖАНИЕ"],
            ),
            make_parsed_page(
                number=4,
                text_blocks=[make_text_block(text="ВВЕДЕНИЕ", bbox=(180.0, 80.0, 410.0, 96.0))],
                lines=["ВВЕДЕНИЕ"],
            ),
            make_parsed_page(
                number=5,
                text_blocks=[make_text_block(text="ЗАКЛЮЧЕНИЕ", bbox=(170.0, 80.0, 420.0, 96.0))],
                lines=["ЗАКЛЮЧЕНИЕ"],
            ),
        ]
        pdf = make_parsed_pdf(pages=pages)

        results = await rule.check(pdf, {})

        assert len(results) == 1
        assert results[0].status == CheckStatus.PASSED
        assert results[0].message == "required_sections_ok"
