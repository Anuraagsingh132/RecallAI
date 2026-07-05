from pydantic_settings import BaseSettings
from pydantic import model_validator
from typing import Optional

class Settings(BaseSettings):
    ENV: str = "development"
    MAX_UPLOAD_SIZE_MB: int = 10
    
    JWT_SECRET: Optional[str] = None
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/recallai"
    QDRANT_URL: str = "http://localhost:6333"
    SENTRY_DSN: Optional[str] = None
    FRONTEND_CORS_ORIGIN: str = "http://localhost:3000"
    GROQ_API_KEY: Optional[str] = None
    
    @property
    def MAX_UPLOAD_SIZE_BYTES(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    # Ingestion Settings
    EMBEDDING_BATCH_SIZE: int = 100
    
    @model_validator(mode='after')
    def validate_secrets(self) -> 'Settings':
        if self.ENV == 'production' and not self.JWT_SECRET:
            raise ValueError("JWT_SECRET must be set in production environment")
        if not self.JWT_SECRET:
            self.JWT_SECRET = "dummy"
        return self
    
    class Config:
        env_file = ".env"

settings = Settings()
