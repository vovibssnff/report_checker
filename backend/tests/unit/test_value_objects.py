from __future__ import annotations

import dataclasses

import pytest

from app.core.domain.value_objects import (
    CheckStatus,
    DocumentStatus,
    DocumentType,
    Pagination,
    Severity,
    UserRole,
)


class TestDocumentType:
    def test_values(self):
        assert DocumentType.VKR_TEMPLATE == "vkr_template"
        assert DocumentType.PRACTICE_REPORT == "practice_report"

    def test_member_count(self):
        assert len(DocumentType) == 2


class TestDocumentStatus:
    def test_values(self):
        assert DocumentStatus.PENDING == "pending"
        assert DocumentStatus.CHECKING == "checking"
        assert DocumentStatus.PASSED == "passed"
        assert DocumentStatus.FAILED == "failed"
        assert DocumentStatus.WARNING == "warning"

    def test_member_count(self):
        assert len(DocumentStatus) == 5


class TestCheckStatus:
    def test_values(self):
        assert CheckStatus.PASSED == "passed"
        assert CheckStatus.FAILED == "failed"

    def test_member_count(self):
        assert len(CheckStatus) == 2


class TestSeverity:
    def test_values(self):
        assert Severity.ERROR == "error"
        assert Severity.WARNING == "warning"
        assert Severity.INFO == "info"

    def test_member_count(self):
        assert len(Severity) == 3


class TestUserRole:
    def test_values(self):
        assert UserRole.STUDENT == "student"
        assert UserRole.TEACHER == "teacher"
        assert UserRole.ADMIN == "admin"


class TestPagination:
    def test_creation(self):
        p = Pagination(page=1, size=20)
        assert p.page == 1
        assert p.size == 20

    def test_frozen(self):
        p = Pagination(page=1, size=20)
        with pytest.raises(dataclasses.FrozenInstanceError):
            p.page = 2  # type: ignore[misc]

    def test_equality(self):
        assert Pagination(page=1, size=10) == Pagination(page=1, size=10)
        assert Pagination(page=1, size=10) != Pagination(page=2, size=10)
