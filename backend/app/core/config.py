from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://sync_user:sync_pass@localhost:5432/sync_db"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # Ollama (free local AI)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "mistral"
    
    # App
    app_env: str = "development"
    secret_key: str = "your-secret-key-change-this"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"

settings = Settings()