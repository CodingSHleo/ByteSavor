from datetime import datetime, timedelta, timezone
import bcrypt
from jose import jwt
from app.core.config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def _check_secret():
    s = settings.jwt_secret
    if not s or s in ("change-me-in-production", "请替换为随机字符串"):
        raise RuntimeError("JWT_SECRET 未设置或仍为占位值，请在 .env 中配置随机密钥")


def create_token(user_id: str, openid: str = "") -> str:
    _check_secret()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": user_id, "openid": openid, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    _check_secret()
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
