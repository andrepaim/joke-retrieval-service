import os
import sys
import unittest
import uuid
import numpy as np
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.embeddings import EmbeddingService
from app.models.joke import Joke


class TestEmbeddingService(unittest.TestCase):
    """Test cases for the EmbeddingService class."""
    
    @patch('app.core.embeddings.chromadb.PersistentClient')
    def setUp(self, mock_chroma_client):
        """Set up test fixtures."""
        # Mock Chroma client and collections
        self.mock_client = MagicMock()
        mock_chroma_client.return_value = self.mock_client
        
        self.mock_joke_collection = MagicMock()
        self.mock_query_collection = MagicMock()
        
        self.mock_client.get_or_create_collection.side_effect = [
            self.mock_joke_collection,
            self.mock_query_collection
        ]
        
        self.embedding_service = EmbeddingService()
    
    def test_create_embedding(self):
        """Test creating an embedding from text."""
        text = "This is a test joke"
        embedding = self.embedding_service.create_embedding(text)
        
        # Verify embedding is a numpy array with the correct dimensions
        self.assertIsInstance(embedding, np.ndarray)
        self.assertEqual(embedding.shape[0], self.embedding_service.embedding_dim)
    
    def test_add_joke_to_chroma(self):
        """Test adding a joke to Chroma."""
        # Setup
        joke_id = 1
        text = "This is a test joke"
        
        # Call method
        with patch('uuid.uuid4', return_value=uuid.UUID('12345678-1234-5678-1234-567812345678')):
            doc_id = self.embedding_service.add_joke_to_chroma(joke_id, text)
        
        # Verify Chroma collection was called correctly
        self.mock_joke_collection.add.assert_called_once()
        args, kwargs = self.mock_joke_collection.add.call_args
        
        # Verify document was added with correct metadata
        self.assertEqual(kwargs['documents'], [text])
        self.assertEqual(kwargs['ids'], ['12345678-1234-5678-1234-567812345678'])
        self.assertEqual(kwargs['metadatas'][0]['db_id'], joke_id)
        
        # Verify return value
        self.assertEqual(doc_id, '12345678-1234-5678-1234-567812345678')
    
    @patch('app.core.embeddings.SessionLocal')
    def test_search(self, mock_session_local):
        """Test searching for similar jokes using Chroma."""
        # Mock the database session
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        
        # Mock the Chroma query results
        self.mock_joke_collection.query.return_value = {
            'ids': [['doc1', 'doc2', 'doc3']],
            'distances': [[0.05, 0.15, 0.25]],  # Distance (lower is better, convert to similarity)
            'metadatas': [[
                {'db_id': 1},
                {'db_id': 2},
                {'db_id': 3}
            ]]
        }
        
        # Search for jokes using text
        results = self.embedding_service.search(query_text="funny joke", k=3)
        
        # Verify Chroma was called correctly
        self.mock_joke_collection.query.assert_called_once()
        args, kwargs = self.mock_joke_collection.query.call_args
        
        # Verify returned the expected format
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0], (1, 0.95))  # 1 - 0.05 = 0.95
        self.assertEqual(results[1], (2, 0.85))  # 1 - 0.15 = 0.85
        self.assertEqual(results[2], (3, 0.75))  # 1 - 0.25 = 0.75


if __name__ == "__main__":
    unittest.main()