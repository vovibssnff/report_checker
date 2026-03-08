from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import httpx


async def test_dev_login_creates_user_and_sets_cookie(client: httpx.AsyncClient):
    resp = await client.post(
        "/api/v1/auth/dev/login",
        json={"email": "new@test.com", "name": "New User"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "new@test.com"
    assert body["name"] == "New User"
    assert body["role"] == "student"
    assert "id" in body
    assert "access_token" in resp.cookies


async def test_dev_login_returns_existing_user(client: httpx.AsyncClient, user_repo):
    resp1 = await client.post(
        "/api/v1/auth/dev/login",
        json={"email": "repeat@test.com", "name": "Repeat User"},
    )
    assert resp1.status_code == 200
    first_id = resp1.json()["id"]

    resp2 = await client.post(
        "/api/v1/auth/dev/login",
        json={"email": "repeat@test.com", "name": "Repeat User"},
    )
    assert resp2.status_code == 200
    assert resp2.json()["id"] == first_id


async def test_me_with_auth(auth_client: httpx.AsyncClient, test_user):
    resp = await auth_client.get("/api/v1/auth/me")
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == test_user.email
    assert body["name"] == test_user.name
    assert body["id"] == str(test_user.id)


async def test_me_without_auth(client: httpx.AsyncClient):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


async def test_logout_clears_cookie(auth_client: httpx.AsyncClient):
    resp = await auth_client.post("/api/v1/auth/logout")
    assert resp.status_code == 204
    set_cookie = resp.headers.get("set-cookie", "")
    assert "access_token" in set_cookie
    assert "Max-Age=0" in set_cookie or '="";' in set_cookie or "expires=" in set_cookie.lower()
