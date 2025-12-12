from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.models.user import User
from app.utils.security import get_password_hash, verify_password
from app.utils.jwt_utils import create_access_token, create_refresh_token
from app.config.settings import settings
from datetime import datetime, timedelta
from typing import Optional

class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return self.db.query(User).filter(User.username == username).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        return self.db.query(User).filter(User.email == email).first()

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """验证用户身份"""
        user = self.get_user_by_username(username)
        if not user:
            return None
        if not verify_password(password, user.password):
            return None
        return user

    async def register(self, user_create: UserCreate) -> UserResponse:
        """用户注册"""
        # 检查用户名是否已存在
        if self.get_user_by_username(user_create.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )

        # 检查邮箱是否已存在
        if self.get_user_by_email(user_create.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已存在"
            )

        # 创建新用户
        hashed_password = get_password_hash(user_create.password)
        db_user = User(
            username=user_create.username,
            email=user_create.email,
            password=hashed_password,
            phone=user_create.phone,
            is_active=True
        )

        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)

        return UserResponse(
            id=db_user.id,
            username=db_user.username,
            email=db_user.email,
            phone=db_user.phone,
            avatar=db_user.avatar,
            is_active=db_user.is_active,
            created_at=db_user.created_at
        )

    async def login(self, user_login: UserLogin) -> Token:
        """用户登录"""
        user = self.authenticate_user(user_login.username, user_login.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户账户已被禁用"
            )

        # 创建访问令牌
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": user.username, "user_id": user.id},
            expires_delta=access_token_expires
        )

        # 创建刷新令牌
        refresh_token = create_refresh_token(
            data={"sub": user.username, "user_id": user.id}
        )

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )

    async def refresh_token(self, refresh_token: str) -> Token:
        """刷新访问令牌"""
        from app.utils.jwt_utils import verify_token

        payload = verify_token(refresh_token)
        if payload is None or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的刷新令牌",
                headers={"WWW-Authenticate": "Bearer"},
            )

        username = payload.get("sub")
        user = self.get_user_by_username(username)
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在或已被禁用"
            )

        # 创建新的访问令牌
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": user.username, "user_id": user.id},
            expires_delta=access_token_expires
        )

        # 创建新的刷新令牌
        new_refresh_token = create_refresh_token(
            data={"sub": user.username, "user_id": user.id}
        )

        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer"
        )

    async def request_password_reset(self, email: str) -> str:
        """请求密码重置"""
        user = self.get_user_by_email(email)
        if not user:
            # 为了安全，即使用户不存在也返回成功
            return "如果该邮箱存在，重置链接已发送"

        # 生成重置令牌
        from app.utils.security import generate_password_reset_token
        reset_token = generate_password_reset_token(email)

        # 这里应该发送邮件，暂时只返回令牌（实际应用中应该通过邮件发送）
        # TODO: 集成邮件服务
        print(f"密码重置令牌: {reset_token}")  # 临时用于调试

        return "如果该邮箱存在，重置链接已发送"

    async def reset_password(self, token: str, new_password: str) -> bool:
        """重置密码"""
        from app.utils.jwt_utils import verify_token

        try:
            payload = verify_token(token)
            if payload is None or payload.get("type") != "password_reset":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="无效的重置令牌"
                )

            email = payload.get("sub")
            user = self.get_user_by_email(email)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="用户不存在"
                )

            # 更新密码
            user.password = get_password_hash(new_password)
            self.db.commit()

            return True

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="重置密码失败"
            )

    async def get_user_profile(self, user_id: int) -> UserResponse:
        """获取用户信息"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            phone=user.phone,
            avatar=user.avatar,
            is_active=user.is_active,
            created_at=user.created_at
        )

    async def update_user_profile(self, user_id: int, user_update: dict) -> UserResponse:
        """更新用户信息"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        # 检查用户名是否被其他用户使用
        if "username" in user_update and user_update["username"] != user.username:
            existing_user = self.get_user_by_username(user_update["username"])
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="用户名已存在"
                )

        # 检查邮箱是否被其他用户使用
        if "email" in user_update and user_update["email"] != user.email:
            existing_user = self.get_user_by_email(user_update["email"])
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="邮箱已存在"
                )

        # 更新用户信息
        for key, value in user_update.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)

        self.db.commit()
        self.db.refresh(user)

        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            phone=user.phone,
            avatar=user.avatar,
            is_active=user.is_active,
            created_at=user.created_at
        )