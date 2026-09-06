from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "Verdant Document Hub"
    environment: str = "development"
    api_prefix: str = "/api"

    verdant_db_host: str = "localhost"
    verdant_db_port: int = 5432
    verdant_db_user: str = "verdant_app"
    verdant_db_password: str = "change-this-local-password"
    verdant_db_name: str = "verdant"
    verdant_db_sslmode: str = "prefer"

    jwt_secret: str = Field(
        default="change-this-development-secret-at-least-32-characters",
        min_length=32,
    )
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 480

    storage_root: Path = BACKEND_DIR / "storage"
    max_upload_size_mb: int = Field(default=100, ge=1, le=2048)
    frontend_origin: str = "http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def database_url(self) -> URL:
        """Build a safely escaped SQLAlchemy PostgreSQL URL."""

        return URL.create(
            drivername="postgresql+psycopg",
            username=self.verdant_db_user,
            password=self.verdant_db_password,
            host=self.verdant_db_host,
            port=self.verdant_db_port,
            database=self.verdant_db_name,
            query={"sslmode": self.verdant_db_sslmode},
        )

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    configured = Settings()
    configured.storage_root.mkdir(parents=True, exist_ok=True)
    return configured


settings = get_settings()
