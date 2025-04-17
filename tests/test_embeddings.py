import os
import sys
import unittest
import numpy as np
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock pgvector.sqlalchemy.Vector to avoid import errors in tests
sys.modules['pgvector'] = MagicMock()
sys.modules['pgvector.sqlalchemy'] = MagicMock()
sys.modules['pgvector.sqlalchemy.Vector'] = MagicMock()

from app.core.embeddings import EmbeddingService
from app.models.joke import Joke


class TestEmbeddingService(unittest.TestCase):
    """Test cases for the EmbeddingService class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create embedding service
        self.embedding_service = EmbeddingService()
    
    def test_create_embedding(self):
        """Test creating an embedding from text."""
        text = "This is a test joke"
        embedding = self.embedding_service.create_embedding(text)
        
        # Verify embedding is a numpy array with the correct dimensions
        self.assertIsInstance(embedding, np.ndarray)
        self.assertEqual(embedding.shape[0], self.embedding_service.embedding_dim)
    
    @patch('app.core.embeddings.SessionLocal')
    def test_add_joke_embedding(self, mock_session_local):
        """Test adding an embedding to a joke."""
        # Setup
        mock_db = MagicMock()
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        
        # Mock joke
        mock_joke = MagicMock()
        mock_joke.id = 1
        
        # Mock db query
        mock_db.query.return_value.filter.return_value.first.return_value = mock_joke
        
        # Test text
        text = "This is a test joke"
        
        # Call method
        self.embedding_service.add_joke_embedding(mock_db, 1, text)
        
        # Verify joke.embedding was updated
        self.assertTrue(hasattr(mock_joke, 'embedding'))
        self.assertTrue(mock_db.add.called)
    
    @patch('app.core.embeddings.SessionLocal')
    def test_search(self, mock_session_local):
        """Test searching for similar jokes using pgvector."""
        # Mock the database session
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        
        # Mock query execution results
        mock_result1 = MagicMock()
        mock_result1.id = 1
        mock_result1.similarity = 0.95
        
        mock_result2 = MagicMock()
        mock_result2.id = 2
        mock_result2.similarity = 0.85
        
        mock_result3 = MagicMock()
        mock_result3.id = 3
        mock_result3.similarity = 0.75
        
        mock_session.execute.return_value.fetchall.return_value = [
            mock_result1, mock_result2, mock_result3
        ]
        
        # Search for jokes using text
        results = self.embedding_service.search(query_text="funny joke", k=3)
        
        # Verify execution was called
        self.assertTrue(mock_session.execute.called)
        
        # Verify returned the expected format
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0], (1, 0.95))
        self.assertEqual(results[1], (2, 0.85))
        self.assertEqual(results[2], (3, 0.75))


if __name__ == "__main__":
    unittest.main()