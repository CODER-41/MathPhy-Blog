from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List


class Settings(BaseSettings):
    APP_NAME: str = "Physics Blog API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    DATABASE_URL: str
    DB_POOL_SIZE: int = 4
    DB_MAX_OVERFLOW: int = 2
    DB_POOL_TIMEOUT: int = 30

    REDIS_URL: str = "redis://localhost:6379"
    CACHE_POST_TTL: int = 300
    CACHE_LIST_TTL: int = 120
    CACHE_TAXONOMY_TTL: int = 3600
    CACHE_COMMENTS_TTL: int = 30

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173"]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v):
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    RATE_LIMIT_LOGIN: int = 10
    RATE_LIMIT_LOGIN_WINDOW: int = 900
    RATE_LIMIT_REGISTER: int = 5
    RATE_LIMIT_REGISTER_WINDOW: int = 3600

    FIRST_ADMIN_EMAIL: str = "admin@example.com"
    FIRST_ADMIN_PASSWORD: str = "changeme123"
    FIRST_ADMIN_USERNAME: str = "admin"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
