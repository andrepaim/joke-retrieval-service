import os
from typing import Any, Dict, Optional

from pydantic import BaseSettings, PostgresDsn, validator


class Settings(BaseSettings):
    # Service Settings
    PROJECT_NAME: str = "Joke Retrieval Service"
    
    # Database
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "joke_service")
    DATABASE_URI: Optional[PostgresDsn] = None
    
    # Chroma settings
    CHROMA_PERSIST_DIRECTORY: str = os.getenv("CHROMA_PERSIST_DIRECTORY", "chroma_db")
    
    # Vector search
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"  # Default SentenceTransformers model
    VECTOR_SIMILARITY_THRESHOLD: float = 0.6
    
    # gRPC server
    GRPC_HOST: str = os.getenv("GRPC_HOST", "0.0.0.0")
    GRPC_PORT: int = int(os.getenv("GRPC_PORT", 50051))
    
    @validator("DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()