from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from app.config.settings import settings

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建访问令牌

    Args:
        data: 要编码的数据
        expires_delta: 过期时间增量

    Returns:
        JWT token字符串
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """
    验证JWT令牌

    Args:
        token: JWT令牌字符串

    Returns:
        解码后的数据，验证失败返回None
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        return None

def create_refresh_token(data: dict) -> str:
    """
    创建刷新令牌

    Args:
        data: 要编码的数据

    Returns:
        JWT refresh token字符串
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)  # 刷新令牌有效期7天
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt