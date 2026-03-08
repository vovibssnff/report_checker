from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from app.core.domain.entities.check_rule import CheckRule
from app.core.domain.value_objects import CheckRuleId, DocumentType

if TYPE_CHECKING:
    import httpx


async def test_list_rules(auth_client: httpx.AsyncClient, check_rule_repo):
    rule_id = CheckRuleId(uuid.uuid4())
    rule = CheckRule(
        id=rule_id,
        code="fmt_font",
        document_type=DocumentType.VKR_TEMPLATE,
        name="Font Check",
        description="Validates font usage",
        enabled=True,
        config=None,
    )
    check_rule_repo._store[rule_id] = rule

    resp = await auth_client.get("/api/v1/rules/")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["code"] == "fmt_font"
    assert body[0]["enabled"] is True


async def test_list_rules_filter_by_document_type(auth_client: httpx.AsyncClient, check_rule_repo):
    r1_id = CheckRuleId(uuid.uuid4())
    r2_id = CheckRuleId(uuid.uuid4())
    check_rule_repo._store[r1_id] = CheckRule(
        id=r1_id,
        code="vkr_headings",
        document_type=DocumentType.VKR_TEMPLATE,
        name="Headings",
        description="Check headings",
        enabled=True,
        config=None,
    )
    check_rule_repo._store[r2_id] = CheckRule(
        id=r2_id,
        code="pr_structure",
        document_type=DocumentType.PRACTICE_REPORT,
        name="Structure",
        description="Check structure",
        enabled=True,
        config=None,
    )

    resp = await auth_client.get("/api/v1/rules/", params={"document_type": "vkr_template"})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["code"] == "vkr_headings"


async def test_update_rule_admin(admin_client: httpx.AsyncClient, check_rule_repo):
    rule_id = CheckRuleId(uuid.uuid4())
    rule = CheckRule(
        id=rule_id,
        code="fmt_margins",
        document_type=DocumentType.VKR_TEMPLATE,
        name="Margins",
        description="Check margins",
        enabled=True,
        config=None,
    )
    check_rule_repo._store[rule_id] = rule

    resp = await admin_client.patch(
        f"/api/v1/rules/{rule_id}",
        json={"enabled": False, "config": {"tolerance_mm": 2}},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["enabled"] is False
    assert body["config"] == {"tolerance_mm": 2}


async def test_update_rule_non_admin_forbidden(auth_client: httpx.AsyncClient, check_rule_repo):
    rule_id = CheckRuleId(uuid.uuid4())
    check_rule_repo._store[rule_id] = CheckRule(
        id=rule_id,
        code="fmt_margins",
        document_type=DocumentType.VKR_TEMPLATE,
        name="Margins",
        description="Check margins",
        enabled=True,
        config=None,
    )

    resp = await auth_client.patch(
        f"/api/v1/rules/{rule_id}",
        json={"enabled": False},
    )
    assert resp.status_code == 403


async def test_update_rule_unauthenticated(client: httpx.AsyncClient):
    fake_id = uuid.uuid4()
    resp = await client.patch(
        f"/api/v1/rules/{fake_id}",
        json={"enabled": False},
    )
    assert resp.status_code == 401
