"""配置管理 — 从环境变量加载配置"""
import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # 应用
    APP_NAME: str = "乐乐亲子乐园"
    DEBUG: bool = True
    SECRET_KEY: str = "dev-secret-key-change-in-production"

    # 数据库
    DATABASE_URL: str = "mysql+aiomysql://root:password@localhost:3306/lele_park"
    DB_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Dify
    DIFY_API_BASE: str = "http://localhost/v1"
    DIFY_APP_KEY_PLANNER: str = ""
    DIFY_APP_KEY_GUIDE: str = ""
    DIFY_APP_KEY_TICKET: str = ""

    # JWT
    JWT_SECRET: str = "jwt-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    class Config:
        # 使用绝对路径：Project/.env（相对于本文件为 ../../.env）
        env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
        env_file_encoding = "utf-8"


settings = Settings()
