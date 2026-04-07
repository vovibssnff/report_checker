from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

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


async def test_upload_document(auth_client: httpx.AsyncClient, test_user):
    resp = await auth_client.post(
        "/api/v1/documents/",
        files={"files": ("report.pdf", FAKE_PDF, "application/pdf")},
        data={"document_type": "vkr_template"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) == 1
    doc = body[0]
    assert doc["filename"] == "report.pdf"
    assert doc["document_type"] == "vkr_template"
    # Upload runs checks inline; functional tests use a mock engine with no outputs → passed.
    assert doc["status"] == "passed"


async def test_upload_multiple_documents(auth_client: httpx.AsyncClient):
    resp = await auth_client.post(
        "/api/v1/documents/",
        files=[
            ("files", ("a.pdf", FAKE_PDF, "application/pdf")),
            ("files", ("b.pdf", FAKE_PDF, "application/pdf")),
        ],
        data={"document_type": "practice_report"},
    )
    assert resp.status_code == 201
    assert len(resp.json()) == 2


async def test_upload_without_auth(client: httpx.AsyncClient):
    resp = await client.post(
        "/api/v1/documents/",
        files={"files": ("report.pdf", FAKE_PDF, "application/pdf")},
        data={"document_type": "vkr_template"},
    )
    assert resp.status_code == 401


async def test_list_documents(auth_client: httpx.AsyncClient, test_user, doc_repo):
    doc = Document(
        id=DocumentId(uuid.uuid4()),
        document_type=DocumentType.VKR_TEMPLATE,
        filename="listed.pdf",
        s3_key="documents/test/listed.pdf",
        file_size=1234,
        status=DocumentStatus.PENDING,
        source="user_upload",
        uploaded_at=datetime.now(UTC),
        checked_at=None,
        user_id=test_user.id,
    )
    doc_repo._store[doc.id] = doc

    resp = await auth_client.get("/api/v1/documents/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["filename"] == "listed.pdf"


async def test_get_document_detail(auth_client: httpx.AsyncClient, test_user, doc_repo, check_result_repo):
    doc_id = DocumentId(uuid.uuid4())
    doc = Document(
        id=doc_id,
        document_type=DocumentType.VKR_TEMPLATE,
        filename="detail.pdf",
        s3_key="documents/test/detail.pdf",
        file_size=1000,
        status=DocumentStatus.PASSED,
        source="user_upload",
        uploaded_at=datetime.now(UTC),
        checked_at=datetime.now(UTC),
        user_id=test_user.id,
    )
    doc_repo._store[doc_id] = doc

    result = CheckResult(
        id=CheckResultId(uuid.uuid4()),
        document_id=doc_id,
        rule_code="test_rule",
        severity=Severity.INFO,
        status=CheckStatus.PASSED,
        message="Looks good",
        details=None,
        created_at=datetime.now(UTC),
    )
    check_result_repo.list_for_document.side_effect = None
    check_result_repo.list_for_document.return_value = [result]

    resp = await auth_client.get(f"/api/v1/documents/{doc_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["filename"] == "detail.pdf"
    assert len(body["check_results"]) == 1
    assert body["check_results"][0]["rule_code"] == "test_rule"


async def test_delete_document(auth_client: httpx.AsyncClient, test_user, doc_repo, storage):
    doc_id = DocumentId(uuid.uuid4())
    doc = Document(
        id=doc_id,
        document_type=DocumentType.VKR_TEMPLATE,
        filename="to_delete.pdf",
        s3_key="documents/test/to_delete.pdf",
        file_size=500,
        status=DocumentStatus.PENDING,
        source="user_upload",
        uploaded_at=datetime.now(UTC),
        checked_at=None,
        user_id=test_user.id,
    )
    doc_repo._store[doc_id] = doc

    resp = await auth_client.delete(f"/api/v1/documents/{doc_id}")
    assert resp.status_code == 204
    storage.delete_file.assert_called_once_with(doc.s3_key)


async def test_run_checks(
    auth_client: httpx.AsyncClient,
    test_user,
    doc_repo,
    checker_engine,
    check_result_repo,
):
    doc_id = DocumentId(uuid.uuid4())
    doc = Document(
        id=doc_id,
        document_type=DocumentType.VKR_TEMPLATE,
        filename="check_me.pdf",
        s3_key="documents/test/check_me.pdf",
        file_size=1000,
        status=DocumentStatus.PENDING,
        source="user_upload",
        uploaded_at=datetime.now(UTC),
        checked_at=None,
        user_id=test_user.id,
    )
    doc_repo._store[doc_id] = doc

    from app.checkers.base import RuleResult
    from app.checkers.engine import CheckOutput

    checker_engine.run_checks.return_value = (
        [
            CheckOutput(
                rule_code="fmt_font",
                rule_name="Font Check",
                severity=Severity.ERROR,
                results=[RuleResult(status=CheckStatus.PASSED, message="Font OK")],
            ),
        ],
        5,
    )

    resp = await auth_client.post(f"/api/v1/documents/{doc_id}/checks")
    assert resp.status_code == 201
    body = resp.json()
    assert len(body) == 1
    assert body[0]["rule_code"] == "fmt_font"
    assert body[0]["status"] == "passed"


async def test_get_check_results(auth_client: httpx.AsyncClient, test_user, doc_repo, check_result_repo):
    doc_id = DocumentId(uuid.uuid4())
    doc = Document(
        id=doc_id,
        document_type=DocumentType.PRACTICE_REPORT,
        filename="results.pdf",
        s3_key="documents/test/results.pdf",
        file_size=800,
        status=DocumentStatus.PASSED,
        source="user_upload",
        uploaded_at=datetime.now(UTC),
        checked_at=datetime.now(UTC),
        user_id=test_user.id,
    )
    doc_repo._store[doc_id] = doc

    result = CheckResult(
        id=CheckResultId(uuid.uuid4()),
        document_id=doc_id,
        rule_code="struct_sections",
        severity=Severity.WARNING,
        status=CheckStatus.FAILED,
        message="Missing section",
        details={"section": "Introduction"},
        created_at=datetime.now(UTC),
    )
    check_result_repo.list_for_document.side_effect = None
    check_result_repo.list_for_document.return_value = [result]

    resp = await auth_client.get(f"/api/v1/documents/{doc_id}/checks")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["status"] == "failed"
    assert body[0]["details"]["section"] == "Introduction"
