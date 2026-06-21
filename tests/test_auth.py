import pytest
import uuid

pytestmark = [pytest.mark.asyncio(loop_scope="session"), pytest.mark.db]


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
    assert "computed_targets" in data


async def test_register_persists_name(client):
    """V3-8: 注册昵称应写入数据库 User.name。"""
    uid = f"wx_name_{uuid.uuid4().hex}"
    resp = await client.post("/v1/auth/register", json={"openid": uid, "name": "小明"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["name"] == "小明", f"注册昵称应返回，实际: {data.get('name')}"
    assert data["is_new"] is True


async def test_register_empty_name(client):
    """无昵称注册不报错，返回空 name。"""
    uid = f"wx_noname_{uuid.uuid4().hex}"
    resp = await client.post("/v1/auth/register", json={"openid": uid})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["name"] == ""
    assert data["is_new"] is True


async def test_login_returns_stored_name(client):
    """登录应返回注册时保存的昵称。"""
    uid = f"wx_login_name_{uuid.uuid4().hex}"
    await client.post("/v1/auth/register", json={"openid": uid, "name": "小红"})
    resp = await client.post("/v1/auth/login", json={"openid": uid})
    assert resp.status_code == 200
    assert resp.json()["data"]["name"] == "小红"


async def test_profile_targets_use_body_metrics_and_custom_override(client):
    r = await client.post("/v1/auth/register", json={"openid": f"wx_targets_{uuid.uuid4().hex}"})
    token = r.json()["data"]["token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.put("/v1/user/profile", headers=headers, json={
        "goal": "muscle_gain",
        "preferences": ["high_protein"],
        "body_metrics": {
            "sex": "male",
            "age": 22,
            "height_cm": 180,
            "weight_kg": 80,
            "exercise_per_week": 5,
        },
        "nutrition_targets": {"calories": 3100, "protein": 170},
    })

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["body_metrics"]["weight_kg"] == 80
    assert data["computed_targets"]["calories"] == 3100
    assert data["computed_targets"]["protein"] == 170
    assert data["computed_targets"]["source"] == "custom"


# ── v5: 密码注册/登录测试 ──

async def test_password_register_success(client):
    """用户名密码注册成功。"""
    resp = await client.post("/v1/auth/register", json={
        "username": f"pwd_user_{uuid.uuid4().hex[:8]}",
        "password": "Aa123456",
        "name": "密码用户",
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["is_new"] is True
    assert data["name"] == "密码用户"
    assert "token" in data


async def test_password_register_duplicate_username(client):
    """重复用户名注册失败。"""
    uname = f"dup_{uuid.uuid4().hex[:8]}"
    r1 = await client.post("/v1/auth/register", json={"username": uname, "password": "Aa123456"})
    assert r1.status_code == 200
    r2 = await client.post("/v1/auth/register", json={"username": uname, "password": "Aa123456"})
    assert r2.status_code == 200  # 不是 422
    assert r2.json()["status"] == "error"
    assert r2.json()["error"]["code"] == "USERNAME_TAKEN"


async def test_password_register_weak_password(client):
    """弱密码注册失败。"""
    resp = await client.post("/v1/auth/register", json={
        "username": f"weak_{uuid.uuid4().hex[:8]}",
        "password": "123",
    })
    assert resp.status_code == 200
    assert resp.json()["status"] == "error"
    assert resp.json()["error"]["code"] == "WEAK_PASSWORD"


async def test_password_login_success(client):
    """正确密码登录成功。"""
    uname = f"login_{uuid.uuid4().hex[:8]}"
    await client.post("/v1/auth/register", json={"username": uname, "password": "Aa123456", "name": "登录测试"})
    resp = await client.post("/v1/auth/login", json={"username": uname, "password": "Aa123456"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["name"] == "登录测试"
    assert "token" in data


async def test_password_login_wrong_password(client):
    """密码错误登录失败。"""
    uname = f"wrong_{uuid.uuid4().hex[:8]}"
    await client.post("/v1/auth/register", json={"username": uname, "password": "Aa123456"})
    resp = await client.post("/v1/auth/login", json={"username": uname, "password": "WrongPass1"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "error"
    assert resp.json()["error"]["code"] == "INVALID_CREDENTIALS"


async def test_password_hash_not_in_response(client):
    """password_hash 不出现在任何响应中。"""
    uname = f"nohash_{uuid.uuid4().hex[:8]}"
    r1 = await client.post("/v1/auth/register", json={"username": uname, "password": "Aa123456"})
    text1 = r1.text
    assert "password_hash" not in text1
    r2 = await client.post("/v1/auth/login", json={"username": uname, "password": "Aa123456"})
    text2 = r2.text
    assert "password_hash" not in text2


async def test_invalid_username_format(client):
    """非法用户名注册失败。"""
    resp = await client.post("/v1/auth/register", json={
        "username": "ab",  # too short
        "password": "Aa123456",
    })
    assert resp.status_code == 200
    assert resp.json()["status"] == "error"
    assert resp.json()["error"]["code"] == "INVALID_USERNAME"
