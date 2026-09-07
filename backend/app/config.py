from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[1]

class Settings(BaseSettings):
    app_name: str = "Verdant Document Hub"
    api_prefix: str = "/api"
    database_url: str = "mysql+pymysql://verdant:verdant@localhost:3306/verdant_app?charset=utf8mb4"
    jwt_secret: str = "change-this-development-secret-at-least-32-chars"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 480
    storage_root: Path = BASE_DIR / "storage"
    frontend_origin: str = "http://localhost:3000"
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
settings.storage_root.mkdir(parents=True, exist_ok=True)


