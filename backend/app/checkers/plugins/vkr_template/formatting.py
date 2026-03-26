from __future__ import annotations

from collections import Counter
from itertools import groupby
from typing import TYPE_CHECKING, Any

from app.checkers.base import BaseRule, RuleResult, rule
from app.core.domain.value_objects import CheckStatus, DocumentType, Severity

if TYPE_CHECKING:
    from app.checkers.pdf_parser import ParsedPDF

_PTS_TO_MM = 1 / 2.835


def _merge_nearby_locations(
    locations: list[dict[str, Any]],
    max_gap_chars: float = 4,
    avg_char_width_factor: float = 0.55,
) -> list[dict[str, Any]]:
    """Merge adjacent small-font locations on the same line.

    Two blocks are merged when they share the same page, overlap vertically
    (same line), and the horizontal gap between them is at most
    ``max_gap_chars`` average character widths (covers a space or one short
    word / number between them).
    """
    if not locations:
        return locations

    locations_sorted = sorted(locations, key=lambda e: (e["page"], e["location"]["y0"]))

    merged: list[dict[str, Any]] = []
    for _page, page_iter in groupby(locations_sorted, key=lambda e: e["page"]):
        page_items = list(page_iter)

        lines: list[list[dict[str, Any]]] = []
        for item in sorted(page_items, key=lambda e: e["location"]["y0"]):
            loc = item["location"]
            placed = False
            for line in lines:
                ref = line[0]["location"]
                v_overlap = min(loc["y1"], ref["y1"]) - max(loc["y0"], ref["y0"])
                height = min(loc["y1"] - loc["y0"], ref["y1"] - ref["y0"])
                if height > 0 and v_overlap / height > 0.5:
                    line.append(item)
                    placed = True
                    break
            if not placed:
                lines.append([item])

        for line in lines:
            line.sort(key=lambda e: e["location"]["x0"])
            cur = line[0]
            for nxt in line[1:]:
                gap = nxt["location"]["x0"] - cur["location"]["x1"]
                font_sz = cur.get("font_size") or nxt.get("font_size") or 12
                threshold = max_gap_chars * font_sz * avg_char_width_factor
                if gap <= threshold:
                    cur = {
                        "page": cur["page"],
                        "text": (cur["text"] + " " + nxt["text"])[:120],
                        "font_size": min(cur.get("font_size", 12), nxt.get("font_size", 12)),
                        "location": {
                            "x0": min(cur["location"]["x0"], nxt["location"]["x0"]),
                            "y0": min(cur["location"]["y0"], nxt["location"]["y0"]),
                            "x1": max(cur["location"]["x1"], nxt["location"]["x1"]),
                            "y1": max(cur["location"]["y1"], nxt["location"]["y1"]),
                        },
                    }
                else:
                    merged.append(cur)
                    cur = nxt
            merged.append(cur)

    return merged


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
                    message="page_size_mismatch",
                    details={"pages": bad_pages},
                )
            ]
        return [RuleResult(status=CheckStatus.PASSED, message="page_size_ok")]


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
        small_font_locations: list[dict[str, Any]] = []

        for page in pdf.pages:
            for tb in page.text_blocks:
                font_counts[tb.font_name] += len(tb.text)
                if tb.font_size < min_size - 0.5 and len(tb.text.strip()) > 3:
                    small_font_pages.add(page.number)
                    x0, top, x1, bottom = tb.bbox
                    small_font_locations.append({
                        "page": page.number,
                        "text": tb.text.strip()[:80],
                        "font_size": round(tb.font_size, 1),
                        "location": {
                            "x0": round(x0, 2),
                            "y0": round(top, 2),
                            "x1": round(x1, 2),
                            "y1": round(bottom, 2),
                        },
                    })

        small_font_locations = _merge_nearby_locations(small_font_locations)

        if font_counts:
            dominant_font = font_counts.most_common(1)[0][0]
            if expected_font.lower() not in dominant_font.lower():
                results.append(
                    RuleResult(
                        status=CheckStatus.FAILED,
                        message="font_mismatch",
                        details={"dominant_font": dominant_font, "expected": expected_font},
                    )
                )

        if small_font_pages:
            results.append(
                RuleResult(
                    status=CheckStatus.FAILED,
                    message="font_size_small",
                    details={
                        "pages": sorted(small_font_pages),
                        "min_size": min_size,
                        "locations": small_font_locations,
                    },
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
    code="vkr.formatting.line_spacing",
    name="Межстрочный интервал",
    document_type=DocumentType.VKR_TEMPLATE,
    severity=Severity.ERROR,
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
        bad_indent_locations: list[dict[str, Any]] = []

        for page in pdf.pages:
            blocks = sorted(page.text_blocks, key=lambda b: (b.bbox[1], b.bbox[0]))
            if len(blocks) < 3:
                continue

            body_x0_values = [b.bbox[0] for b in blocks]
            base_x0 = min(body_x0_values)

            indented_count = 0
            total_paragraphs = 0
            page_bad: list[dict[str, Any]] = []

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
                else:
                    x0, top, x1, bottom = block.bbox
                    page_bad.append({
                        "page": page.number,
                        "text": block.text.strip()[:80],
                        "location": {
                            "x0": round(x0, 2),
                            "y0": round(top, 2),
                            "x1": round(x1, 2),
                            "y1": round(bottom, 2),
                        },
                    })

            if total_paragraphs > 2 and indented_count < total_paragraphs * 0.5:
                bad_pages.append(page.number)
                bad_indent_locations.extend(page_bad)

        if bad_pages:
            return [
                RuleResult(
                    status=CheckStatus.FAILED,
                    message="paragraph_indent_missing",
                    details={"pages": bad_pages, "locations": bad_indent_locations},
                )
            ]
        return [
            RuleResult(
                status=CheckStatus.PASSED,
                message="paragraph_indent_ok",
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
        misaligned_locations: list[dict[str, Any]] = []

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
                for tb in long_blocks:
                    if abs(tb.bbox[2] - max_right) >= 10:
                        x0, top, x1, bottom = tb.bbox
                        misaligned_locations.append({
                            "page": page.number,
                            "text": tb.text.strip()[:80],
                            "location": {
                                "x0": round(x0, 2),
                                "y0": round(top, 2),
                                "x1": round(x1, 2),
                                "y1": round(bottom, 2),
                            },
                        })

        if bad_pages:
            return [
                RuleResult(
                    status=CheckStatus.FAILED,
                    message="alignment_invalid",
                    details={"pages": bad_pages, "locations": misaligned_locations},
                )
            ]
        return [RuleResult(status=CheckStatus.PASSED, message="alignment_ok")]
