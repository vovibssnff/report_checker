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

_SECTION_NUMBER_RE = re.compile(r"^(\d+(?:\.\d+)*)\s+")


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
                text_lower = tb.text.strip().lower()
                if not any(elem in text_lower for elem in _STRUCTURAL_ELEMENTS):
                    continue

                issues: list[str] = []
                if tb.text.strip() != tb.text.strip().upper():
                    issues.append("not_uppercase")

                block_center = (tb.bbox[0] + tb.bbox[2]) / 2
                if abs(block_center - page_center_pt) > 30:
                    issues.append("not_centered")

                if issues:
                    x0, top, x1, bottom = tb.bbox
                    violations.append(
                        {
                            "page": page.number,
                            "text": tb.text.strip(),
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
                text_lower = tb.text.strip().lower()
                is_structural = any(elem in text_lower for elem in _STRUCTURAL_ELEMENTS)
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
    description="Проверка иерархической нумерации (1, 1.1, 1.1.1)",
)
class SectionNumberingRule(BaseRule):
    async def check(self, pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
        numbered_headings: list[tuple[str, int]] = []

        for page in pdf.pages:
            for tb in page.text_blocks:
                if not tb.is_bold:
                    continue
                match = _SECTION_NUMBER_RE.match(tb.text.strip())
                if match:
                    numbered_headings.append((match.group(1), page.number))

        for heading in pdf.headings:
            match = _SECTION_NUMBER_RE.match(heading.text.strip())
            if match:
                num = match.group(1)
                if not any(h[0] == num for h in numbered_headings):
                    numbered_headings.append((num, heading.page_number))

        if not numbered_headings:
            return [
                RuleResult(
                    status=CheckStatus.PASSED,
                    message="section_numbering_none",
                )
            ]

        issues: list[dict[str, Any]] = []
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
