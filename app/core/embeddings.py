import logging
from typing import Dict, List, Optional, Union, Tuple

import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy import func

from app.core.config import settings
from app.models.joke import Joke
from app.db.database import SessionLocal

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating and searching text embeddings."""
    
    def __init__(self):
        """Initialize the embedding model."""
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
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
    
    
    def search(self, query_embedding: np.ndarray, k: int = 5) -> List[Tuple[int, float]]:
        """
        Search for most similar jokes using pgvector.
        
        Args:
            query_embedding: The embedding vector to search with
            k: Number of results to return
            
        Returns:
            List[Tuple[int, float]]: List of (joke_id, similarity_score) tuples
        """
        db = SessionLocal()
        try:
            # Normalize the query vector for cosine similarity
            query_norm = query_embedding / np.linalg.norm(query_embedding)
            
            # Convert to list for database query
            query_vector = query_norm.tolist()
            
            # Query using pgvector's cosine similarity operator
            results = db.query(
                Joke.id,
                func.cosine_similarity(Joke.embedding, query_vector).label("similarity")
            ).order_by(
                func.cosine_similarity(Joke.embedding, query_vector).desc()
            ).limit(k).all()
            
            # Convert results to the expected format
            return [(joke_id, float(similarity)) for joke_id, similarity in results]
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            return []
        finally:
            db.close()