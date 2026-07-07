from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """App settings — override via environment variables or .env file."""

    APP_NAME: str = "Lift"
    API_V1_PREFIX: str = "/api/v1"

    # dev ใช้ SQLite, production/Atlas เปลี่ยนเป็น postgresql+psycopg://... ได้เลย
    DATABASE_URL: str = "sqlite:///./lift.db"

    SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"


settings = Settings()
