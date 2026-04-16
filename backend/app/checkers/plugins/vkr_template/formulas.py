from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from app.checkers.base import BaseRule, RuleResult, rule
from app.core.domain.value_objects import CheckStatus, DocumentType, Severity

if TYPE_CHECKING:
    from app.checkers.pdf_parser import ParsedPDF

_FORMULA_NUMBER = re.compile(r"\((\d+(?:\.\d+)*)\)\s*$")
_MATH_OPERATOR = re.compile(r"(=|[+\-*/^]|[<>≤≥±×÷])")
_FUNCTION_CALL = re.compile(r"\b[а-яa-z]\s*\([^)]{1,40}\)", re.IGNORECASE)


def _looks_like_formula_prefix(prefix: str) -> bool:
    text = prefix.strip()
    if not text:
        return False
    if _MATH_OPERATOR.search(text):
        return True
    # Accept function-like expressions such as f(x), g(t), phi(n).
    return bool(_FUNCTION_CALL.search(text))


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
        misaligned_numbers: list[dict[str, Any]] = []

        for page in pdf.pages:
            page_w_pt = page.width_mm / (1 / 2.835)
            for line in page.lines:
                match = _FORMULA_NUMBER.search(line)
                if match:
                    prefix = line[: match.start()]
                    if not _looks_like_formula_prefix(prefix):
                        continue
                    expected_number = match.group(0)
                    matching_block = next((tb for tb in page.text_blocks if expected_number in tb.text), None)
                    if matching_block is not None and (page_w_pt - matching_block.bbox[2]) > 45:
                        misaligned_numbers.append(
                            {
                                "page": page.number,
                                "number": expected_number,
                                "right_offset": round(page_w_pt - matching_block.bbox[2], 2),
                            }
                        )
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
        if misaligned_numbers:
            return [
                RuleResult(
                    status=CheckStatus.FAILED,
                    message="formula_numbering_not_right_aligned",
                    details={"issues": misaligned_numbers},
                )
            ]
        return [
            RuleResult(
                status=CheckStatus.PASSED,
                message="formula_numbering_ok",
            )
        ]
