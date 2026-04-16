from __future__ import annotations

import pytest

from app.checkers.plugins.vkr_template.structure import RequiredSectionsRule
from app.core.domain.value_objects import CheckStatus

pytest.skip("VKR reports are disabled in this deployment", allow_module_level=True)


class TestRequiredSectionsRule:
    @pytest.fixture()
    def rule(self) -> RequiredSectionsRule:
        return RequiredSectionsRule()

    @pytest.mark.asyncio
    async def test_detects_all_required_sections_with_extended_names(
        self,
        rule,
        make_text_block,
        make_parsed_page,
        make_parsed_pdf,
    ) -> None:
        page1_blocks = [make_text_block(text="ТИТУЛЬНЫЙ ЛИСТ", bbox=(160.0, 80.0, 430.0, 96.0))]
        page2_blocks = [make_text_block(text="ЗАДАНИЕ НА ВКР", bbox=(170.0, 80.0, 420.0, 96.0))]
        page3_blocks = [make_text_block(text="СОДЕРЖАНИЕ РАБОТЫ", bbox=(160.0, 80.0, 430.0, 96.0))]
        page4_blocks = [make_text_block(text="ВВЕДЕНИЕ В ТЕМУ", bbox=(180.0, 80.0, 410.0, 96.0))]
        page5_blocks = [make_text_block(text="ЗАКЛЮЧЕНИЕ ПО РАБОТЕ", bbox=(160.0, 80.0, 430.0, 96.0))]
        page6_blocks = [
            make_text_block(
                text="СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ И ЛИТЕРАТУРЫ",
                bbox=(80.0, 80.0, 520.0, 96.0),
            )
        ]
        pages = [
            make_parsed_page(number=1, text_blocks=page1_blocks, lines=[b.text for b in page1_blocks]),
            make_parsed_page(number=2, text_blocks=page2_blocks, lines=[b.text for b in page2_blocks]),
            make_parsed_page(number=3, text_blocks=page3_blocks, lines=[b.text for b in page3_blocks]),
            make_parsed_page(number=4, text_blocks=page4_blocks, lines=[b.text for b in page4_blocks]),
            make_parsed_page(number=5, text_blocks=page5_blocks, lines=[b.text for b in page5_blocks]),
            make_parsed_page(number=6, text_blocks=page6_blocks, lines=[b.text for b in page6_blocks]),
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
                text_blocks=[make_text_block(text="титульный лист", bbox=(100.0, 80.0, 360.0, 96.0))],
                lines=["титульный лист"],
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
            make_parsed_page(
                number=6,
                text_blocks=[make_text_block(text="СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ", bbox=(110.0, 80.0, 500.0, 96.0))],
                lines=["СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ"],
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
    async def test_detects_spaced_letters_toc(self, rule, make_text_block, make_parsed_page, make_parsed_pdf) -> None:
        pages = [
            make_parsed_page(
                number=1,
                text_blocks=[make_text_block(text="ТИТУЛЬНЫЙ ЛИСТ", bbox=(160.0, 80.0, 430.0, 96.0))],
                lines=["ТИТУЛЬНЫЙ ЛИСТ"],
            ),
            make_parsed_page(
                number=2,
                text_blocks=[make_text_block(text="ЗАДАНИЕ", bbox=(180.0, 80.0, 410.0, 96.0))],
                lines=["ЗАДАНИЕ"],
            ),
            make_parsed_page(number=3, lines=["С О Д Е Р Ж А Н И Е"]),
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
            make_parsed_page(
                number=6,
                text_blocks=[make_text_block(text="СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ", bbox=(110.0, 80.0, 500.0, 96.0))],
                lines=["СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ"],
            ),
        ]
        pdf = make_parsed_pdf(pages=pages)

        results = await rule.check(pdf, {})

        assert len(results) == 1
        assert results[0].status == CheckStatus.PASSED
        assert results[0].message == "required_sections_ok"

    @pytest.mark.asyncio
    async def test_ignores_inline_mentions_of_sections(self, rule, make_parsed_page, make_parsed_pdf) -> None:
        lines = [
            "В введении рассматриваются основные подходы.",
            "В содержании приведен список разделов.",
            "В заключении подводятся итоги.",
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
            "Факультет программной инженерии",
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
            make_parsed_page(
                number=6,
                text_blocks=[make_text_block(text="СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ", bbox=(110.0, 80.0, 500.0, 96.0))],
                lines=["СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ"],
            ),
        ]
        pdf = make_parsed_pdf(pages=pages)

        results = await rule.check(pdf, {})

        assert len(results) == 1
        assert results[0].status == CheckStatus.PASSED
        assert results[0].message == "required_sections_ok"
