from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserLogin, UserResponse
from datetime import datetime, timedelta
from app.config.settings import settings
from passlib.context import CryptContext
from jose import JWTError, jwt
from typing import Optional

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """加密密码"""
        return pwd_context.hash(password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """创建访问令牌"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
        return encoded_jwt

    async def register(self, user: UserCreate) -> UserResponse:
        """用户注册"""
        # TODO: 实现用户注册逻辑
        # 检查用户是否已存在
        # 加密密码
        # 创建用户
        # 返回用户信息
        return UserResponse(
            id=1,
            username=user.username,
            email=user.email,
            phone=user.phone,
            is_active=True,
            created_at=datetime.now()
        )

    async def login(self, user: UserLogin):
        """用户登录"""
        # TODO: 实现用户登录逻辑
        # 验证用户名和密码
        # 生成访问令牌
        access_token = self.create_access_token(data={"sub": user.username})
        return {"access_token": access_token, "token_type": "bearer"}