import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    APP_NAME: str = "ClipForge AI"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "clipforge-dev-secret-key-change-in-prod-xyz789")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Storage
    STORAGE_DIR: Path = BASE_DIR / "storage"
    VIDEOS_DIR: Path = BASE_DIR / "storage" / "videos"
    AUDIO_DIR: Path = BASE_DIR / "storage" / "audio"
    FRAMES_DIR: Path = BASE_DIR / "storage" / "frames"
    RENDERS_DIR: Path = BASE_DIR / "storage" / "renders"
    
    # Gemini API Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # Database: Supports SQLite by default or PostgreSQL via DATABASE_URL env var
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/clipforge.db")
    
    # Redis / Celery broker
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_TASK_ALWAYS_EAGER: bool = os.getenv("CELERY_TASK_ALWAYS_EAGER", "False").lower() in ("true", "1")
    
    # Whisper configuration
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "base")
    WHISPER_DEVICE: str = os.getenv("WHISPER_DEVICE", "cpu")
    WHISPER_COMPUTE_TYPE: str = os.getenv("WHISPER_COMPUTE_TYPE", "int8")

settings = Settings()

# Ensure storage directories exist
settings.VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
settings.AUDIO_DIR.mkdir(parents=True, exist_ok=True)
settings.FRAMES_DIR.mkdir(parents=True, exist_ok=True)
settings.RENDERS_DIR.mkdir(parents=True, exist_ok=True)
