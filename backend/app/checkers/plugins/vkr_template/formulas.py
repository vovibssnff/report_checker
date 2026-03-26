from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from app.checkers.base import BaseRule, RuleResult, rule
from app.core.domain.value_objects import CheckStatus, DocumentType, Severity

if TYPE_CHECKING:
    from app.checkers.pdf_parser import ParsedPDF

_FORMULA_NUMBER = re.compile(r"\((\d+(?:\.\d+)*)\)\s*$")


@rule(
    code="vkr.formulas.numbering",
    name="Нумерация формул",
    document_type=DocumentType.VKR_TEMPLATE,
    severity=Severity.WARNING,
    description="Проверка нумерации формул в скобках",
)
class FormulaNumberingRule(BaseRule):
    async def check(self, pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
        numbers: list[int] = []

        for page in pdf.pages:
            for line in page.lines:
                match = _FORMULA_NUMBER.search(line)
                if match:
                    parts = match.group(1).split(".")
                    numbers.append(int(parts[-1]))

        if not numbers:
            return [
                RuleResult(
                    status=CheckStatus.PASSED,
                    message="formulas_not_found",
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
                    message="formula_numbering_invalid",
                    details={"found_numbers": numbers, "gaps_at": gaps},
                )
            ]
        return [
            RuleResult(
                status=CheckStatus.PASSED,
                message="formula_numbering_ok",
            )
        ]
