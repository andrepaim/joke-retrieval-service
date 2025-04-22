import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Mock necessary modules
sys.modules["grpc"] = MagicMock()
mock_typer = MagicMock()
mock_typer.Option = MagicMock()
mock_typer.Typer.return_value.command = MagicMock(return_value=lambda func: func)
sys.modules["typer"] = mock_typer
sys.modules["uvicorn"] = MagicMock()

# Patch dependencies before import
with patch("app.main.start_mcp_server") as mock_mcp_server, \
     patch("app.main.start_grpc_server") as mock_grpc_server, \
     patch("app.main.setup_vector_extension") as mock_vector_setup, \
     patch("app.main.Base") as mock_base, \
     patch("app.main.os.system") as mock_os_system, \
     patch("app.main.os.path.exists", return_value=True):
    
    # Import app after mocks
    from app.main import (
        generate_proto,
        init_database,
        start_server,
    )


class TestMain(unittest.TestCase):
    """Test cases for the main application entry points."""

    @patch("app.main.start_mcp_server")
    @patch("app.main.start_grpc_server")
    @patch("app.main.setup_vector_extension")
    @patch("app.main.Base")
    @patch("app.main.os.system")
    def test_generate_proto(self, mock_os_system, mock_base, mock_vector_setup, mock_grpc_server, mock_mcp_server):
        """Test proto file generation."""
        # Call the function
        generate_proto()
        
        # Verify os.system was called with expected command
        mock_os_system.assert_called_once()
        # The call should contain grpc_tools.protoc
        call_args = mock_os_system.call_args.args[0]
        self.assertTrue("grpc_tools.protoc" in call_args)

    @patch("app.main.start_mcp_server")
    @patch("app.main.start_grpc_server")
    @patch("app.main.setup_vector_extension")
    @patch("app.main.Base")
    def test_init_database(self, mock_base, mock_vector_setup, mock_grpc_server, mock_mcp_server):
        """Test database initialization."""
        # Call the function
        init_database()
        
        # Verify vector extension was set up
        mock_vector_setup.assert_called_once()
        # Verify tables were created
        mock_base.metadata.create_all.assert_called_once()

    @patch("app.main.start_mcp_server")
    @patch("app.main.start_grpc_server")
    @patch("app.main.setup_vector_extension")
    @patch("app.main.Base")
    def test_start_grpc_server(self, mock_base, mock_vector_setup, mock_grpc_server, mock_mcp_server):
        """Test starting the gRPC server."""
        # Call the function
        start_server(server_type="grpc")
        
        # Verify the gRPC server was started
        mock_grpc_server.assert_called_once()
        # Verify MCP server was not started
        mock_mcp_server.assert_not_called()

    @patch("app.main.start_mcp_server")
    @patch("app.main.start_grpc_server")
    @patch("app.main.setup_vector_extension")
    @patch("app.main.Base")
    def test_start_mcp_server(self, mock_base, mock_vector_setup, mock_grpc_server, mock_mcp_server):
        """Test starting the FastMCP server."""
        # Call the function with a custom port
        start_server(server_type="mcp", port=8080)
        
        # Verify MCP server was called (without checking exact args)
        mock_mcp_server.assert_called_once()
        # Verify gRPC server was not started
        mock_grpc_server.assert_not_called()

    @patch("app.main.start_mcp_server")
    @patch("app.main.start_grpc_server")
    @patch("app.main.setup_vector_extension")
    @patch("app.main.Base")
    def test_start_default_server(self, mock_base, mock_vector_setup, mock_grpc_server, mock_mcp_server):
        """Test starting the default server type (gRPC)."""
        # Call the function with default parameters
        start_server()
        
        # Verify the gRPC server was started (default)
        mock_grpc_server.assert_called_once()
        # Verify MCP server was not started
        mock_mcp_server.assert_not_called()


if __name__ == "__main__":
    unittest.main()
