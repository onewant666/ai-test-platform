"""JWT Token 工具 & 密码哈希"""

from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from app.config import get_settings
import hashlib

settings = get_settings()


# ── 密码哈希（使用 SHA-256 + salt，避免 passlib/bcrypt 兼容性问题）──

def hash_password(password: str) -> str:
    """使用 salted SHA-256 哈希密码"""
    salt = settings.jwt_secret_key
    return hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()


def verify_password(plain: str, hashed: str) -> bool:
    """验证密码"""
    return hash_password(plain) == hashed


# ── JWT Token ──

def create_token(user_id: int, expires_minutes: int | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.jwt_expire_minutes
    )
    payload = {"sub": str(user_id), "exp": int(expire.timestamp())}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    """解码 JWT，返回 payload；失败抛 JWTError"""
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


def get_user_id_from_token(token: str) -> int:
    payload = decode_token(token)
    return int(payload["sub"])
