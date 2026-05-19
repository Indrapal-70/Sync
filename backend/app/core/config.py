from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://sync_user:sync_pass@localhost:5432/sync_db"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # Ollama (free local AI)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "mistral"
    thinker_model: str = "mistral"
    builder_model: str = "deepseek-coder:6.7b"
    fallback_model: str = "mistral"
    thinker_timeout: int = 90
    builder_timeout: int = 120
    
    # App
    app_env: str = "development"
    secret_key: str = "your-secret-key-change-this"
    review_pass_threshold: int = 65

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"

settings = Settings()