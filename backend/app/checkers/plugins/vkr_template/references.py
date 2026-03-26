from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.checkers.base import BaseRule, RuleResult, rule
from app.core.domain.value_objects import CheckStatus, DocumentType, Severity

if TYPE_CHECKING:
    from app.checkers.pdf_parser import ParsedPDF

_BIBLIOGRAPHY_KEYWORDS = [
    "список использованных источников",
    "список литературы",
    "библиография",
    "список источников",
]


@rule(
    code="vkr.references.presence",
    name="Наличие списка литературы",
    document_type=DocumentType.VKR_TEMPLATE,
    severity=Severity.ERROR,
    description="Проверка наличия раздела со списком литературы",
)
class ReferencesPresenceRule(BaseRule):
    async def check(self, pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
        for page in pdf.pages:
            for line in page.lines:
                if any(kw in line.strip().lower() for kw in _BIBLIOGRAPHY_KEYWORDS):
                    return [
                        RuleResult(
                            status=CheckStatus.PASSED,
                            message="references_ok",
                        )
                    ]

        for heading in pdf.headings:
            if any(kw in heading.text.strip().lower() for kw in _BIBLIOGRAPHY_KEYWORDS):
                return [
                    RuleResult(
                        status=CheckStatus.PASSED,
                        message="references_ok",
                    )
                ]

        return [
            RuleResult(
                status=CheckStatus.FAILED,
                message="references_missing",
            )
        ]
