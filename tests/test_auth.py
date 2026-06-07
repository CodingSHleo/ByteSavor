import pytest
import time

pytestmark = pytest.mark.asyncio


@pytest.mark.asyncio
async def test_register_new_user(client):
    uid = f"wx_test_{int(time.time()*1000)}"
    resp = await client.post("/v1/auth/register", json={"openid": uid})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["data"]["is_new"] is True
    assert "token" in data["data"]


@pytest.mark.asyncio
async def test_register_existing_user(client):
    uid = f"wx_exist_{int(time.time()*1000)}"
    r1 = await client.post("/v1/auth/register", json={"openid": uid})
    assert r1.json()["data"]["is_new"] is True
    r2 = await client.post("/v1/auth/register", json={"openid": uid})
    assert r2.json()["data"]["is_new"] is False


@pytest.mark.asyncio
async def test_login_not_found(client):
    resp = await client.post("/v1/auth/login", json={"openid": f"nobody_{int(time.time())}"})
    assert resp.json()["status"] == "error"


@pytest.mark.asyncio
async def test_profile_no_token(client):
    resp = await client.get("/v1/user/profile")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_profile_with_token(client):
    r = await client.post("/v1/auth/register", json={"openid": "wx_prof_test"})
    token = r.json()["data"]["token"]
    resp = await client.get("/v1/user/profile", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "user_id" in data
    assert "preferences" in data
