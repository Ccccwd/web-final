from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.utils.jwt_utils import verify_token
from app.models.user import User

# HTTP Bearer 认证方案
security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    获取当前认证用户

    Args:
        credentials: HTTP认证凭据
        db: 数据库会话

    Returns:
        当前用户对象

    Raises:
        HTTPException: 认证失败时抛出异常
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = verify_token(credentials.credentials)
        if payload is None:
            raise credentials_exception

        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")

        if username is None or user_id is None:
            raise credentials_exception

    except Exception:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id, User.username == username).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户账户已被禁用"
        )

    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    获取当前活跃用户

    Args:
        current_user: 当前用户

    Returns:
        活跃用户对象
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户账户已被禁用"
        )
    return current_user

# 可选认证依赖（用于可选登录的接口）
def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User | None:
    """
    获取当前用户（可选认证）

    Args:
        credentials: HTTP认证凭据
        db: 数据库会话

    Returns:
        当前用户对象或None
    """
    if not credentials:
        return None

    try:
        payload = verify_token(credentials.credentials)
        if payload is None:
            return None

        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")

        if username is None or user_id is None:
            return None

        user = db.query(User).filter(User.id == user_id, User.username == username).first()
        return user if user and user.is_active else None

    except Exception:
        return None