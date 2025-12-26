from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    # 应用配置
    app_name: str = "个人财务记账系统"
    debug: bool = True

    # 数据库配置
    database_url: str = "mysql://root:root123456@localhost:3307/finance_system?charset=utf8mb4"

    # Redis配置
    redis_url: str = "redis://localhost:6380/0"

    # JWT配置
    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # CORS配置
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"

    # 文件导出配置
    export_path: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "exports")
    
    @property
    def cors_origins(self) -> list[str]:
        """将逗号分隔的字符串转换为列表"""
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    model_config = SettingsConfigDict(env_file=".env",extra="ignore")

settings = Settings()