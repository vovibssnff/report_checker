from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from app.checkers.base import RuleResult
from app.checkers.engine import CheckOutput
from app.core.domain.entities.check_result import CheckResult
from app.core.domain.entities.document import Document
from app.core.domain.value_objects import (
    CheckResultId,
    CheckStatus,
    DocumentId,
    DocumentStatus,
    DocumentType,
    Severity,
)
from tests.functional.conftest import FAKE_PDF

if TYPE_CHECKING:
    import httpx


async def test_internal_upload_and_check(client: httpx.AsyncClient, checker_engine):
    checker_engine.run_checks.return_value = (
        [
            CheckOutput(
                rule_code="fmt_margins",
                rule_name="Margin Check",
                severity=Severity.WARNING,
                results=[
                    RuleResult(status=CheckStatus.FAILED, message="Left margin too small"),
                ],
            ),
        ],
        8,
    )

    resp = await client.post(
        "/internal/documents/",
        files={"files": ("report.pdf", FAKE_PDF, "application/pdf")},
        data={"document_type": "practice_report", "source": "lms"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) == 1
    item = body[0]
    assert "document_id" in item
    assert len(item["check_results"]) == 1
    assert item["check_results"][0]["rule_code"] == "fmt_margins"
    assert item["check_results"][0]["status"] == "failed"


async def test_internal_get_check_results(client: httpx.AsyncClient, doc_repo, check_result_repo):
    doc_id = DocumentId(uuid.uuid4())
    doc = Document(
        id=doc_id,
        document_type=DocumentType.PRACTICE_REPORT,
        filename="internal.pdf",
        s3_key="documents/internal/test.pdf",
        file_size=500,
        status=DocumentStatus.PASSED,
        source="lms",
        uploaded_at=datetime.now(UTC),
        checked_at=datetime.now(UTC),
        user_id=None,
    )
    doc_repo._store[doc_id] = doc

    result = CheckResult(
        id=CheckResultId(uuid.uuid4()),
        document_id=doc_id,
        rule_code="struct_toc",
        severity=Severity.INFO,
        status=CheckStatus.PASSED,
        message="TOC present",
        details=None,
        created_at=datetime.now(UTC),
    )
    check_result_repo.list_for_document.side_effect = None
    check_result_repo.list_for_document.return_value = [result]

    resp = await client.get(f"/internal/documents/{doc_id}/checks")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["rule_code"] == "struct_toc"


async def test_internal_upload_no_auth_required(client: httpx.AsyncClient, checker_engine):
    checker_engine.run_checks.return_value = ([], 0)

    resp = await client.post(
        "/internal/documents/",
        files={"files": ("noauth.pdf", FAKE_PDF, "application/pdf")},
        data={"document_type": "vkr_template", "source": "api"},
    )
    assert resp.status_code == 200
