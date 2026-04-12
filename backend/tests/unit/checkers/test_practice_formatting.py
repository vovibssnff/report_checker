from __future__ import annotations

import pytest

from app.checkers.plugins.practice_report.formatting import AlignmentRule, FontRule, ParagraphIndentRule
from app.core.domain.value_objects import CheckStatus


@pytest.mark.asyncio
async def test_practice_font_detects_non_black(make_text_block, make_parsed_page, make_parsed_pdf):
    rule = FontRule()
    page = make_parsed_page(text_blocks=[make_text_block(text="Long text " * 10, color=(0.5, 0.5, 0.5))])
    results = await rule.check(make_parsed_pdf(pages=[page]), {})
    assert any(r.message == "font_color_not_black" for r in results)


@pytest.mark.asyncio
async def test_practice_alignment_rule_runs(make_parsed_pdf):
    results = await AlignmentRule().check(make_parsed_pdf(pages=[]), {})
    assert results[0].status == CheckStatus.PASSED


@pytest.mark.asyncio
async def test_practice_paragraph_indent_rule_runs(make_parsed_pdf):
    results = await ParagraphIndentRule().check(make_parsed_pdf(pages=[]), {})
    assert results[0].status == CheckStatus.PASSED


@pytest.mark.asyncio
async def test_practice_font_skips_bold_in_body_on_title_page(make_text_block, make_parsed_page, make_parsed_pdf):
    page = make_parsed_page(
        lines=[
            "Министерство науки и высшего образования Российской Федерации",
            "Университет ИТМО",
            "Факультет программной инженерии",
        ],
        text_blocks=[make_text_block(text="ОТЧЕТ " * 12, is_bold=True)],
    )
    results = await FontRule().check(make_parsed_pdf(pages=[page]), {})
    assert not any(r.message == "bold_in_body" for r in results)


@pytest.mark.asyncio
async def test_practice_paragraph_indent_skips_title_page(make_text_block, make_parsed_page, make_parsed_pdf):
    blocks = [
        make_text_block(text="Строка " * 12, bbox=(120, 100, 420, 114)),
        make_text_block(text="Строка " * 12, bbox=(120, 130, 420, 144)),
        make_text_block(text="Строка " * 12, bbox=(120, 160, 420, 174)),
    ]
    page = make_parsed_page(
        lines=[
            "Министерство науки и высшего образования Российской Федерации",
            "Университет ИТМО",
            "Факультет программной инженерии",
        ],
        text_blocks=blocks,
    )
    results = await ParagraphIndentRule().check(make_parsed_pdf(pages=[page]), {})
    assert results[0].status == CheckStatus.PASSED


@pytest.mark.asyncio
async def test_practice_alignment_skips_title_page(make_text_block, make_parsed_page, make_parsed_pdf):
    blocks = [
        make_text_block(text="Текст " * 12, is_bold=False, bbox=(85, 100, 360, 114)),
        make_text_block(text="Текст " * 12, is_bold=False, bbox=(85, 130, 510, 144)),
        make_text_block(text="Текст " * 12, is_bold=False, bbox=(85, 160, 350, 174)),
    ]
    page = make_parsed_page(
        lines=[
            "Министерство науки и высшего образования Российской Федерации",
            "Университет ИТМО",
            "Факультет программной инженерии",
        ],
        text_blocks=blocks,
    )
    results = await AlignmentRule().check(make_parsed_pdf(pages=[page]), {})
    assert results[0].status == CheckStatus.PASSED
