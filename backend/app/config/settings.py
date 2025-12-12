from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # 应用配置
    app_name: str = "个人财务记账系统"
    debug: bool = True

    # 数据库配置
    database_url: str = "mysql://root:password@localhost:3306/finance_system"

    # Redis配置
    redis_url: str = "redis://localhost:6379/0"

    # JWT配置
    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # CORS配置
    allowed_origins: list = ["http://localhost:3000"]

    class Config:
        env_file = ".env"

settings = Settings()