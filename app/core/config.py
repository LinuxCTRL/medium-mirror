from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./articles.db"
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Medium Mirror"

settings = Settings()
