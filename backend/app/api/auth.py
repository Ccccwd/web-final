from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.schemas.user import (
    UserCreate, UserLogin, UserResponse, Token,
    PasswordResetRequest, PasswordReset
)
from app.services.auth_service import AuthService
from app.core.responses import success_response
from app.core.exceptions import BusinessException
from app.core.dependencies import get_current_active_user

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

@router.post("/password-reset-request")
async def request_password_reset(
    request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """请求密码重置"""
    try:
        auth_service = AuthService(db)
        result = await auth_service.request_password_reset(request.email)
        return success_response(message=result)
    except Exception as e:
        if isinstance(e, BusinessException):
            raise e
        raise BusinessException(f"请求密码重置失败: {str(e)}")

@router.post("/password-reset")
async def reset_password(
    reset_data: PasswordReset,
    db: Session = Depends(get_db)
):
    """重置密码"""
    try:
        auth_service = AuthService(db)
        result = await auth_service.reset_password(reset_data.token, reset_data.new_password)
        return success_response(message="密码重置成功")
    except Exception as e:
        if isinstance(e, BusinessException):
            raise e
        raise BusinessException(f"密码重置失败: {str(e)}")

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取当前用户信息"""
    try:
        auth_service = AuthService(db)
        result = await auth_service.get_user_profile(current_user.id)
        return success_response(data=result.dict(), message="获取用户信息成功")
    except Exception as e:
        if isinstance(e, BusinessException):
            raise e
        raise BusinessException(f"获取用户信息失败: {str(e)}")

@router.put("/me", response_model=UserResponse)
async def update_current_user_info(
    user_update: dict,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新当前用户信息"""
    try:
        auth_service = AuthService(db)
        result = await auth_service.update_user_profile(current_user.id, user_update)
        return success_response(data=result.dict(), message="更新用户信息成功")
    except Exception as e:
        if isinstance(e, BusinessException):
            raise e
        raise BusinessException(f"更新用户信息失败: {str(e)}")