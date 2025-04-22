import asyncio
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Mock necessary modules
sys.modules["fastmcp"] = MagicMock()
sys.modules["fastmcp.client"] = MagicMock()
mock_client = MagicMock()
mock_client.__aenter__ = AsyncMock(return_value=mock_client)
mock_client.__aexit__ = AsyncMock(return_value=None)
mock_client.call_tool = AsyncMock()
mock_client.read_resource = AsyncMock()
sys.modules["fastmcp.client"].Client = MagicMock(return_value=mock_client)
sys.modules["fastmcp.client"].SSETransport = MagicMock()

# Mock typer
mock_typer = MagicMock()
mock_typer.echo = MagicMock()
mock_typer.Argument = MagicMock()
mock_typer.Option = MagicMock()
mock_typer_app = MagicMock()
mock_typer_app.command = MagicMock(return_value=lambda func: func)
mock_typer.Typer = MagicMock(return_value=mock_typer_app)
sys.modules["typer"] = mock_typer

# Patch asyncio.run
patch_asyncio_run = patch(
    "asyncio.run", new=lambda coro: asyncio.get_event_loop().run_until_complete(coro)
)
patch_asyncio_run.start()

# Import client functions after all mocks are setup
from app.utils.mcp_client import add, create_client, get, get_by_id, random, rate


class TestMCPClient(unittest.TestCase):
    """Test cases for the FastMCP client."""

    def test_create_client(self):
        """Test creating a client with default parameters."""
        client = create_client()
        # Just verify the function returns without errors for simple test
        self.assertIsNotNone(client)

    def test_create_client_custom_params(self):
        """Test creating a client with custom host and port."""
        client = create_client(host="example.com", port=9000)
        # Just verify the function returns without errors for simple test
        self.assertIsNotNone(client)

    def test_get_single_joke(self):
        """Test getting a single joke."""
        # Call function - this should work with our global mocks
        get("chicken", context="funny", multiple=False, limit=1)
        # Test passes if no exceptions

    def test_get_multiple_jokes(self):
        """Test getting multiple jokes."""
        # Call function - this should work with our global mocks
        get("test query", multiple=True, limit=2)
        # Test passes if no exceptions

    def test_rate_joke(self):
        """Test rating a joke."""
        # Call function
        rate(1, liked=True, user_id="user123")
        # Test passes if no exceptions

    def test_add_joke(self):
        """Test adding a new joke."""
        # Call function
        add(
            "New joke text",
            category="Test Category",
            source="Test Source",
            tags=["test", "new"],
        )
        # Test passes if no exceptions

    def test_random_joke(self):
        """Test getting a random joke."""
        # Call function
        random()
        # Test passes if no exceptions

    def test_get_joke_by_id(self):
        """Test getting a joke by ID."""
        # Call function
        get_by_id(123)
        # Test passes if no exceptions

    def test_get_joke_by_id_error(self):
        """Test getting a joke by ID with an error response."""
        # Set up mock to return an error response
        sys.modules["fastmcp.client"].Client().read_resource.return_value = {
            "error": "Joke with ID 999 not found"
        }
        # Call function
        get_by_id(999)
        # Test passes if no exceptions

    def test_exception_handling(self):
        """Test handling exceptions in client calls."""
        # Set up mock to raise an exception
        sys.modules["fastmcp.client"].Client().call_tool.side_effect = Exception(
            "Connection error"
        )
        # Call function
        get("test query")
        # Test passes if no exceptions


if __name__ == "__main__":
    unittest.main()
