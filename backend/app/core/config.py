"""
Core configuration settings for the AI Compliance Engine.
Uses Pydantic Settings for environment variable validation.
"""
from typing import List, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = "AI Compliance Engine"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8501"]
    
    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production-min-32-chars"
    JWT_SECRET_KEY: Optional[str] = "dev-jwt-secret-key-change-in-production-min-32-chars"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/compliance.db"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    
    # ChromaDB
    CHROMA_PERSIST_DIRECTORY: str = "./data/embeddings"
    CHROMA_COLLECTION_NAME: str = "compliance_documents"
    
    # AI/ML
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    LLM_PROVIDER: str = "openai"
    LLM_MODEL: str = "gpt-4o-mini"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    MAX_TOKENS: int = 4096
    TEMPERATURE: float = 0.1
    
    # OCR
    TESSERACT_PATH: Optional[str] = None
    OCR_LANGUAGE: str = "eng+hin"
    OCR_DPI: int = 300
    
    # Document Processing
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "docx", "xlsx", "png", "jpg", "jpeg", "xbrl"]
    BATCH_SIZE: int = 10
    MAX_CONCURRENT_TASKS: int = 5
    
    # Paths
    COMPLIANCE_RULES_PATH: str = "./backend/data/compliance_rules"
    UPLOAD_DIR: str = "./data/raw"
    PROCESSED_DIR: str = "./data/processed"
    REPORT_DIR: str = "./data/reports"
    
    # Monitoring
    PROMETHEUS_PORT: int = 9090
    ENABLE_METRICS: bool = True
    
    # Additional fields from .env
    ALGORITHM: str = "HS256"
    STREAMLIT_SERVER_PORT: int = 8501
    STREAMLIT_SERVER_ADDRESS: str = "0.0.0.0"
    
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow"
    )
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    @validator("ALLOWED_EXTENSIONS", pre=True)
    def assemble_extensions(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    def ensure_directories(self):
        """Create necessary directories if they don't exist."""
        directories = [
            self.UPLOAD_DIR,
            self.PROCESSED_DIR,
            self.REPORT_DIR,
            self.CHROMA_PERSIST_DIRECTORY,
            self.COMPLIANCE_RULES_PATH,
            "./logs"
        ]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)


# Global settings instance
settings = Settings()
settings.ensure_directories()
