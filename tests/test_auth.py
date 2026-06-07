import pytest
import uuid

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_register_new_user(client):
    uid = f"wx_test_{uuid.uuid4().hex}"
    resp = await client.post("/v1/auth/register", json={"openid": uid})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["data"]["is_new"] is True
    assert "token" in data["data"]


async def test_register_existing_user(client):
    uid = f"wx_exist_{uuid.uuid4().hex}"
    r1 = await client.post("/v1/auth/register", json={"openid": uid})
    assert r1.json()["data"]["is_new"] is True
    r2 = await client.post("/v1/auth/register", json={"openid": uid})
    assert r2.json()["data"]["is_new"] is False


async def test_login_not_found(client):
    resp = await client.post("/v1/auth/login", json={"openid": f"nobody_{uuid.uuid4().hex}"})
    assert resp.json()["status"] == "error"


async def test_profile_no_token(client):
    resp = await client.get("/v1/user/profile")
    assert resp.status_code == 401


async def test_profile_with_token(client):
    r = await client.post("/v1/auth/register", json={"openid": f"wx_prof_{uuid.uuid4().hex}"})
    token = r.json()["data"]["token"]
    resp = await client.get("/v1/user/profile", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "user_id" in data
    assert "preferences" in data
