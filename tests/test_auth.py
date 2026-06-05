import pytest

pytestmark = pytest.mark.asyncio


@pytest.mark.asyncio
async def test_register_new_user(client):
    resp = await client.post("/v1/auth/register", json={"openid": "wx_test_pytest"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["data"]["is_new"] is True
    assert "token" in data["data"]


@pytest.mark.asyncio
async def test_register_existing_user(client):
    await client.post("/v1/auth/register", json={"openid": "wx_test_pytest"})
    resp = await client.post("/v1/auth/register", json={"openid": "wx_test_pytest"})
    assert resp.json()["data"]["is_new"] is False


@pytest.mark.asyncio
async def test_login_not_found(client):
    resp = await client.post("/v1/auth/login", json={"openid": "nobody_xyz"})
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
