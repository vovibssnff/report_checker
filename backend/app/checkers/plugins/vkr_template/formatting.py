from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING, Any

from app.checkers.base import BaseRule, RuleResult, rule
from app.core.domain.value_objects import CheckStatus, DocumentType, Severity

if TYPE_CHECKING:
    from app.checkers.pdf_parser import ParsedPDF

_PTS_TO_MM = 1 / 2.835


@rule(
    code="vkr.formatting.page_size",
    name="Формат страницы А4",
    document_type=DocumentType.VKR_TEMPLATE,
    severity=Severity.ERROR,
    description="Проверка формата страницы (А4, 210×297 мм)",
    default_config={"tolerance_mm": 5},
)
class PageSizeRule(BaseRule):
    async def check(self, pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
        tolerance = config.get("tolerance_mm", 5)
        bad_pages: list[int] = []
        for page in pdf.pages:
            if abs(page.width_mm - 210) > tolerance or abs(page.height_mm - 297) > tolerance:
                bad_pages.append(page.number)

        if bad_pages:
            return [
                RuleResult(
                    status=CheckStatus.FAILED,
                    message=f"Страницы не соответствуют формату А4: {bad_pages}",
                    details={"pages": bad_pages},
                )
            ]
        return [RuleResult(status=CheckStatus.PASSED, message="Все страницы формата А4")]


@rule(
    code="vkr.formatting.margins",
    name="Поля страницы",
    document_type=DocumentType.VKR_TEMPLATE,
    severity=Severity.ERROR,
    description="Проверка размеров полей (левое 30мм, правое 15мм, верх/низ 20мм)",
    default_config={
        "left_mm": 30,
        "right_mm": 15,
        "top_mm": 20,
        "bottom_mm": 20,
        "tolerance_mm": 5,
    },
)
class MarginsRule(BaseRule):
    async def check(self, pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
        left_expected = config.get("left_mm", 30)
        right_expected = config.get("right_mm", 15)
        top_expected = config.get("top_mm", 20)
        bottom_expected = config.get("bottom_mm", 20)
        tolerance = config.get("tolerance_mm", 5)

        violations: list[dict[str, Any]] = []
        for page in pdf.pages:
            if not page.text_blocks:
                continue
            page_w_pt = page.width_mm / _PTS_TO_MM
            page_h_pt = page.height_mm / _PTS_TO_MM

            min_x0 = min(tb.bbox[0] for tb in page.text_blocks)
            max_x1 = max(tb.bbox[2] for tb in page.text_blocks)
            min_top = min(tb.bbox[1] for tb in page.text_blocks)
            max_bottom = max(tb.bbox[3] for tb in page.text_blocks)

            left_mm = min_x0 * _PTS_TO_MM
            right_mm = (page_w_pt - max_x1) * _PTS_TO_MM
            top_mm = min_top * _PTS_TO_MM
            bottom_mm = (page_h_pt - max_bottom) * _PTS_TO_MM

            issues: list[str] = []
            if abs(left_mm - left_expected) > tolerance:
                issues.append(f"левое {left_mm:.1f}мм")
            if abs(right_mm - right_expected) > tolerance:
                issues.append(f"правое {right_mm:.1f}мм")
            if abs(top_mm - top_expected) > tolerance:
                issues.append(f"верхнее {top_mm:.1f}мм")
            if abs(bottom_mm - bottom_expected) > tolerance:
                issues.append(f"нижнее {bottom_mm:.1f}мм")

            if issues:
                violations.append({"page": page.number, "issues": issues})

        if violations:
            pages = [v["page"] for v in violations]
            return [
                RuleResult(
                    status=CheckStatus.FAILED,
                    message=f"Неверные поля на страницах: {pages}",
                    details={"violations": violations},
                )
            ]
        return [RuleResult(status=CheckStatus.PASSED, message="Поля соответствуют требованиям")]


@rule(
    code="vkr.formatting.font",
    name="Шрифт основного текста",
    document_type=DocumentType.VKR_TEMPLATE,
    severity=Severity.ERROR,
    description="Проверка основного шрифта (Times New Roman, ≥12pt)",
    default_config={"expected_font": "Times", "min_size": 12},
)
class FontRule(BaseRule):
    async def check(self, pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
        expected_font = config.get("expected_font", "Times")
        min_size = config.get("min_size", 12)

        results: list[RuleResult] = []
        font_counts: Counter[str] = Counter()
        small_font_pages: set[int] = set()

        for page in pdf.pages:
            for tb in page.text_blocks:
                font_counts[tb.font_name] += len(tb.text)
                if tb.font_size < min_size - 0.5 and len(tb.text.strip()) > 3:
                    small_font_pages.add(page.number)

        if font_counts:
            dominant_font = font_counts.most_common(1)[0][0]
            if expected_font.lower() not in dominant_font.lower():
                results.append(
                    RuleResult(
                        status=CheckStatus.FAILED,
                        message=f"Основной шрифт '{dominant_font}' вместо '{expected_font}'",
                        details={"dominant_font": dominant_font, "expected": expected_font},
                    )
                )

        if small_font_pages:
            results.append(
                RuleResult(
                    status=CheckStatus.FAILED,
                    message=f"Размер шрифта менее {min_size}pt на страницах: {sorted(small_font_pages)}",
                    details={"pages": sorted(small_font_pages)},
                )
            )

        if not results:
            results.append(
                RuleResult(
                    status=CheckStatus.PASSED,
                    message="Шрифт соответствует требованиям",
                )
            )
        return results


@rule(
    code="vkr.formatting.line_spacing",
    name="Межстрочный интервал",
    document_type=DocumentType.VKR_TEMPLATE,
    severity=Severity.WARNING,
    description="Проверка межстрочного интервала (1.5)",
    default_config={"expected_spacing": 1.5, "tolerance": 0.3},
)
class LineSpacingRule(BaseRule):
    async def check(self, pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
        expected = config.get("expected_spacing", 1.5)
        tolerance = config.get("tolerance", 0.3)
        bad_pages: list[int] = []

        for page in pdf.pages:
            blocks = sorted(page.text_blocks, key=lambda b: (b.bbox[1], b.bbox[0]))
            spacings: list[float] = []
            for i in range(len(blocks) - 1):
                cur = blocks[i]
                nxt = blocks[i + 1]
                if abs(cur.bbox[0] - nxt.bbox[0]) > 50:
                    continue
                dy = nxt.bbox[1] - cur.bbox[1]
                if cur.font_size > 0 and 0 < dy < cur.font_size * 4:
                    spacings.append(dy / cur.font_size)

            if spacings:
                avg = sum(spacings) / len(spacings)
                if abs(avg - expected) > tolerance:
                    bad_pages.append(page.number)

        if bad_pages:
            return [
                RuleResult(
                    status=CheckStatus.FAILED,
                    message=f"Межстрочный интервал не соответствует {expected} на страницах: {bad_pages}",
                    details={"pages": bad_pages},
                )
            ]
        return [
            RuleResult(
                status=CheckStatus.PASSED,
                message="Межстрочный интервал соответствует требованиям",
            )
        ]


@rule(
    code="vkr.formatting.paragraph_indent",
    name="Абзацный отступ",
    document_type=DocumentType.VKR_TEMPLATE,
    severity=Severity.WARNING,
    description="Проверка абзацного отступа (1.25 см)",
    default_config={"indent_mm": 12.5, "tolerance_mm": 3},
)
class ParagraphIndentRule(BaseRule):
    async def check(self, pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
        indent_mm = config.get("indent_mm", 12.5)
        tolerance_mm = config.get("tolerance_mm", 3)
        indent_pt = indent_mm / _PTS_TO_MM
        tolerance_pt = tolerance_mm / _PTS_TO_MM
        bad_pages: list[int] = []

        for page in pdf.pages:
            blocks = sorted(page.text_blocks, key=lambda b: (b.bbox[1], b.bbox[0]))
            if len(blocks) < 3:
                continue

            body_x0_values = [b.bbox[0] for b in blocks]
            base_x0 = min(body_x0_values)

            indented_count = 0
            total_paragraphs = 0

            for i, block in enumerate(blocks):
                is_new_paragraph = i == 0 or (blocks[i].bbox[1] - blocks[i - 1].bbox[3]) > blocks[i - 1].font_size * 0.5
                if not is_new_paragraph:
                    continue
                if len(block.text.strip()) < 5:
                    continue
                total_paragraphs += 1
                offset = block.bbox[0] - base_x0
                if abs(offset - indent_pt) < tolerance_pt:
                    indented_count += 1

            if total_paragraphs > 2 and indented_count < total_paragraphs * 0.5:
                bad_pages.append(page.number)

        if bad_pages:
            return [
                RuleResult(
                    status=CheckStatus.FAILED,
                    message=f"Абзацный отступ не обнаружен на страницах: {bad_pages}",
                    details={"pages": bad_pages},
                )
            ]
        return [
            RuleResult(
                status=CheckStatus.PASSED,
                message="Абзацный отступ соответствует требованиям",
            )
        ]


@rule(
    code="vkr.formatting.alignment",
    name="Выравнивание текста",
    document_type=DocumentType.VKR_TEMPLATE,
    severity=Severity.WARNING,
    description="Проверка выравнивания текста по ширине",
)
class AlignmentRule(BaseRule):
    async def check(self, pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
        bad_pages: list[int] = []

        for page in pdf.pages:
            if not page.text_blocks:
                continue
            long_blocks = [tb for tb in page.text_blocks if len(tb.text.strip()) > 30 and not tb.is_bold]
            if len(long_blocks) < 3:
                continue

            right_edges = [tb.bbox[2] for tb in long_blocks]
            max_right = max(right_edges)
            aligned_count = sum(1 for r in right_edges if abs(r - max_right) < 10)
            if aligned_count < len(right_edges) * 0.6:
                bad_pages.append(page.number)

        if bad_pages:
            return [
                RuleResult(
                    status=CheckStatus.FAILED,
                    message=f"Текст не выровнен по ширине на страницах: {bad_pages}",
                    details={"pages": bad_pages},
                )
            ]
        return [RuleResult(status=CheckStatus.PASSED, message="Текст выровнен по ширине")]
