from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import RegisterRequest, LoginRequest, SuccessResponse, ErrorResponse
from app.services import user as user_svc
from app.core.database import get_db
from app.core.security import create_token

router = APIRouter()

# ── 安全说明 ──
# 旧 openid 演示路径：openid 由前端直传，适用于开发/演示环境。
# 微信生产环境应改为: 前端传 code → 后端调 code2session → 换取 openid，避免客户端伪造 openid。
# v5 新增密码注册/登录：使用 bcrypt 哈希存储密码，不保存明文。


@router.post("/v1/auth/register", tags=["Auth"])
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    await user_svc.ensure_user_auth_columns(db)

    # ── v5 密码注册路径 ──
    if req.username.strip():
        username = req.username.strip()
        password = req.password
        if not user_svc.validate_username_format(username):
            return ErrorResponse(error={"code": "INVALID_USERNAME", "message": "用户名需要 3-32 位字母、数字、下划线或短横线"})
        ok, err = user_svc.validate_password_strength(password)
        if not ok:
            return ErrorResponse(error={"code": "WEAK_PASSWORD", "message": err})

        exist = await user_svc.get_user_by_username(db, username)
        if exist:
            return ErrorResponse(error={"code": "USERNAME_TAKEN", "message": "用户名已注册"})

        user = await user_svc.create_password_user(db, username, password, name=req.name)
        token = create_token(user.id, user.username or user.openid or "")
        return SuccessResponse(data={
            "token": token, "user_id": user.id, "name": user.name,
            "username": user.username, "is_new": True,
        })

    # ── 旧 openid 演示注册路径（兼容） ──
    if not req.openid.strip():
        return ErrorResponse(error={"code": "INVALID_INPUT", "message": "请提供用户名和密码，或 OpenID"})

    exist = await user_svc.get_user_by_openid(db, req.openid)
    if exist:
        token = create_token(exist.id, exist.openid)
        return SuccessResponse(data={"token": token, "user_id": exist.id, "name": exist.name, "is_new": False})

    user = await user_svc.create_user(db, req.openid, name=req.name)
    token = create_token(user.id, user.openid)
    return SuccessResponse(data={"token": token, "user_id": user.id, "name": user.name, "is_new": True})


@router.post("/v1/auth/login", tags=["Auth"])
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    await user_svc.ensure_user_auth_columns(db)

    # ── v5 密码登录路径 ──
    if req.username.strip() and req.password:
        user = await user_svc.authenticate_password_user(db, req.username, req.password)
        if user is None:
            return ErrorResponse(error={"code": "INVALID_CREDENTIALS", "message": "账号或密码错误"})
        token = create_token(user.id, user.username or user.openid or "")
        return SuccessResponse(data={
            "token": token, "user_id": user.id, "name": user.name,
            "username": user.username, "is_new": False,
        })

    # ── 旧 openid 演示登录路径（兼容） ──
    if not req.openid.strip():
        return ErrorResponse(error={"code": "INVALID_INPUT", "message": "请提供用户名和密码，或 OpenID"})

    user = await user_svc.get_user_by_openid(db, req.openid)
    if user is None:
        return ErrorResponse(error={"code": "USER_NOT_FOUND", "message": "用户未注册"})
    token = create_token(user.id, user.openid)
    return SuccessResponse(data={"token": token, "user_id": user.id, "name": user.name})
