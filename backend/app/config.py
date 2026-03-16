from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # OpenAI
    openai_api_key: str

    # Database
    database_url: str = "postgresql://hsuser:hspassword@localhost:5432/hsdb"

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection_training: str = "hs_training"
    qdrant_collection_corrections: str = "hs_corrections"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Classification
    confidence_threshold: float = 80.0
    top_k_results: int = 10
    enhancement_min_length: int = 15

    # Pipeline
    upload_dir: str = "uploads"
    results_dir: str = "results"
    max_file_size_mb: int = 50
    supported_file_types: List[str] = [".csv", ".xlsx", ".xls", ".txt"]
    polling_interval_ms: int = 2000

    # LLM
    llm_model: str = "gpt-4o"
    embedding_model: str = "text-embedding-3-small"
    batch_size_enrichment: int = 20
    batch_size_assessment: int = 50

    # CORS
    cors_origins: List[str] = ["*"]

    model_config = {"env_file": ".env", "case_sensitive": False}


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
