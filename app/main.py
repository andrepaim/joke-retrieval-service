import asyncio
import logging
import os
import sys
from typing import Optional

import typer

from app.api.grpc_server import serve as start_grpc_server
from app.core.config import settings
from app.db.database import engine, setup_vector_extension
from app.models.joke import Base

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# Create Typer CLI app
app = typer.Typer()


def init_db() -> None:
    """Initialize the database with tables and vector extension."""
    try:
        # Set up pgvector extension
        setup_vector_extension()
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables and vector extension created")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


@app.command()
def start_server(
    init_database: bool = typer.Option(False, "--init-db", help="Initialize the database")
) -> None:
    """Start the joke retrieval gRPC service."""
    if init_database:
        logger.info("Initializing database...")
        init_db()
    
    logger.info("Starting gRPC server...")
    start_grpc_server()


@app.command()
def init_database() -> None:
    """Initialize the database with tables."""
    logger.info("Initializing database...")
    init_db()


@app.command()
def generate_proto() -> None:
    """Generate Python code from proto file."""
    try:
        proto_dir = os.path.join(os.getcwd(), "proto")
        proto_file = os.path.join(proto_dir, "joke_service.proto")
        
        if not os.path.exists(proto_file):
            logger.error(f"Proto file not found: {proto_file}")
            return
        
        # Generate Python code from proto
        logger.info(f"Generating Python code from {proto_file}...")
        cmd = f"python -m grpc_tools.protoc -I {proto_dir} --python_out=. --grpc_python_out=. {proto_file}"
        os.system(cmd)
        logger.info("Proto code generation completed")
    except Exception as e:
        logger.error(f"Error generating proto code: {e}")


if __name__ == "__main__":
    app()