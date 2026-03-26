from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.checkers.base import BaseRule, RuleResult, rule
from app.core.domain.value_objects import CheckStatus, DocumentType, Severity

if TYPE_CHECKING:
    from app.checkers.pdf_parser import ParsedPDF

_REQUIRED_SECTIONS = [
    ("title_page", ["титульный лист"]),
    ("task", ["задание"]),
    ("abstract", ["реферат", "аннотация"]),
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


@rule(
    code="vkr.structure.required_sections",
    name="Обязательные разделы ВКР",
    document_type=DocumentType.VKR_TEMPLATE,
    severity=Severity.ERROR,
    description="Проверка наличия и порядка обязательных разделов",
)
class RequiredSectionsRule(BaseRule):
    async def check(self, pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
        all_lines: list[str] = []
        for page in pdf.pages:
            all_lines.extend(line.strip().lower() for line in page.lines)
        heading_texts = [h.text.strip().lower() for h in pdf.headings]
        searchable = all_lines + heading_texts

        found_order: list[tuple[str, int]] = []
        missing: list[str] = []

        for section_code, keywords in _REQUIRED_SECTIONS:
            position = -1
            for kw in keywords:
                for i, line in enumerate(searchable):
                    if kw in line:
                        position = i
                        break
                if position >= 0:
                    break
            if position >= 0:
                found_order.append((section_code, position))
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

        order_violations: list[dict[str, str]] = []
        for i in range(len(found_order) - 1):
            if found_order[i][1] > found_order[i + 1][1]:
                order_violations.append({
                    "before": found_order[i][0],
                    "after": found_order[i + 1][0],
                })

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
