import os
from typing import Any, Dict, Optional

from pydantic import PostgresDsn, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Service Settings
    PROJECT_NAME: str = "Joke Retrieval Service"

    # Database
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "joke_service")
    DATABASE_URI: Optional[str] = None

    # Vector search
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"  # Default SentenceTransformers model
    EMBEDDING_DIMENSION: int = 384  # Dimension of the embedding vectors for the model
    VECTOR_SIMILARITY_THRESHOLD: float = 0.05

    # gRPC server
    GRPC_HOST: str = os.getenv("GRPC_HOST", "0.0.0.0")
    GRPC_PORT: int = int(os.getenv("GRPC_PORT", 50051))

    @field_validator("DATABASE_URI", mode="before")
    def assemble_db_connection(cls, v: Optional[str], info: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        values = info.data
        user = values.get("POSTGRES_USER", "")
        password = values.get("POSTGRES_PASSWORD", "")
        host = values.get("POSTGRES_SERVER", "")
        db = values.get("POSTGRES_DB", "")

        # Construct DSN string manually as the API changed in Pydantic v2
        return f"postgresql://{user}:{password}@{host}/{db}"

    model_config = {
        "case_sensitive": True,
        "env_file": ".env",
        "extra": "ignore",  # Allow extra fields
    }


settings = Settings()
