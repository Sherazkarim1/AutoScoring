from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://autoscoring:autoscoring@db:5432/autoscoring"
    secret_key: str = "fyp-autoscoring-secret-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    scoring_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    upload_dir: str = "uploads"
    max_upload_mb: int = 15

    class Config:
        env_file = ".env"


settings = Settings()
