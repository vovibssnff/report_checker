from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.checkers.base import BaseRule, RuleResult, rule
from app.core.domain.value_objects import CheckStatus, DocumentType, Severity

if TYPE_CHECKING:
    from app.checkers.pdf_parser import ParsedPDF

_REQUIRED_SECTIONS = [
    ("титульный лист", ["титульный лист"]),
    ("задание", ["задание"]),
    ("реферат", ["реферат", "аннотация"]),
    ("содержание", ["содержание", "оглавление"]),
    ("введение", ["введение"]),
    ("заключение", ["заключение"]),
    (
        "список источников",
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

        for section_name, keywords in _REQUIRED_SECTIONS:
            position = -1
            for kw in keywords:
                for i, line in enumerate(searchable):
                    if kw in line:
                        position = i
                        break
                if position >= 0:
                    break
            if position >= 0:
                found_order.append((section_name, position))
            else:
                missing.append(section_name)

        if missing:
            return [
                RuleResult(
                    status=CheckStatus.FAILED,
                    message=f"Отсутствуют обязательные разделы: {', '.join(missing)}",
                    details={"missing_sections": missing},
                )
            ]

        order_violations: list[str] = []
        for i in range(len(found_order) - 1):
            if found_order[i][1] > found_order[i + 1][1]:
                order_violations.append(f"'{found_order[i][0]}' найден после '{found_order[i + 1][0]}'")

        if order_violations:
            return [
                RuleResult(
                    status=CheckStatus.FAILED,
                    message="Нарушен порядок разделов",
                    details={"order_violations": order_violations},
                )
            ]

        return [
            RuleResult(
                status=CheckStatus.PASSED,
                message="Все обязательные разделы присутствуют в правильном порядке",
            )
        ]
