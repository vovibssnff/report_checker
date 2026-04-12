from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.integration.conftest import INTEGRATION_PDF

if TYPE_CHECKING:
    import httpx

pytestmark = pytest.mark.integration


async def test_upload_check_retrieve_flow(
    auth_integration_client: httpx.AsyncClient,
):
    upload_resp = await auth_integration_client.post(
        "/api/v1/documents/",
        files={"files": ("flow_test.pdf", INTEGRATION_PDF, "application/pdf")},
        data={"document_type": "practice_report"},
    )
    assert upload_resp.status_code == 201
    docs = upload_resp.json()
    assert len(docs) == 1
    doc_id = docs[0]["id"]
    # Upload endpoint runs checks before responding; status is already terminal.
    assert docs[0]["status"] in ("passed", "failed", "warning")

    check_resp = await auth_integration_client.post(f"/api/v1/documents/{doc_id}/checks")
    assert check_resp.status_code == 201
    results = check_resp.json()
    assert isinstance(results, list)

    results_resp = await auth_integration_client.get(f"/api/v1/documents/{doc_id}/checks")
    assert results_resp.status_code == 200
    assert isinstance(results_resp.json(), list)

    detail_resp = await auth_integration_client.get(f"/api/v1/documents/{doc_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["status"] in ("passed", "failed", "warning")
    assert detail["checked_at"] is not None
    assert "check_results" in detail


async def test_internal_upload_check_flow(
    integration_client: httpx.AsyncClient,
):
    resp = await integration_client.post(
        "/internal/documents/",
        files={"files": ("internal_flow.pdf", INTEGRATION_PDF, "application/pdf")},
        data={"document_type": "practice_report", "source": "ci"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    item = body[0]
    assert "document_id" in item
    assert item["status"] in ("passed", "failed", "warning")
    assert isinstance(item["check_results"], list)

    doc_id = item["document_id"]
    checks_resp = await integration_client.get(f"/internal/documents/{doc_id}/checks")
    assert checks_resp.status_code == 200


async def test_list_documents_after_upload(
    auth_integration_client: httpx.AsyncClient,
):
    await auth_integration_client.post(
        "/api/v1/documents/",
        files={"files": ("listed.pdf", INTEGRATION_PDF, "application/pdf")},
        data={"document_type": "practice_report"},
    )

    list_resp = await auth_integration_client.get("/api/v1/documents/")
    assert list_resp.status_code == 200
    body = list_resp.json()
    assert body["total"] >= 1
    assert len(body["items"]) >= 1


async def test_delete_cleans_up(
    auth_integration_client: httpx.AsyncClient,
):
    upload_resp = await auth_integration_client.post(
        "/api/v1/documents/",
        files={"files": ("to_delete.pdf", INTEGRATION_PDF, "application/pdf")},
        data={"document_type": "practice_report"},
    )
    doc_id = upload_resp.json()[0]["id"]

    del_resp = await auth_integration_client.delete(f"/api/v1/documents/{doc_id}")
    assert del_resp.status_code == 204

    get_resp = await auth_integration_client.get(f"/api/v1/documents/{doc_id}")
    assert get_resp.status_code == 500 or get_resp.status_code == 404
