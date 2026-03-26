from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING, Any

from app.checkers.base import BaseRule, RuleResult, rule
from app.core.domain.value_objects import CheckStatus, DocumentType, Severity

if TYPE_CHECKING:
    from app.checkers.pdf_parser import ParsedPDF

_PTS_TO_MM = 1 / 2.835


@rule(
    code="practice.formatting.page_size",
    name="Формат страницы А4",
    document_type=DocumentType.PRACTICE_REPORT,
    severity=Severity.ERROR,
    description="Проверка формата страницы (А4)",
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
                    message="page_size_mismatch",
                    details={"pages": bad_pages},
                )
            ]
        return [RuleResult(status=CheckStatus.PASSED, message="page_size_ok")]


@rule(
    code="practice.formatting.margins",
    name="Поля страницы",
    document_type=DocumentType.PRACTICE_REPORT,
    severity=Severity.ERROR,
    description="Проверка размеров полей",
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

            issues: list[dict[str, Any]] = []
            if abs(left_mm - left_expected) > tolerance:
                issues.append({"side": "left", "value_mm": round(left_mm, 1)})
            if abs(right_mm - right_expected) > tolerance:
                issues.append({"side": "right", "value_mm": round(right_mm, 1)})
            if abs(top_mm - top_expected) > tolerance:
                issues.append({"side": "top", "value_mm": round(top_mm, 1)})
            if abs(bottom_mm - bottom_expected) > tolerance:
                issues.append({"side": "bottom", "value_mm": round(bottom_mm, 1)})

            if issues:
                violations.append({"page": page.number, "issues": issues})

        if violations:
            pages = [v["page"] for v in violations]
            return [
                RuleResult(
                    status=CheckStatus.FAILED,
                    message="margins_invalid",
                    details={"violations": violations, "pages": pages},
                )
            ]
        return [RuleResult(status=CheckStatus.PASSED, message="margins_ok")]


@rule(
    code="practice.formatting.font",
    name="Шрифт основного текста",
    document_type=DocumentType.PRACTICE_REPORT,
    severity=Severity.ERROR,
    description="Проверка основного шрифта (Times New Roman)",
    default_config={"expected_font": "Times", "min_size": 12},
)
class FontRule(BaseRule):
    async def check(self, pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
        expected_font = config.get("expected_font", "Times")
        min_size = config.get("min_size", 12)

        font_counts: Counter[str] = Counter()
        small_pages: set[int] = set()

        for page in pdf.pages:
            for tb in page.text_blocks:
                font_counts[tb.font_name] += len(tb.text)
                if tb.font_size < min_size - 0.5 and len(tb.text.strip()) > 3:
                    small_pages.add(page.number)

        results: list[RuleResult] = []
        if font_counts:
            dominant = font_counts.most_common(1)[0][0]
            if expected_font.lower() not in dominant.lower():
                results.append(
                    RuleResult(
                        status=CheckStatus.FAILED,
                        message="font_mismatch",
                        details={"dominant_font": dominant, "expected": expected_font},
                    )
                )

        if small_pages:
            results.append(
                RuleResult(
                    status=CheckStatus.FAILED,
                    message="font_size_small",
                    details={"pages": sorted(small_pages), "min_size": min_size},
                )
            )

        if not results:
            results.append(
                RuleResult(
                    status=CheckStatus.PASSED,
                    message="font_ok",
                )
            )
        return results


@rule(
    code="practice.formatting.line_spacing",
    name="Межстрочный интервал",
    document_type=DocumentType.PRACTICE_REPORT,
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
                    message="line_spacing_mismatch",
                    details={"pages": bad_pages, "expected": expected},
                )
            ]
        return [
            RuleResult(
                status=CheckStatus.PASSED,
                message="line_spacing_ok",
            )
        ]
