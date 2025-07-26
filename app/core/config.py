import os
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from pydantic import field_validator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # 应用基础设置
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "淘宝智能搜索助手"
    VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=True, description="Debug mode")  # 启用DEBUG模式
    ENVIRONMENT: str = Field(default="development", description="Environment: development, staging, production")
    
    # 日志设置
    LOG_LEVEL: str = Field(default="DEBUG", description="Logging level")  # 设置为DEBUG级别
    LOG_FILE: str = Field(default="logs/app.log", description="Log file path")
    
    # CORS设置
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:8000", "http://localhost:3000"],
        description="Allowed CORS origins"
    )
    
    # 数据库设置
    DATABASE_URL: str = Field(
        default="sqlite:///./taobao_agent.db",
        description="Database connection URL"
    )
    DATABASE_POOL_SIZE: int = Field(default=10, description="Database connection pool size")
    DATABASE_MAX_OVERFLOW: int = Field(default=20, description="Database max overflow connections")
    
    # JWT设置
    JWT_SECRET: str = Field(
        default="your-secret-key-change-in-production",
        description="JWT secret key"
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30, 
        description="Access token expiration time in minutes"
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7,
        description="Refresh token expiration time in days"
    )
    
    # AI模型设置
    MODEL_PROVIDER: str = Field(default="openai", description="Model provider: openai, qwen")
    
    # OpenAI设置
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API key")
    OPENAI_MODEL: str = Field(default="gpt-3.5-turbo", description="OpenAI model to use")
    OPENAI_MAX_TOKENS: int = Field(default=1000, description="Max tokens for OpenAI responses")
    OPENAI_TEMPERATURE: float = Field(default=0.7, description="OpenAI temperature setting")
    
    # Qwen/DashScope设置
    DASHSCOPE_API_KEY: str = Field(default="", description="DashScope API key for Qwen models")
    QWEN_MODEL: str = Field(default="qwen-turbo", description="Qwen model to use")
    QWEN_MAX_TOKENS: int = Field(default=1000, description="Max tokens for Qwen responses")
    QWEN_TEMPERATURE: float = Field(default=0.7, description="Qwen temperature setting")
    
    # Taobao API配置
    TAOBAO_APP_KEY: str = Field(default="", description="Taobao app key")
    TAOBAO_APP_SECRET: str = Field(default="", description="Taobao app secret")
    TAOBAO_ADZONE_ID: str = Field(default="", description="Taobao adzone id (推广位ID)")
    TAOBAO_MATERIAL_ID: str = Field(default="", description="Taobao material id (物料ID)")
    TAOBAO_API_TIMEOUT: int = Field(default=30, description="Taobao API timeout in seconds")
    
    # 缓存设置
    REDIS_URL: str = Field(default="redis://localhost:6379", description="Redis connection URL")
    CACHE_TTL: int = Field(default=3600, description="Default cache TTL in seconds")
    
    # 安全设置
    ALLOWED_HOSTS: List[str] = Field(default=["*"], description="Allowed hosts")
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, description="Rate limit per minute")
    
    # 文件上传设置
    MAX_FILE_SIZE: int = Field(default=10 * 1024 * 1024, description="Max file size in bytes (10MB)")
    UPLOAD_DIR: str = Field(default="uploads", description="Upload directory")
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    @field_validator("JWT_SECRET")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("JWT secret must be at least 32 characters long")
        return v
    
    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed_envs = ["development", "staging", "production"]
        if v not in allowed_envs:
            raise ValueError(f"Environment must be one of: {allowed_envs}")
        return v
    
    def create_upload_dir(self) -> None:
        """Create upload directory if it doesn't exist"""
        Path(self.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"
    
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

# 创建全局设置对象
settings = Settings()