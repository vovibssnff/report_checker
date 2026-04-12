from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from app.checkers.base import BaseRule, RuleResult, rule
from app.core.domain.value_objects import CheckStatus, DocumentType, Severity

if TYPE_CHECKING:
    from app.checkers.pdf_parser import ParsedPDF

_TABLE_PATTERN = re.compile(r"таблица\s+(\d+(?:\.\d+)*)\s*[—–\-]\s*\S", re.IGNORECASE)
_TABLE_MENTION = re.compile(r"таблица\s+(\d+(?:\.\d+)*)", re.IGNORECASE)
_NON_WORD_RE = re.compile(r"[^a-zа-я0-9]+", re.IGNORECASE)
_SPACED_LETTERS_RE = re.compile(r"\b(?:[a-zа-я]\s+){2,}[a-zа-я]\b", re.IGNORECASE)


def _collapse_spaced_letters(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        return match.group(0).replace(" ", "")

    return _SPACED_LETTERS_RE.sub(repl, text)


def _normalize_for_search(text: str) -> str:
    collapsed = _collapse_spaced_letters(text)
    normalized = _NON_WORD_RE.sub(" ", collapsed.lower().replace("ё", "е"))
    return " ".join(normalized.split())


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
                issues: list[str] = []
                if not _TABLE_PATTERN.search(text):
                    issues.append("format")
                if text.rstrip().endswith("."):
                    issues.append("caption_ends_with_period")
                page_width_pt = page.width_mm / (1 / 2.835)
                block_center = (block.bbox[0] + block.bbox[2]) / 2
                if abs(block_center - page_width_pt / 2) < 30:
                    issues.append("centered_instead_of_left")
                if block.bbox[0] > 120:
                    issues.append("has_paragraph_indent")
                has_table_below = any(tb.bbox[1] >= block.bbox[3] for tb in page.tables)
                if not has_table_below:
                    issues.append("caption_not_above_table")
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
        has_layout_tables = any(page.tables for page in pdf.pages)

        for page in pdf.pages:
            searchable_texts = [*page.lines, *(tb.text for tb in page.text_blocks)]
            for raw_text in searchable_texts:
                text = _normalize_for_search(raw_text)
                for match in _TABLE_MENTION.finditer(text):
                    num_str = match.group(1)
                    parts = num_str.split(".")
                    numbers.append(int(parts[-1]))

        if not numbers:
            if has_layout_tables:
                return [
                    RuleResult(
                        status=CheckStatus.PASSED,
                        message="table_numbering_ok",
                        details={"detected_tables": sum(len(page.tables) for page in pdf.pages)},
                    )
                ]
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
