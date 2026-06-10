from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import RegisterRequest, LoginRequest, SuccessResponse, ErrorResponse
from app.services import user as user_svc
from app.core.database import get_db
from app.core.security import create_token

router = APIRouter()
# 安全说明: 当前 openid 由前端直传，适用于开发/演示环境。
# 微信生产环境应改为: 前端传 code → 后端调 code2session → 换取 openid
# 避免客户端伪造 openid 的账户接管风险。


@router.post("/v1/auth/register", tags=["Auth"])
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    exist = await user_svc.get_user_by_openid(db, req.openid)
    if exist:
        token = create_token(exist.id, exist.openid)
        return SuccessResponse(data={"token": token, "user_id": exist.id, "name": exist.name, "is_new": False})

    user = await user_svc.create_user(db, req.openid)
    token = create_token(user.id, user.openid)
    return SuccessResponse(data={"token": token, "user_id": user.id, "name": user.name, "is_new": True})


@router.post("/v1/auth/login", tags=["Auth"])
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await user_svc.get_user_by_openid(db, req.openid)
    if user is None:
        return ErrorResponse(error={"code": "USER_NOT_FOUND", "message": "用户未注册"})
    token = create_token(user.id, user.openid)
    return SuccessResponse(data={"token": token, "user_id": user.id, "name": user.name})
