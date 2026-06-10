"""JWT 认证与密码加密"""
from datetime import datetime, timedelta
from jose import jwt, JWTError
import hashlib
import hmac
from passlib.hash import bcrypt
from app.core.config import settings


def hash_password(password: str) -> str:
    """bcrypt 密码哈希"""
    return bcrypt.hash(password)


def _verify_sha256(password: str, hashed: str) -> bool:
    """兼容旧版 SHA-256 密码（迁移期间使用）"""
    try:
        salt, h = hashed.split("$", 1)
        return hmac.compare_digest(hashlib.sha256((salt + password).encode()).hexdigest(), h)
    except Exception:
        return False


def verify_password(password: str, hashed: str) -> bool:
    """验证密码 — 先试 bcrypt，失败则试旧 SHA-256"""
    if hashed.startswith("$2b$") or hashed.startswith("$2a$"):
        try:
            return bcrypt.verify(password, hashed)
        except Exception:
            return False
    # 旧格式 SHA-256 降级兼容
    return _verify_sha256(password, hashed)


def create_access_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": str(user_id), "exp": expire, "type": "access"},
        settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM,
    )


def create_refresh_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return jwt.encode(
        {"sub": str(user_id), "exp": expire, "type": "refresh"},
        settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM,
    )


def decode_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return {"user_id": int(payload["sub"]), "type": payload.get("type")}
    except (JWTError, Exception):
        return None
