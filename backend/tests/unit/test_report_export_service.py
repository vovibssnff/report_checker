from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.domain.entities.check_result import CheckResult
from app.core.domain.entities.document import Document
from app.core.domain.value_objects import CheckResultId, CheckStatus, DocumentId, DocumentStatus, DocumentType, Severity
from app.core.services.report_export_service import ReportExportService


@pytest.mark.asyncio
async def test_export_csv_includes_header_and_rows() -> None:
    document_id = DocumentId(uuid4())
    doc = Document(
        id=document_id,
        document_type=DocumentType.VKR_TEMPLATE,
        filename="report.pdf",
        s3_key="k/report.pdf",
        file_size=123,
        status=DocumentStatus.PASSED,
        source="upload",
        uploaded_at=datetime.now(UTC),
        checked_at=None,
        user_id=None,
    )
    check_results = [
        CheckResult(
            id=CheckResultId(uuid4()),
            document_id=document_id,
            rule_code="rule.a",
            severity=Severity.ERROR,
            status=CheckStatus.FAILED,
            message="failed_a",
            details=None,
            created_at=datetime.now(UTC),
        ),
        CheckResult(
            id=CheckResultId(uuid4()),
            document_id=document_id,
            rule_code="rule.b",
            severity=Severity.INFO,
            status=CheckStatus.PASSED,
            message="passed_b",
            details=None,
            created_at=datetime.now(UTC),
        ),
    ]

    doc_repo = AsyncMock()
    check_result_repo = AsyncMock()
    doc_repo.get_by_id.return_value = doc
    check_result_repo.list_for_document.return_value = check_results

    service = ReportExportService(doc_repo=doc_repo, check_result_repo=check_result_repo)

    exported = await service.export_csv(document_id)

    assert "document,rule_code,severity,status,message" in exported
    assert "report.pdf,rule.a,error,failed,failed_a" in exported
    assert "report.pdf,rule.b,info,passed,passed_b" in exported
    doc_repo.get_by_id.assert_awaited_once_with(document_id)
    check_result_repo.list_for_document.assert_awaited_once_with(document_id)


@pytest.mark.asyncio
async def test_export_pdf_report_returns_utf8_csv_bytes() -> None:
    document_id = DocumentId(uuid4())
    doc_repo = AsyncMock()
    check_result_repo = AsyncMock()
    doc_repo.get_by_id.return_value = Document(
        id=document_id,
        document_type=DocumentType.PRACTICE_REPORT,
        filename="practice.pdf",
        s3_key="k/practice.pdf",
        file_size=123,
        status=DocumentStatus.PENDING,
        source="upload",
        uploaded_at=datetime.now(UTC),
        checked_at=None,
        user_id=None,
    )
    check_result_repo.list_for_document.return_value = []

    service = ReportExportService(doc_repo=doc_repo, check_result_repo=check_result_repo)

    payload = await service.export_pdf_report(document_id)

    assert isinstance(payload, bytes)
    assert payload.decode("utf-8").startswith("document,rule_code,severity,status,message")
