from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import httpx


async def test_dev_register_creates_user_and_sets_cookie(client: httpx.AsyncClient):
    resp = await client.post(
        "/api/v1/auth/dev/register",
        json={"email": "new@test.com", "name": "New User", "password": "qwerty123", "role": "student"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "new@test.com"
    assert body["name"] == "New User"
    assert body["role"] == "student"
    assert "id" in body
    assert "access_token" in resp.cookies


async def test_dev_register_conflict_for_existing_email(client: httpx.AsyncClient):
    resp1 = await client.post(
        "/api/v1/auth/dev/register",
        json={"email": "repeat@test.com", "name": "Repeat User", "password": "qwerty123", "role": "student"},
    )
    assert resp1.status_code == 201
    resp2 = await client.post(
        "/api/v1/auth/dev/register",
        json={"email": "repeat@test.com", "name": "Repeat User", "password": "qwerty123", "role": "student"},
    )
    assert resp2.status_code == 409


async def test_dev_login_success(client: httpx.AsyncClient):
    await client.post(
        "/api/v1/auth/dev/register",
        json={"email": "login@test.com", "name": "Login User", "password": "qwerty123", "role": "teacher"},
    )
    resp = await client.post(
        "/api/v1/auth/dev/login",
        json={"email": "login@test.com", "password": "qwerty123"},
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == "login@test.com"


async def test_dev_login_wrong_password(client: httpx.AsyncClient):
    await client.post(
        "/api/v1/auth/dev/register",
        json={"email": "wrong@test.com", "name": "Wrong User", "password": "qwerty123", "role": "student"},
    )
    resp = await client.post(
        "/api/v1/auth/dev/login",
        json={"email": "wrong@test.com", "password": "bad-password"},
    )
    assert resp.status_code == 401


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
