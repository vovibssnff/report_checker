from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from app.checkers.base import RuleResult
from app.core.domain.value_objects import CheckStatus

if TYPE_CHECKING:
    from app.checkers.pdf_parser import ParsedPDF

# Leaders: ASCII dots, Unicode ellipsis, spaced dots (Word export), middle dots.
_LEADER_CHARS_RE = re.compile(r"(?:\.{2,}|…|(?:\s*\.){3,}|[·•]{2,})")
_PAGE_NUM_TAIL_RE = re.compile(r"\s+(\d{1,3})\s*$")


def _normalize_title(text: str) -> str:
    return " ".join(text.lower().replace("ё", "е").split())


def _line_ends_with_page_number(line: str) -> bool:
    return bool(_PAGE_NUM_TAIL_RE.search(line.strip()))


def _strip_page_number(line: str) -> str:
    return _PAGE_NUM_TAIL_RE.sub("", line.strip()).strip()


def looks_like_toc_entry_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if _line_ends_with_page_number(stripped) and _line_has_leader_or_gap(stripped):
        return True
    m = _LEADER_CHARS_RE.search(stripped)
    if not m or m.start() < 2:
        return False
    title_part = stripped[: m.start()].strip()
    if not title_part or len(title_part) > 120:
        return False
    return True


def _line_has_leader_or_gap(line: str) -> bool:
    """True if the line plausibly has a TOC leader before the page number.

    pdfplumber often omits dot leaders or merges them differently than Word shows;
    we accept dots, ellipsis, dot runs with spaces, and long gaps (tabs/spaces)
    between the title and the page number.
    """
    stripped = line.strip()
    num_m = re.search(r"(\d{1,3})\s*$", stripped)
    if not num_m:
        return False
    # Everything before the page number: title + leader (dots/spaces), not "title only"
    before_digits = stripped[: num_m.start()]
    if _LEADER_CHARS_RE.search(before_digits):
        return True
    gap_m = re.search(r"(\s+)$", before_digits)
    return bool(gap_m and len(gap_m.group(1)) >= 4)


def _extract_toc_title_from_entry_line(line: str) -> str:
    """Title text without leader and page number."""
    no_page = _strip_page_number(line)
    # Split off leader region (dots, ellipsis, long gap)
    parts = re.split(r"(?:\.{2,}|…|(?:\s*\.){3,}|[·•]{2,}|[\s\u00a0]{4,})", no_page, maxsplit=1)
    title = parts[0].strip() if parts else no_page
    return _normalize_title(title)


def _title_appears_in_body(title_norm: str, body_norm: str) -> bool:
    if not title_norm or len(title_norm) < 2:
        return True
    if title_norm in body_norm:
        return True
    # Long headings: prefix / first words (PDF text may truncate or differ slightly)
    if len(title_norm) > 50:
        prefix = title_norm[:48].rstrip()
        if prefix in body_norm:
            return True
    words = title_norm.split()
    if len(words) >= 3:
        snippet = " ".join(words[: min(5, len(words))])
        if snippet in body_norm:
            return True
    return False


async def check_toc_content(pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
    toc_page = next(
        (p for p in pdf.pages if any(line.strip().lower() in {"содержание", "оглавление"} for line in p.lines[:8])),
        None,
    )
    if toc_page is None:
        return [RuleResult(status=CheckStatus.FAILED, message="toc_missing")]

    issues: list[str] = []
    toc_lines = [line.strip() for line in toc_page.lines if line.strip()]
    entry_lines = [line for line in toc_lines if _line_ends_with_page_number(line)]
    if not entry_lines:
        issues.append("toc_entries_missing")

    if entry_lines:
        bad_leaders = [ln for ln in entry_lines if not _line_has_leader_or_gap(ln)]
        if bad_leaders:
            issues.append("toc_dotted_leaders_missing")

    # Match TOC entries to document body text (not pdf.headings: those are only bold/large blocks).
    body_text = " ".join(
        " ".join(p.lines) for p in pdf.pages if p.number != toc_page.number
    )
    body_norm = _normalize_title(body_text)

    toc_titles = [_extract_toc_title_from_entry_line(line) for line in entry_lines]
    toc_titles = [t for t in toc_titles if t and t not in {"содержание", "оглавление"}]

    check_count = min(3, len(toc_titles))
    # At least one of the first entries must appear in the body; avoids false failures when
    # one line differs slightly from extracted text while the TOC is still valid.
    if check_count > 0 and not any(_title_appears_in_body(t, body_norm) for t in toc_titles[:check_count]):
        issues.append("toc_titles_mismatch")

    if issues:
        return [RuleResult(status=CheckStatus.FAILED, message="toc_invalid", details={"issues": issues})]
    return [RuleResult(status=CheckStatus.PASSED, message="toc_ok")]
