from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.checkers.base import BaseRule, RuleResult, rule
from app.core.domain.value_objects import CheckStatus, DocumentType, Severity

if TYPE_CHECKING:
    from app.checkers.pdf_parser import ParsedPDF

_REQUIRED_SECTIONS = [
    ("title_page", ["титульный лист"]),
    ("toc", ["содержание", "оглавление"]),
    ("introduction", ["введение"]),
    ("conclusion", ["заключение"]),
]

_STAGE_KEYWORDS = ["этап", "раздел", "часть", "stage"]


@rule(
    code="practice.structure.required_sections",
    name="Обязательные разделы отчёта по практике",
    document_type=DocumentType.PRACTICE_REPORT,
    severity=Severity.ERROR,
    description="Проверка наличия обязательных разделов",
)
class RequiredSectionsRule(BaseRule):
    async def check(self, pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
        all_text: list[str] = []
        for page in pdf.pages:
            all_text.extend(line.strip().lower() for line in page.lines)
        heading_texts = [h.text.strip().lower() for h in pdf.headings]
        searchable = all_text + heading_texts

        missing: list[str] = []
        for section_code, keywords in _REQUIRED_SECTIONS:
            found = any(kw in line for kw in keywords for line in searchable)
            if not found:
                missing.append(section_code)

        if missing:
            return [
                RuleResult(
                    status=CheckStatus.FAILED,
                    message="required_sections_missing",
                    details={"missing_sections": missing},
                )
            ]
        return [
            RuleResult(
                status=CheckStatus.PASSED,
                message="required_sections_ok",
            )
        ]


@rule(
    code="practice.structure.stage_descriptions",
    name="Описание этапов практики",
    document_type=DocumentType.PRACTICE_REPORT,
    severity=Severity.ERROR,
    description="Проверка наличия описания этапов 2, 3, 4",
    default_config={"required_stages": [2, 3, 4]},
)
class StageDescriptionsRule(BaseRule):
    async def check(self, pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
        required_stages: list[int] = config.get("required_stages", [2, 3, 4])

        all_text: list[str] = []
        for page in pdf.pages:
            all_text.extend(line.strip().lower() for line in page.lines)
        heading_texts = [h.text.strip().lower() for h in pdf.headings]
        searchable = all_text + heading_texts

        missing_stages: list[int] = []
        for stage in required_stages:
            found = any(kw in line and str(stage) in line for kw in _STAGE_KEYWORDS for line in searchable)
            if not found:
                missing_stages.append(stage)

        if missing_stages:
            return [
                RuleResult(
                    status=CheckStatus.FAILED,
                    message="stage_descriptions_missing",
                    details={"missing_stages": missing_stages},
                )
            ]
        return [
            RuleResult(
                status=CheckStatus.PASSED,
                message="stage_descriptions_ok",
            )
        ]


@rule(
    code="practice.structure.screenshots",
    name="Наличие скриншотов",
    document_type=DocumentType.PRACTICE_REPORT,
    severity=Severity.WARNING,
    description="Проверка наличия скриншотов (изображений) в отчёте",
    default_config={"min_images": 1},
)
class ScreenshotsRule(BaseRule):
    async def check(self, pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
        min_images = config.get("min_images", 1)
        total_images = sum(len(page.images) for page in pdf.pages)

        if total_images < min_images:
            return [
                RuleResult(
                    status=CheckStatus.FAILED,
                    message="screenshots_insufficient",
                    details={"found": total_images, "required": min_images},
                )
            ]
        return [
            RuleResult(
                status=CheckStatus.PASSED,
                message="screenshots_ok",
                details={"found": total_images},
            )
        ]
