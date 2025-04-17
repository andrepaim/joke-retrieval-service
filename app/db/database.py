from typing import Generator
import logging

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings

logger = logging.getLogger(__name__)

# Create SQLAlchemy engine
engine = create_engine(settings.DATABASE_URI)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for database session.
    
    Yields:
        Session: Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def setup_vector_extension() -> None:
    """
    Set up the pgvector extension in the PostgreSQL database.
    This should be called once during database initialization.
    """
    try:
        # Create a raw connection
        with engine.connect() as conn:
            # Create the extension if it doesn't exist
            conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            conn.commit()
        
        logger.info("Successfully set up pgvector extension")
    except Exception as e:
        logger.error(f"Error setting up pgvector extension: {e}")
        raise