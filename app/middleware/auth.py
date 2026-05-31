from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import decode_token

bearer = HTTPBearer(auto_error=False)


async def get_current_user(cred: HTTPAuthorizationCredentials | None = Depends(bearer)) -> dict:
    if cred is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="缺少认证信息")
    try:
        payload = decode_token(cred.credentials)
        return payload
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token 无效或已过期")


async def get_optional_user(cred: HTTPAuthorizationCredentials | None = Depends(bearer)) -> dict | None:
    """可选认证：有 token 就解析，没有也不报错"""
    if cred is None:
        return None
    try:
        return decode_token(cred.credentials)
    except Exception:
        return None
