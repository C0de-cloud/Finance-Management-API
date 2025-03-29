from typing import Any, Dict, Optional, List
from pydantic import BaseSettings, validator
from functools import lru_cache
import os


class Settings(BaseSettings):
    API_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Finance Manager API"
    PROJECT_VERSION: str = "1.0.0"
    PROJECT_DESCRIPTION: str = "API сервис для управления личными финансами"
    
    # MongoDB configuration
    MONGODB_URL: str
    MONGODB_DB_NAME: str
    
    # JWT Configuration
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    
    # Debug
    DEBUG: bool = False
    
    # Валидаторы
    @validator("MONGODB_URL", pre=True)
    def validate_mongodb_url(cls, v: Optional[str]) -> str:
        if not v:
            raise ValueError("MongoDB URL обязателен")
        return v
    
    @validator("MONGODB_DB_NAME", pre=True)
    def validate_mongodb_db_name(cls, v: Optional[str]) -> str:
        if not v:
            raise ValueError("MongoDB DB Name обязателен")
        return v
    
    @validator("SECRET_KEY", pre=True)
    def validate_secret_key(cls, v: Optional[str]) -> str:
        if not v or len(v) < 32:
            raise ValueError("SECRET_KEY должен быть не менее 32 символов")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Возвращает объект настроек приложения с кешированием для производительности
    """
    return Settings() 