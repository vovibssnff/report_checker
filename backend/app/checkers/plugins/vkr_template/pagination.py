from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.checkers.base import BaseRule, RuleResult, rule
from app.core.domain.value_objects import CheckStatus, DocumentType, Severity

if TYPE_CHECKING:
    from app.checkers.pdf_parser import ParsedPDF

_PTS_TO_MM = 1 / 2.835


@rule(
    code="vkr.pagination.arabic_numbers",
    name="Наличие нумерации страниц",
    document_type=DocumentType.VKR_TEMPLATE,
    severity=Severity.ERROR,
    description="Проверка наличия арабских номеров страниц",
    default_config={"skip_first_pages": 2},
)
class ArabicNumbersRule(BaseRule):
    async def check(self, pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
        skip_first = config.get("skip_first_pages", 2)
        pages_without_numbers: list[int] = []

        for page in pdf.pages:
            if page.number <= skip_first:
                continue
            page_h_pt = page.height_mm / _PTS_TO_MM
            bottom_numbers = [
                tb for tb in page.text_blocks if tb.bbox[1] > page_h_pt * 0.9 and tb.text.strip().isdigit()
            ]
            if not bottom_numbers:
                pages_without_numbers.append(page.number)

        if pages_without_numbers and len(pages_without_numbers) > pdf.page_count * 0.3:
            return [
                RuleResult(
                    status=CheckStatus.FAILED,
                    message="Отсутствует нумерация страниц",
                    details={"pages_without_numbers": pages_without_numbers},
                )
            ]
        return [RuleResult(status=CheckStatus.PASSED, message="Нумерация страниц присутствует")]


@rule(
    code="vkr.pagination.position",
    name="Положение номеров страниц",
    document_type=DocumentType.VKR_TEMPLATE,
    severity=Severity.WARNING,
    description="Проверка расположения номеров страниц (внизу по центру)",
    default_config={"skip_first_pages": 2},
)
class PageNumberPositionRule(BaseRule):
    async def check(self, pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]:
        skip_first = config.get("skip_first_pages", 2)
        misplaced: list[int] = []

        for page in pdf.pages:
            if page.number <= skip_first:
                continue
            page_w_pt = page.width_mm / _PTS_TO_MM
            page_h_pt = page.height_mm / _PTS_TO_MM
            page_center = page_w_pt / 2

            bottom_numbers = [
                tb for tb in page.text_blocks if tb.bbox[1] > page_h_pt * 0.9 and tb.text.strip().isdigit()
            ]
            for tb in bottom_numbers:
                block_center = (tb.bbox[0] + tb.bbox[2]) / 2
                if abs(block_center - page_center) > page_w_pt * 0.15:
                    misplaced.append(page.number)
                    break

        if misplaced:
            return [
                RuleResult(
                    status=CheckStatus.FAILED,
                    message=f"Номера страниц не по центру на страницах: {misplaced}",
                    details={"pages": misplaced},
                )
            ]
        return [
            RuleResult(
                status=CheckStatus.PASSED,
                message="Номера страниц расположены по центру",
            )
        ]
