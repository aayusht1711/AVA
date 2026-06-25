"""
AVA Core Config — Environment Variables
All settings loaded from .env
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # App
    APP_NAME: str = "AVA"
    DEBUG: bool = False
    SECRET_KEY: str = "change-this-in-production"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://ava:ava_password@localhost:5432/ava_db"

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
    ]

    # JWT
    JWT_SECRET: str = "change-this-jwt-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # AI Models — Free tier
    GROQ_API_KEY: str = ""
    GEMINI_API_KEY: str = ""

    # Voice
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_VOICE_ID: str = "21m00Tcm4TlvDq8ikWAM"  # Rachel — warm, natural

    # Web Search
    TAVILY_API_KEY: str = ""

    # Code Execution
    E2B_API_KEY: str = ""

    # Vector Memory
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001

    # Google Cloud (for deployment)
    GCP_PROJECT_ID: str = ""
    GCS_BUCKET_NAME: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
