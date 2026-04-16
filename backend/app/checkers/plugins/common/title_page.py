from __future__ import annotations

import re
from datetime import datetime
from typing import TYPE_CHECKING, Any

from app.checkers.base import RuleResult
from app.core.domain.value_objects import CheckStatus, DocumentType

if TYPE_CHECKING:
    from app.checkers.pdf_parser import ParsedPDF


_YEAR_RE = re.compile(r"\b(20\d{2})\b")


async def check_title_page_content(
    pdf: ParsedPDF, config: dict[str, Any], document_type: DocumentType
) -> list[RuleResult]:
    first_pages = pdf.pages[:2]
    text = " ".join(" ".join(page.lines) for page in first_pages).lower()
    expected_variants = (
        ["отчет о научно-исследовательской работе"]
        if document_type == DocumentType.VKR_TEMPLATE
        else ["отчет об учебной, ознакомительной практике", "отчет об учебной практике"]
    )

    issues: list[str] = []
    if not any(variant in text for variant in expected_variants):
        issues.append("invalid_work_type")

    year_matches = [int(m.group(1)) for m in _YEAR_RE.finditer(text)]
    current_year = datetime.now().year
    if not year_matches or current_year not in year_matches:
        issues.append("year_not_current")

    if issues:
        return [
            RuleResult(
                status=CheckStatus.FAILED,
                message="title_page_content_invalid",
                details={"issues": issues, "current_year": current_year},
            )
        ]
    return [RuleResult(status=CheckStatus.PASSED, message="title_page_content_ok")]
