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
            for line in page.lines:
                mention = _TABLE_MENTION.search(line)
                if not mention:
                    continue
                if not _TABLE_PATTERN.search(line):
                    bad_captions.append(
                        {
                            "page": page.number,
                            "text": line.strip(),
                        }
                    )

        if bad_captions:
            return [
                RuleResult(
                    status=CheckStatus.FAILED,
                    message=f"Неверный формат подписи таблиц ({len(bad_captions)} шт.)",
                    details={"bad_captions": bad_captions},
                )
            ]
        return [
            RuleResult(
                status=CheckStatus.PASSED,
                message="Подписи таблиц оформлены верно",
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
                    message="Таблицы не обнаружены",
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
                    message="Нарушена последовательность нумерации таблиц",
                    details={"found_numbers": numbers, "gaps_at": gaps},
                )
            ]
        return [
            RuleResult(
                status=CheckStatus.PASSED,
                message="Нумерация таблиц последовательна",
            )
        ]
