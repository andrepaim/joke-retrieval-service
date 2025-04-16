import os
import sys
import unittest
import numpy as np
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.embeddings import EmbeddingService
from app.models.joke import Joke


class TestEmbeddingService(unittest.TestCase):
    """Test cases for the EmbeddingService class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.embedding_service = EmbeddingService()
    
    def test_create_embedding(self):
        """Test creating an embedding from text."""
        text = "This is a test joke"
        embedding = self.embedding_service.create_embedding(text)
        
        # Verify embedding is a numpy array with the correct dimensions
        self.assertIsInstance(embedding, np.ndarray)
        self.assertEqual(embedding.shape[0], self.embedding_service.embedding_dim)
    
    def test_update_index(self):
        """Test updating the index is now a no-op but maintains API compatibility."""
        # Create mock jokes
        jokes = []
        for i in range(5):
            embedding = np.random.randn(self.embedding_service.embedding_dim).astype(np.float32)
            joke = Joke(id=i, text=f"Test joke {i}", category="test", embedding=embedding)
            jokes.append(joke)
        
        # Test that update_index runs without error (should be a no-op now)
        try:
            self.embedding_service.update_index(jokes)
            # If we get here, the test passed
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"update_index raised exception {e}")
    
    @patch('app.core.embeddings.SessionLocal')
    def test_search(self, mock_session_local):
        """Test searching for similar jokes using pgvector."""
        # Mock the database session
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        
        # Mock the query results
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = [
            (1, 0.95),
            (2, 0.85),
            (3, 0.75)
        ]
        
        # Create a query embedding
        query_embedding = np.random.randn(self.embedding_service.embedding_dim).astype(np.float32)
        
        # Search for similar jokes
        results = self.embedding_service.search(query_embedding, k=3)
        
        # Verify results
        self.assertEqual(len(results), 3)
        for joke_id, score in results:
            self.assertIn(joke_id, [1, 2, 3])
            self.assertIsInstance(score, float)


if __name__ == "__main__":
    unittest.main()