from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://autoscoring:autoscoring@db:5432/autoscoring"
    secret_key: str = "fyp-autoscoring-secret-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    scoring_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    # Scoring hyperparameters (must sum to 1.0 for a pure convex combination)
    weight_semantic: float = 0.60
    weight_keywords: float = 0.25
    weight_coherence: float = 0.15
    concept_match_threshold: float = 0.72
    concept_partial_threshold: float = 0.45
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    upload_dir: str = "uploads"
    max_upload_mb: int = 15
    student_ocr_engine: str = "trocr"
    question_ocr_engine: str = "easyocr"
    trocr_model: str = "microsoft/trocr-base-handwritten"
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"

    class Config:
        env_file = ".env"


settings = Settings()
