from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from app.checkers.base import BaseRule, RuleResult, rule
from app.core.domain.value_objects import CheckStatus, DocumentType, Severity

if TYPE_CHECKING:
    from app.checkers.pdf_parser import ParsedPDF

_PTS_TO_MM = 1 / 2.835

_STRUCTURAL_ELEMENTS = [
    "содержание",
    "введение",
    "заключение",
    "список использованных источников",
    "список литературы",
    "приложение",
]

_SECTION_NUMBER_RE = re.compile(r"^(\d+\.(?:\d+\.?)*)\s+")
_SECTION_NUMBER_MISSING_DOT_RE = re.compile(r"^(\d+)\s+")
_MAX_STRUCTURAL_TOKENS = 10
_NON_WORD_RE = re.compile(r"[^a-zа-я0-9]+", re.IGNORECASE)
_RIGHT_ALIGN_TOLERANCE_PT = 35


def _looks_like_structural_heading(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    lowered = stripped.lower().replace("ё", "е")
    normalized = " ".join(_NON_WORD_RE.sub(" ", lowered).split())
    tokens = normalized.split()
    if not tokens or len(tokens) > _MAX_STRUCTURAL_TOKENS:
        return False

    # Strict heading forms to avoid inline mentions inside sentences.
    if normalized in {"содержание", "оглавление", "введение", "заключение"}:
        return True
    if normalized in {"список литературы", "список использованных источников"}:
        return True
    if normalized.startswith("список использованных источников "):
        tail_tokens = normalized.split()[3:]
        return tail_tokens in (["и", "литературы"], ["и", "информационных", "источников"])
    if normalized.startswith("приложение"):
        # Accept appendix headings like "ПРИЛОЖЕНИЕ А" / "ПРИЛОЖЕНИЕ 1".
        return len(tokens) <= 3
    return False


def _is_appendix_heading(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    lowered = stripped.lower().replace("ё", "е")
    normalized = " ".join(_NON_WORD_RE.sub(" ", lowered).split())
    return normalized.startswith("приложение")


@rule(
    code="vkr.headings.structural_elements",
    name="Оформление структурных элементов",
    document_type=DocumentType.VKR_TEMPLATE,
    severity=Severity.ERROR,
    description="Проверка центрирования и верхнего регистра структурных элементов",
)
class StructuralElementsRule(BaseRule):
    async def check(self, pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
        violations: list[dict[str, Any]] = []

        for page in pdf.pages:
            page_center_pt = page.width_mm / _PTS_TO_MM / 2
            for tb in page.text_blocks:
                text = tb.text.strip()
                if not _looks_like_structural_heading(text):
                    continue

                issues: list[str] = []
                if text != text.upper():
                    issues.append("not_uppercase")

                if _is_appendix_heading(text):
                    page_width_pt = page.width_mm / _PTS_TO_MM
                    right_offset = page_width_pt - tb.bbox[2]
                    if right_offset > _RIGHT_ALIGN_TOLERANCE_PT:
                        issues.append("not_right_aligned")
                else:
                    block_center = (tb.bbox[0] + tb.bbox[2]) / 2
                    if abs(block_center - page_center_pt) > 30:
                        issues.append("not_centered")

                if issues:
                    x0, top, x1, bottom = tb.bbox
                    violations.append(
                        {
                            "page": page.number,
                            "text": text,
                            "issues": issues,
                            "location": {
                                "x0": round(x0, 2),
                                "y0": round(top, 2),
                                "x1": round(x1, 2),
                                "y1": round(bottom, 2),
                            },
                        }
                    )

        if violations:
            return [
                RuleResult(
                    status=CheckStatus.FAILED,
                    message="structural_elements_invalid",
                    details={"violations": violations},
                )
            ]
        return [
            RuleResult(
                status=CheckStatus.PASSED,
                message="structural_elements_ok",
            )
        ]


@rule(
    code="vkr.headings.new_page",
    name="Начало разделов с новой страницы",
    document_type=DocumentType.VKR_TEMPLATE,
    severity=Severity.ERROR,
    description="Проверка что структурные элементы и главы начинаются с новой страницы",
)
class NewPageRule(BaseRule):
    async def check(self, pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
        violations: list[int] = []

        for page in pdf.pages:
            structural_block_top = float("inf")
            has_structural = False

            for tb in page.text_blocks:
                text = tb.text.strip()
                is_structural = _looks_like_structural_heading(text)
                is_chapter = bool(re.match(r"^\d+\s", tb.text.strip())) and tb.is_bold
                if is_structural or is_chapter:
                    has_structural = True
                    structural_block_top = min(structural_block_top, tb.bbox[1])

            if not has_structural:
                continue

            preceding_content = [
                tb
                for tb in page.text_blocks
                if tb.bbox[1] < structural_block_top - 5 and len(tb.text.strip()) > 2 and not tb.text.strip().isdigit()
            ]
            if preceding_content:
                violations.append(page.number)

        if violations:
            return [
                RuleResult(
                    status=CheckStatus.FAILED,
                    message="sections_not_new_page",
                    details={"pages": violations},
                )
            ]
        return [
            RuleResult(
                status=CheckStatus.PASSED,
                message="sections_new_page_ok",
            )
        ]


@rule(
    code="vkr.headings.section_numbering",
    name="Нумерация разделов",
    document_type=DocumentType.VKR_TEMPLATE,
    severity=Severity.WARNING,
    description="Проверка иерархической нумерации (1., 1.1, 1.1.1)",
)
class SectionNumberingRule(BaseRule):
    async def check(self, pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
        numbered_headings: list[tuple[str, int]] = []
        issues: list[dict[str, Any]] = []

        for page in pdf.pages:
            for tb in page.text_blocks:
                if not tb.is_bold:
                    continue
                stripped = tb.text.strip()
                missing_dot_match = _SECTION_NUMBER_MISSING_DOT_RE.match(stripped)
                if missing_dot_match:
                    issues.append({"type": "missing_dot_after_number", "number": missing_dot_match.group(1), "page": page.number})
                    continue

                match = _SECTION_NUMBER_RE.match(stripped)
                if match:
                    numbered_headings.append((match.group(1).rstrip("."), page.number))

        for heading in pdf.headings:
            stripped = heading.text.strip()
            missing_dot_match = _SECTION_NUMBER_MISSING_DOT_RE.match(stripped)
            if missing_dot_match:
                issues.append(
                    {"type": "missing_dot_after_number", "number": missing_dot_match.group(1), "page": heading.page_number}
                )
                continue

            match = _SECTION_NUMBER_RE.match(stripped)
            if match:
                num = match.group(1).rstrip(".")
                if not any(h[0] == num for h in numbered_headings):
                    numbered_headings.append((num, heading.page_number))

        if not numbered_headings and not issues:
            return [
                RuleResult(
                    status=CheckStatus.PASSED,
                    message="section_numbering_none",
                )
            ]

        prev_parts: list[int] = []

        for num_str, page_num in numbered_headings:
            parts = [int(p) for p in num_str.split(".") if p]
            level = len(parts)

            if level == 1:
                if prev_parts and prev_parts[0] + 1 != parts[0] and parts[0] != 1:
                    issues.append({"type": "wrong_number", "number": num_str, "page": page_num})
            elif level >= 2 and prev_parts and len(prev_parts) < level - 1:
                issues.append({"type": "skipped_level", "number": num_str, "page": page_num})

            prev_parts = parts

        if issues:
            return [
                RuleResult(
                    status=CheckStatus.FAILED,
                    message="section_numbering_invalid",
                    details={"issues": issues},
                )
            ]
        return [RuleResult(status=CheckStatus.PASSED, message="section_numbering_ok")]
