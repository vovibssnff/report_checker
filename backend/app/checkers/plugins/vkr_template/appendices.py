from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from app.checkers.base import BaseRule, RuleResult, rule
from app.core.domain.value_objects import CheckStatus, DocumentType, Severity

if TYPE_CHECKING:
    from app.checkers.pdf_parser import ParsedPDF

_APPENDIX_PATTERN = re.compile(r"приложение\s+([а-яёА-ЯЁ])\b", re.IGNORECASE)
_VALID_LABELS = "АБВГДЕЖИКЛМНПРСТУФХЦШЩЭЮЯ"


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

        for page in pdf.pages:
            for line in page.lines:
                match = _APPENDIX_PATTERN.search(line)
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
