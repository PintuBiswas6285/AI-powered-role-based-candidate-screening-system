from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings

# Points to the backend directory regardless of where uvicorn is started from
BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "AI Candidate Screening API"
    frontend_origin: str = "http://localhost:5173"
    database_url: str = "sqlite:///./screening.db"

    knowledge_base_dir: Path = BASE_DIR / "data" / "knowledge_base"
    vector_store_path: Path = BASE_DIR / "data" / "vector_store.json"

    max_questions_per_session: int = 5
    embedding_dimensions: int = 384

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()