from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码

    Args:
        plain_password: 明文密码
        hashed_password: 哈希密码

    Returns:
        密码是否匹配
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    获取密码哈希值

    Args:
        password: 明文密码

    Returns:
        哈希后的密码
    """
    return pwd_context.hash(password)

def generate_password_reset_token(email: str) -> str:
    """
    生成密码重置令牌

    Args:
        email: 用户邮箱

    Returns:
        重置令牌
    """
    from app.utils.jwt_utils import create_access_token
    delta = timedelta(hours=1)  # 1小时有效期
    token_data = {"sub": email, "type": "password_reset"}
    return create_access_token(token_data, expires_delta=delta)