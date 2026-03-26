from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from app.checkers.base import BaseRule, RuleResult, rule
from app.core.domain.value_objects import CheckStatus, DocumentType, Severity

if TYPE_CHECKING:
    from app.checkers.pdf_parser import ParsedPDF

_TABLE_PATTERN = re.compile(r"таблица\s+(\d+(?:\.\d+)*)\s*[—–\-]\s*\S", re.IGNORECASE)
_TABLE_MENTION = re.compile(r"таблица\s+(\d+(?:\.\d+)*)", re.IGNORECASE)


@rule(
    code="vkr.tables.caption_format",
    name="Формат подписей таблиц",
    document_type=DocumentType.VKR_TEMPLATE,
    severity=Severity.ERROR,
    description="Проверка формата подписей таблиц (Таблица N — Название)",
)
class TableCaptionFormatRule(BaseRule):
    async def check(self, pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
        bad_captions: list[dict[str, Any]] = []

        for page in pdf.pages:
            for block in page.text_blocks:
                text = block.text.strip()
                if not text:
                    continue
                mention = _TABLE_MENTION.search(text)
                if not mention:
                    continue
                if not _TABLE_PATTERN.search(text):
                    x0, top, x1, bottom = block.bbox
                    bad_captions.append(
                        {
                            "page": page.number,
                            "text": text,
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
                    message="table_caption_invalid",
                    details={"bad_captions": bad_captions, "pages": pages, "count": len(bad_captions)},
                )
            ]
        return [
            RuleResult(
                status=CheckStatus.PASSED,
                message="table_caption_ok",
            )
        ]


@rule(
    code="vkr.tables.numbering",
    name="Нумерация таблиц",
    document_type=DocumentType.VKR_TEMPLATE,
    severity=Severity.WARNING,
    description="Проверка последовательной нумерации таблиц",
)
class TableNumberingRule(BaseRule):
    async def check(self, pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
        numbers: list[int] = []

        for page in pdf.pages:
            for line in page.lines:
                for match in _TABLE_PATTERN.finditer(line):
                    num_str = match.group(1)
                    parts = num_str.split(".")
                    numbers.append(int(parts[-1]))

        if not numbers:
            return [
                RuleResult(
                    status=CheckStatus.PASSED,
                    message="tables_not_found",
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
                    message="table_numbering_invalid",
                    details={"found_numbers": numbers, "gaps_at": gaps},
                )
            ]
        return [
            RuleResult(
                status=CheckStatus.PASSED,
                message="table_numbering_ok",
            )
        ]
