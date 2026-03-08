from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from app.core.domain.value_objects import CheckStatus, DocumentType, Severity

if TYPE_CHECKING:
    from app.checkers.pdf_parser import ParsedPDF


@dataclass
class RuleResult:
    status: CheckStatus
    message: str
    details: dict[str, Any] | None = None


class BaseRule(ABC):
    code: str
    name: str
    description: str
    document_type: DocumentType
    default_severity: Severity
    default_config: dict[str, Any]

    @abstractmethod
    async def check(self, pdf: ParsedPDF, config: dict[str, Any]) -> list[RuleResult]: ...


def rule(
    code: str,
    name: str,
    document_type: DocumentType,
    severity: Severity = Severity.ERROR,
    description: str = "",
    default_config: dict[str, Any] | None = None,
):
    def decorator(cls: type[BaseRule]) -> type[BaseRule]:
        cls.code = code
        cls.name = name
        cls.description = description
        cls.document_type = document_type
        cls.default_severity = severity
        cls.default_config = default_config or {}

        from app.checkers.registry import RuleRegistry

        RuleRegistry.instance().register(cls())
        return cls

    return decorator
