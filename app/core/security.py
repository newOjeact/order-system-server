# -*- coding: utf-8 -*-
"""
安全模块：密码哈希 / JWT 签发与校验
"""
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

# bcrypt 密码哈希
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """对明文密码进行哈希"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """校验明文密码与哈希是否匹配"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    subject: int,
    expires_minutes: Optional[int] = None,
    token_type: str = "user",
) -> str:
    """签发 JWT 访问令牌，subject 为 ID；token_type 区分 user / admin"""
    expire = datetime.utcnow() + timedelta(
        minutes=expires_minutes or ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": str(subject), "exp": expire, "type": token_type}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """校验并解析 JWT，返回完整 payload；无效返回 None"""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


def decode_access_token(token: str) -> Optional[int]:
    """校验并解析 JWT，返回 subject（用户/管理员 ID）；无效返回 None"""
    payload = decode_token(token)
    if payload is None:
        return None
    try:
        return int(payload.get("sub"))
    except (ValueError, TypeError):
        return None
