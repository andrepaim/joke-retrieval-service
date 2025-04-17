# Development Container for Joke Retrieval Service

This folder contains configuration for using GitHub Codespaces or VS Code with Remote Containers.

## Features

- Python 3.9 development environment
- PostgreSQL with pgvector extension
- Pre-configured VS Code with Python extensions
- Automatic initialization of database and sample data
- Integrated testing and linting tools

## Getting Started

### GitHub Codespaces

1. Click on the "Code" button in the GitHub repository
2. Select "Create codespace on master"
3. Wait for the container to build and initialize

### VS Code Remote Containers

1. Install the [Remote Development extension pack](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.vscode-remote-extensionpack)
2. Clone the repository locally
3. Open the repository in VS Code
4. When prompted, click "Reopen in Container"
   - Or use Command Palette (F1) and select "Remote-Containers: Reopen in Container"

## Workflow

Once the container is running:

- The database is automatically initialized
- Sample joke data is loaded
- All development tools are available
- Server can be started with: `python -m app.main start-server`
- Tests can be run with: `poetry run pytest`

## Using the Makefile

The project includes a Makefile with common commands:

```
make start        # Start the gRPC server
make client QUERY="your query"  # Test with a client query
make test         # Run all tests
make format       # Format code with black and isort
make lint         # Lint code with flake8
```