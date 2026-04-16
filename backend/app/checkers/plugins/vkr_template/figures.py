from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from app.checkers.base import BaseRule, RuleResult, rule
from app.core.domain.value_objects import CheckStatus, DocumentType, Severity

if TYPE_CHECKING:
    from app.checkers.pdf_parser import ParsedPDF

_FIGURE_PATTERN = re.compile(r"рисунок\s+(\d+(?:\.\d+)*)\s*[—–\-]\s*\S", re.IGNORECASE)
_FIGURE_MENTION = re.compile(r"рисунок\s+(\d+(?:\.\d+)*)", re.IGNORECASE)


@rule(
    code="vkr.figures.caption_format",
    name="Формат подписей рисунков",
    document_type=DocumentType.VKR_TEMPLATE,
    severity=Severity.ERROR,
    description="Проверка формата подписей рисунков (Рисунок N — Название)",
)
class FigureCaptionFormatRule(BaseRule):
    async def check(self, pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
        bad_captions: list[dict[str, Any]] = []

        for page in pdf.pages:
            for block in page.text_blocks:
                text = block.text.strip()
                if not text:
                    continue

                mention = _FIGURE_MENTION.search(text)
                if not mention:
                    continue
                issues: list[str] = []
                if not _FIGURE_PATTERN.search(text):
                    issues.append("format")
                if text.rstrip().endswith("."):
                    issues.append("caption_ends_with_period")
                page_center = (page.width_mm / (1 / 2.835)) / 2
                block_center = (block.bbox[0] + block.bbox[2]) / 2
                if abs(block_center - page_center) > 30:
                    issues.append("not_centered")
                has_image_above = any(img.bbox[3] <= block.bbox[1] for img in page.images)
                if not has_image_above:
                    issues.append("caption_not_below_image")
                if issues:
                    x0, top, x1, bottom = block.bbox
                    bad_captions.append(
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

        if bad_captions:
            pages = sorted({item["page"] for item in bad_captions})
            return [
                RuleResult(
                    status=CheckStatus.FAILED,
                    message="figure_caption_invalid",
                    details={
                        "bad_captions": bad_captions,
                        "pages": pages,
                        "count": len(bad_captions),
                    },
                )
            ]
        return [
            RuleResult(
                status=CheckStatus.PASSED,
                message="figure_caption_ok",
            )
        ]


@rule(
    code="vkr.figures.numbering",
    name="Нумерация рисунков",
    document_type=DocumentType.VKR_TEMPLATE,
    severity=Severity.WARNING,
    description="Проверка последовательной нумерации рисунков",
)
class FigureNumberingRule(BaseRule):
    async def check(self, pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
        numbers: list[int] = []

        for page in pdf.pages:
            for line in page.lines:
                for match in _FIGURE_PATTERN.finditer(line):
                    num_str = match.group(1)
                    parts = num_str.split(".")
                    numbers.append(int(parts[-1]))

        if not numbers:
            return [
                RuleResult(
                    status=CheckStatus.PASSED,
                    message="figures_not_found",
                )
            ]

        gaps: list[int] = []
        for i in range(len(numbers) - 1):
            if numbers[i + 1] != numbers[i] + 1 and numbers[i + 1] != 1:
                gaps.append(numbers[i + 1])

        if gaps:
            return [
                RuleResult(
                    status=CheckStatus.FAILED,
                    message="figure_numbering_invalid",
                    details={"found_numbers": numbers, "gaps_at": gaps},
                )
            ]
        return [
            RuleResult(
                status=CheckStatus.PASSED,
                message="figure_numbering_ok",
            )
        ]
