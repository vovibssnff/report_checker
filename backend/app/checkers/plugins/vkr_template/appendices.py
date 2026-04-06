from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from app.checkers.base import BaseRule, RuleResult, rule
from app.core.domain.value_objects import CheckStatus, DocumentType, Severity

if TYPE_CHECKING:
    from app.checkers.pdf_parser import ParsedPDF, ParsedPage, TextBlock

_APPENDIX_PATTERN = re.compile(r"\bприложение\b(?:\s+|[:.\-–—]+)([а-яёА-ЯЁ])\b", re.IGNORECASE)
_VALID_LABELS = "АБВГДЕЖИКЛМНПРСТУФХЦШЩЭЮЯ"
_NON_WORD_RE = re.compile(r"[^a-zа-я0-9]+", re.IGNORECASE)
_SPACED_LETTERS_RE = re.compile(r"\b(?:[a-zа-я]\s+){2,}[a-zа-я]\b", re.IGNORECASE)
_CENTER_TOLERANCE_PT = 35
_MAX_HEADING_TOKENS = 10


def _collapse_spaced_letters(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        return match.group(0).replace(" ", "")

    return _SPACED_LETTERS_RE.sub(repl, text)


def _normalize_for_search(text: str) -> str:
    collapsed = _collapse_spaced_letters(text)
    normalized = _NON_WORD_RE.sub(" ", collapsed.lower().replace("ё", "е"))
    return " ".join(normalized.split())


def _is_uppercase_heading(text: str) -> bool:
    letters = [ch for ch in text if ch.isalpha()]
    if not letters:
        return False
    return "".join(letters) == "".join(letters).upper()


def _is_centered(block: TextBlock, page: ParsedPage) -> bool:
    page_center_pt = page.width_mm / (1 / 2.835) / 2
    block_center = (block.bbox[0] + block.bbox[2]) / 2
    return abs(block_center - page_center_pt) <= _CENTER_TOLERANCE_PT


def _is_appendix_heading_candidate(text: str, *, source: str, is_uppercase: bool, is_centered: bool | None) -> bool:
    normalized = _normalize_for_search(text)
    if not normalized:
        return False
    if not normalized.startswith("приложение"):
        return False

    tokens = normalized.split()
    if len(tokens) > _MAX_HEADING_TOKENS:
        return False

    if source == "heading":
        return True
    if source == "block":
        return is_uppercase and bool(is_centered)
    if source == "line":
        return is_uppercase and len(tokens) <= 6
    return False


@rule(
    code="vkr.appendices.labeling",
    name="Обозначение приложений",
    document_type=DocumentType.VKR_TEMPLATE,
    severity=Severity.WARNING,
    description="Проверка обозначения приложений буквами (А, Б, В...)",
)
class AppendixLabelingRule(BaseRule):
    async def check(self, pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
        found_labels: list[str] = []
        page_map = {p.number: p for p in pdf.pages}
        candidates: list[dict[str, Any]] = []
        for page in pdf.pages:
            for line in page.lines:
                raw = line.strip()
                if not raw:
                    continue
                candidates.append(
                    {"source": "line", "text": raw, "is_uppercase": _is_uppercase_heading(raw), "is_centered": None}
                )
            for block in page.text_blocks:
                raw = block.text.strip()
                if not raw:
                    continue
                candidates.append(
                    {
                        "source": "block",
                        "text": raw,
                        "is_uppercase": _is_uppercase_heading(raw),
                        "is_centered": _is_centered(block, page),
                    }
                )
        for heading in pdf.headings:
            raw = heading.text.strip()
            if not raw:
                continue
            page = page_map.get(heading.page_number)
            center_ok: bool | None = None
            if page:
                matched_block = next((b for b in page.text_blocks if b.text.strip() == raw), None)
                if matched_block:
                    center_ok = _is_centered(matched_block, page)
            candidates.append(
                {"source": "heading", "text": raw, "is_uppercase": _is_uppercase_heading(raw), "is_centered": center_ok}
            )

        for candidate in candidates:
            if not _is_appendix_heading_candidate(
                candidate["text"],
                source=candidate["source"],
                is_uppercase=candidate["is_uppercase"],
                is_centered=candidate["is_centered"],
            ):
                continue

            text = _normalize_for_search(candidate["text"])
            if not text:
                continue
            match = _APPENDIX_PATTERN.search(text)
            if not match:
                # Fallback for cases like "ПРИЛОЖЕНИЕА" from odd extraction.
                merged = text.replace(" ", "")
                match = re.search(r"приложение([а-я])\b", merged, re.IGNORECASE)
                if match:
                    found_labels.append(match.group(1).upper())

        if not found_labels:
            return [
                RuleResult(
                    status=CheckStatus.PASSED,
                    message="appendices_not_found",
                )
            ]

        issues: list[dict[str, Any]] = []
        for i, label in enumerate(found_labels):
            if label not in _VALID_LABELS:
                issues.append({"type": "invalid_label", "label": label})
            elif i < len(_VALID_LABELS):
                expected = _VALID_LABELS[i]
                if label != expected:
                    issues.append({"type": "wrong_order", "expected": expected, "found": label})

        if issues:
            return [
                RuleResult(
                    status=CheckStatus.FAILED,
                    message="appendices_labeling_invalid",
                    details={"found_labels": found_labels, "issues": issues},
                )
            ]
        return [
            RuleResult(
                status=CheckStatus.PASSED,
                message="appendices_labeling_ok",
            )
        ]
