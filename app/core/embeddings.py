import logging
from typing import Dict, List, Optional, Union, Tuple

import numpy as np
from sqlalchemy import select, text
from sentence_transformers import SentenceTransformer
from pgvector.sqlalchemy import Vector

from app.core.config import settings
from app.models.joke import Joke, QueryLog
from app.db.database import SessionLocal

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating and searching text embeddings using pgvector."""
    
    def __init__(self):
        """Initialize the embedding model."""
        # Set up sentence transformers model
        self.model_name = settings.EMBEDDING_MODEL
        self.model = SentenceTransformer(self.model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
    
    def create_embedding(self, text: str) -> np.ndarray:
        """
        Create an embedding vector for a given text.
        
        Args:
            text: The text to encode
            
        Returns:
            np.ndarray: The embedding vector
        """
        return self.model.encode(text)
    
    def add_joke_embedding(self, db, joke_id: int, text: str) -> None:
        """
        Create and store an embedding for a joke.
        
        Args:
            db: Database session
            joke_id: The SQL database ID of the joke
            text: The joke text
        """
        try:
            # Get the joke from database
            joke = db.query(Joke).filter(Joke.id == joke_id).first()
            if not joke:
                logger.error(f"Joke with ID {joke_id} not found")
                return
            
            # Create embedding
            embedding = self.create_embedding(text)
            
            # Store the embedding
            joke.embedding = embedding.tolist()
            db.add(joke)
            logger.info(f"Added embedding for joke {joke_id}")
            
        except Exception as e:
            logger.error(f"Error adding joke embedding: {e}")
            raise
    
    def add_query_embedding(self, db, query_id: int, text: str) -> None:
        """
        Create and store an embedding for a query.
        
        Args:
            db: Database session
            query_id: The SQL database ID of the query
            text: The query text
        """
        try:
            # Get the query from database
            query_log = db.query(QueryLog).filter(QueryLog.id == query_id).first()
            if not query_log:
                logger.error(f"Query log with ID {query_id} not found")
                return
            
            # Create embedding
            embedding = self.create_embedding(text)
            
            # Store the embedding
            query_log.embedding = embedding.tolist()
            db.add(query_log)
            logger.info(f"Added embedding for query {query_id}")
            
        except Exception as e:
            logger.error(f"Error adding query embedding: {e}")
            raise
    
    def search(self, query_embedding: np.ndarray = None, query_text: str = None, k: int = 5) -> List[Tuple[int, float]]:
        """
        Search for most similar jokes using pgvector.
        
        Args:
            query_embedding: The embedding vector to search with (optional if query_text is provided)
            query_text: The text to search with (optional if query_embedding is provided)
            k: Number of results to return
            
        Returns:
            List[Tuple[int, float]]: List of (joke_id, similarity_score) tuples
        """
        db = SessionLocal()
        try:
            # Validate inputs
            if query_embedding is None and query_text is None:
                raise ValueError("Either query_embedding or query_text must be provided")
            
            # Generate embedding from text if needed
            if query_embedding is None:
                query_embedding = self.create_embedding(query_text)
            
            # Convert numpy array to list for database query
            embedding_list = query_embedding.tolist()
            
            # Query jokes with cosine similarity
            # Using raw SQL with text() for pgvector functions
            query = select(
                Joke.id,
                text("(embedding <=> :embedding) * -1 + 1 AS similarity")
            ).params(
                embedding=embedding_list
            ).order_by(
                text("similarity DESC")
            ).limit(k)
            
            results = db.execute(query).fetchall()
            
            # Process results - cosine similarity already provides values between 0-1
            return [(result.id, float(result.similarity)) for result in results]
            
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            return []
        finally:
            db.close()