from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import NewType
from uuid import UUID

DocumentId = NewType("DocumentId", UUID)
UserId = NewType("UserId", UUID)
CheckResultId = NewType("CheckResultId", UUID)
CheckRuleId = NewType("CheckRuleId", UUID)


class DocumentType(StrEnum):
    VKR_TEMPLATE = "vkr_template"
    PRACTICE_REPORT = "practice_report"


class DocumentStatus(StrEnum):
    PENDING = "pending"
    CHECKING = "checking"
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"


class UserRole(StrEnum):
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"


class Severity(StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class CheckStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    error: str | None = None


@dataclass(frozen=True)
class Pagination:
    page: int
    size: int
