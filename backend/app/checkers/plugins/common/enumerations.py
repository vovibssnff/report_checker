from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from app.checkers.base import RuleResult
from app.core.domain.value_objects import CheckStatus

if TYPE_CHECKING:
    from app.checkers.pdf_parser import ParsedPDF


_ENUM_RE = re.compile(r"^\s*(—|[а-я]\)|\d+\))(\s+|\t+)", re.IGNORECASE)


async def check_enumerations_format(pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
    issues: list[dict[str, Any]] = []
    for page in pdf.pages:
        for line in page.lines:
            stripped = line.rstrip()
            if not stripped:
                continue
            match = _ENUM_RE.match(stripped)
            if not match:
                continue
            marker = match.group(1)
            gap = match.group(2)
            if "\t" in gap:
                issues.append({"page": page.number, "line": stripped[:120], "issue": "tab_after_marker"})
            invalid_markers = {"ё)", "з)", "й)", "о)", "ч)", "ъ)", "ы)", "ь)"}
            if marker != "—" and marker.endswith(")") and len(marker) == 2 and marker.lower() in invalid_markers:
                issues.append({"page": page.number, "line": stripped[:120], "issue": "invalid_russian_letter_marker"})

    if issues:
        return [RuleResult(status=CheckStatus.FAILED, message="enumerations_invalid", details={"issues": issues})]
    return [RuleResult(status=CheckStatus.PASSED, message="enumerations_ok")]
