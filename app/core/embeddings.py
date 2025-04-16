import logging
import uuid
from typing import Dict, List, Optional, Union, Tuple

import numpy as np
import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.models.joke import Joke
from app.db.database import SessionLocal

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating and searching text embeddings using Chroma."""
    
    def __init__(self):
        """Initialize the embedding model and Chroma client."""
        # Set up sentence transformers model
        self.model_name = settings.EMBEDDING_MODEL
        self.sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=self.model_name)
        
        # Initialize Chroma client with persistence
        self.client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIRECTORY)
        
        # Create or get collections for jokes
        self.joke_collection = self.client.get_or_create_collection(
            name="jokes",
            embedding_function=self.sentence_transformer_ef
        )
        
        # Create or get collections for queries
        self.query_collection = self.client.get_or_create_collection(
            name="queries",
            embedding_function=self.sentence_transformer_ef
        )
        
        # Get the embedding dimension
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
    
    def add_joke_to_chroma(self, joke_id: int, text: str, metadata: dict = None) -> str:
        """
        Add a joke to the Chroma collection.
        
        Args:
            joke_id: The SQL database ID of the joke
            text: The joke text
            metadata: Additional metadata for the joke
            
        Returns:
            str: The Chroma document ID
        """
        doc_id = str(uuid.uuid4())
        
        # Create default metadata if not provided
        if metadata is None:
            metadata = {}
        
        # Add database ID to metadata    
        metadata["db_id"] = joke_id
        
        # Add to collection
        self.joke_collection.add(
            documents=[text],
            metadatas=[metadata],
            ids=[doc_id]
        )
        
        return doc_id
    
    def add_query_to_chroma(self, query_id: int, text: str, metadata: dict = None) -> str:
        """
        Add a query to the Chroma collection.
        
        Args:
            query_id: The SQL database ID of the query
            text: The query text
            metadata: Additional metadata for the query
            
        Returns:
            str: The Chroma document ID
        """
        doc_id = str(uuid.uuid4())
        
        # Create default metadata if not provided
        if metadata is None:
            metadata = {}
        
        # Add database ID to metadata    
        metadata["db_id"] = query_id
        
        # Add to collection
        self.query_collection.add(
            documents=[text],
            metadatas=[metadata],
            ids=[doc_id]
        )
        
        return doc_id
    
    def search(self, query_embedding: np.ndarray = None, query_text: str = None, k: int = 5) -> List[Tuple[int, float]]:
        """
        Search for most similar jokes using Chroma.
        
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
            
            # Use text directly if provided
            if query_text is not None:
                results = self.joke_collection.query(
                    query_texts=[query_text],
                    n_results=k
                )
            # Otherwise use the embedding
            else:
                # For embeddings, we need to normalize and convert to list
                query_norm = query_embedding / np.linalg.norm(query_embedding)
                query_list = query_norm.tolist()
                
                results = self.joke_collection.query(
                    query_embeddings=[query_list],
                    n_results=k
                )
            
            # Process results
            if not results["ids"]:
                return []
                
            # Extract joke IDs and distances
            joke_ids = results["metadatas"][0]  # First query result
            distances = results["distances"][0]  # First query result
            
            # Map to the expected return format
            return [(int(meta["db_id"]), float(1.0 - distance)) for meta, distance in zip(joke_ids, distances)]
            
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            return []
        finally:
            db.close()