from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.services.auth_service import AuthService
from app.core.responses import success_response
from app.core.exceptions import BusinessException

router = APIRouter()

@router.post("/register")
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    try:
        auth_service = AuthService(db)
        result = await auth_service.register(user)
        return success_response(data=result.dict(), message="注册成功")
    except Exception as e:
        if isinstance(e, BusinessException):
            raise e
        raise BusinessException(f"注册失败: {str(e)}")

@router.post("/login")
async def login(user: UserLogin, db: Session = Depends(get_db)):
    """用户登录"""
    try:
        auth_service = AuthService(db)
        result = await auth_service.login(user)
        return success_response(data=result.dict(), message="登录成功")
    except Exception as e:
        if isinstance(e, BusinessException):
            raise e
        raise BusinessException(f"登录失败: {str(e)}")

@router.post("/refresh")
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """刷新访问令牌"""
    try:
        auth_service = AuthService(db)
        result = await auth_service.refresh_token(refresh_token)
        return success_response(data=result.dict(), message="令牌刷新成功")
    except Exception as e:
        if isinstance(e, BusinessException):
            raise e
        raise BusinessException(f"令牌刷新失败: {str(e)}")

@router.post("/logout")
async def logout():
    """用户登出"""
    return success_response(message="退出登录成功")