from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from app.checkers.base import BaseRule, RuleResult, rule
from app.core.domain.value_objects import CheckStatus, DocumentType, Severity

if TYPE_CHECKING:
    from app.checkers.pdf_parser import ParsedPage, ParsedPDF, TextBlock

_REQUIRED_SECTIONS = [
    ("title_page", ["титульный лист"]),
    ("task", ["задание"]),
    ("toc", ["содержание", "оглавление"]),
    ("introduction", ["введение"]),
    ("conclusion", ["заключение"]),
    (
        "references",
        [
            "список использованных источников",
            "список литературы",
            "библиография",
        ],
    ),
]

_TOP_LINES_PER_PAGE = 10
_CENTER_TOLERANCE_PT = 35
_NON_WORD_RE = re.compile(r"[^a-zа-я0-9]+", re.IGNORECASE)
_SPACED_LETTERS_RE = re.compile(r"\b(?:[a-zа-я]\s+){2,}[a-zа-я]\b", re.IGNORECASE)
_MAX_HEADING_TOKENS = 12
_TITLE_PAGE_MARKERS = [
    "министерство науки и высшего образования",
    "университет итмо",
    "факультет",
]


def _collapse_spaced_letters(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        return match.group(0).replace(" ", "")

    return _SPACED_LETTERS_RE.sub(repl, text)


def _normalize(text: str) -> str:
    collapsed = _collapse_spaced_letters(text)
    normalized = _NON_WORD_RE.sub(" ", collapsed.lower().replace("ё", "е"))
    return " ".join(normalized.split())


def _tokenize(text: str) -> set[str]:
    return set(_normalize(text).split())


def _is_uppercase_heading(text: str) -> bool:
    letters = [ch for ch in text if ch.isalpha()]
    if not letters:
        return False
    return "".join(letters) == "".join(letters).upper()


def _is_centered(block: TextBlock, page: ParsedPage) -> bool:
    page_center_pt = page.width_mm / (1 / 2.835) / 2
    block_center = (block.bbox[0] + block.bbox[2]) / 2
    return abs(block_center - page_center_pt) <= _CENTER_TOLERANCE_PT


def _section_match_score(text: str, aliases: list[str]) -> float:
    normalized_text = _normalize(text)
    if not normalized_text:
        return 0.0
    text_tokens = _tokenize(normalized_text)
    if not text_tokens:
        return 0.0

    best = 0.0
    for alias in aliases:
        normalized_alias = _normalize(alias)
        if not normalized_alias:
            continue
        if normalized_alias in normalized_text:
            return 1.0
        alias_tokens = _tokenize(normalized_alias)
        if not alias_tokens:
            continue
        overlap = len(text_tokens & alias_tokens)
        if overlap == 0:
            continue
        ratio = overlap / len(alias_tokens)
        if ratio >= 0.6:
            best = max(best, ratio)
    return best


def _looks_like_section_heading(entry: dict[str, Any]) -> bool:
    text = entry.get("text", "")
    normalized = _normalize(text)
    tokens = normalized.split()
    if not tokens or len(tokens) > _MAX_HEADING_TOKENS:
        return False

    # Parsed heading candidates are trusted as heading-like.
    if entry.get("source") == "heading":
        return True

    is_uppercase = bool(entry.get("is_uppercase"))
    is_centered = bool(entry.get("is_centered"))
    if is_uppercase and is_centered:
        return True

    # For line-based fallback, accept only very heading-like text.
    return bool(entry.get("source") == "line" and is_uppercase and len(tokens) <= 8)


def _is_first_meaningful_on_page(entry: dict[str, Any]) -> bool:
    if entry.get("source") == "marker":
        return True
    return int(entry.get("order", 9999)) == 0


def _title_page_marker_score(lines: list[str]) -> int:
    normalized_lines = [_normalize(line) for line in lines if line.strip()]
    line_blob = " ".join(normalized_lines)
    return sum(1 for marker in _TITLE_PAGE_MARKERS if marker in line_blob)


@rule(
    code="vkr.structure.required_sections",
    name="Обязательные разделы ВКР",
    document_type=DocumentType.VKR_TEMPLATE,
    severity=Severity.ERROR,
    description="Проверка наличия и порядка обязательных разделов",
)
class RequiredSectionsRule(BaseRule):
    async def check(self, pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
        candidate_entries: list[dict[str, Any]] = []
        page_map = {p.number: p for p in pdf.pages}

        for page in pdf.pages:
            sorted_blocks = sorted(page.text_blocks, key=lambda b: (b.bbox[1], b.bbox[0]))
            block_order = 0
            for block in sorted_blocks[:_TOP_LINES_PER_PAGE]:
                text = block.text.strip()
                if len(text) < 3:
                    continue
                candidate_entries.append(
                    {
                        "page": page.number,
                        "order": block_order,
                        "text": text,
                        "source": "block",
                        "is_uppercase": _is_uppercase_heading(text),
                        "is_centered": _is_centered(block, page),
                        "location": {
                            "x0": round(block.bbox[0], 2),
                            "y0": round(block.bbox[1], 2),
                            "x1": round(block.bbox[2], 2),
                            "y1": round(block.bbox[3], 2),
                        },
                    }
                )
                block_order += 1

            line_order = 0
            for line in page.lines[:_TOP_LINES_PER_PAGE]:
                text = line.strip()
                if len(text) < 3:
                    continue
                candidate_entries.append(
                    {
                        "page": page.number,
                        "order": line_order,
                        "text": text,
                        "source": "line",
                        "is_uppercase": _is_uppercase_heading(text),
                        "is_centered": None,
                        "location": None,
                    }
                )
                line_order += 1

        for heading in pdf.headings:
            text = heading.text.strip()
            if len(text) < 3:
                continue
            heading_page = page_map.get(heading.page_number)
            candidate_entries.append(
                {
                    "page": heading.page_number,
                    "order": 0,
                    "text": text,
                    "source": "heading",
                    "is_uppercase": _is_uppercase_heading(text),
                    "is_centered": None,
                    "location": None,
                }
            )
            if heading_page:
                matching_block = next((b for b in heading_page.text_blocks if b.text.strip() == text), None)
                if matching_block:
                    candidate_entries[-1]["is_centered"] = _is_centered(matching_block, heading_page)
                    candidate_entries[-1]["location"] = {
                        "x0": round(matching_block.bbox[0], 2),
                        "y0": round(matching_block.bbox[1], 2),
                        "x1": round(matching_block.bbox[2], 2),
                        "y1": round(matching_block.bbox[3], 2),
                    }

        found_order: list[tuple[str, int, dict[str, Any]]] = []
        missing: list[str] = []
        formatting_violations: list[dict[str, Any]] = []

        for section_code, keywords in _REQUIRED_SECTIONS:
            if section_code == "title_page":
                title_marker_hits: list[tuple[int, int]] = []
                for page in pdf.pages:
                    marker_score = _title_page_marker_score(page.lines)
                    if marker_score > 0:
                        position = page.number * 1000
                        title_marker_hits.append((position, marker_score))
                if title_marker_hits:
                    title_marker_hits.sort(key=lambda x: (x[0], -x[1]))
                    position, _marker_score = title_marker_hits[0]
                    found_order.append(
                        (
                            section_code,
                            position,
                            {
                                "page": position // 1000,
                                "text": "title_page_markers",
                                "source": "marker",
                                "is_uppercase": True,
                                "is_centered": True,
                                "location": None,
                            },
                        )
                    )
                    continue

            matched: list[tuple[int, float, dict[str, Any]]] = []
            for entry in candidate_entries:
                if not _is_first_meaningful_on_page(entry):
                    continue
                is_heading_like = _looks_like_section_heading(entry)
                if not is_heading_like and section_code != "title_page":
                    continue
                match_score = _section_match_score(entry["text"], keywords)
                if match_score <= 0:
                    continue
                absolute_position = entry["page"] * 1000 + entry["order"]
                matched.append((absolute_position, match_score, entry))

            if matched:
                matched.sort(key=lambda x: (x[0], -x[1]))
                position, _match_score, best = matched[0]
                found_order.append((section_code, position, best))

                has_style_data = best.get("is_uppercase") is not None and best.get("is_centered") is not None
                if has_style_data and (not best["is_uppercase"] or not best["is_centered"]):
                    issues: list[str] = []
                    if not best["is_uppercase"]:
                        issues.append("not_uppercase")
                    if not best["is_centered"]:
                        issues.append("not_centered")
                    formatting_violations.append(
                        {
                            "page": best["page"],
                            "text": best["text"],
                            "section": section_code,
                            "issues": issues,
                            "location": best.get("location"),
                        }
                    )
            else:
                missing.append(section_code)

        if missing:
            return [
                RuleResult(
                    status=CheckStatus.FAILED,
                    message="required_sections_missing",
                    details={"missing_sections": missing},
                )
            ]

        if formatting_violations:
            return [
                RuleResult(
                    status=CheckStatus.FAILED,
                    message="required_sections_format_invalid",
                    details={"violations": [v for v in formatting_violations if v.get("location")]},
                )
            ]

        order_violations: list[dict[str, str]] = []
        for i in range(len(found_order) - 1):
            if found_order[i][1] > found_order[i + 1][1]:
                order_violations.append(
                    {
                        "before": found_order[i][0],
                        "after": found_order[i + 1][0],
                    }
                )

        if order_violations:
            return [
                RuleResult(
                    status=CheckStatus.FAILED,
                    message="sections_order_invalid",
                    details={"order_violations": order_violations},
                )
            ]

        return [
            RuleResult(
                status=CheckStatus.PASSED,
                message="required_sections_ok",
            )
        ]
