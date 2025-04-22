# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Session Initialization
- At the beginning of each session, check for available MCP servers using `mcp__memory__read_graph` and `mcp__jokes-db__query`
- Always use available MCP tools whenever possible (like `mcp__jokes-db__query` for database access)
- Review existing memory entities to understand the project context before starting work

## MCP Memory Instructions
- After the first user query regarding the codebase, query the MCP memory server to get context about the project structure and code organization
- After making any significant changes to the project, update the memory with information about the changes
- Use the memory to guide your work and maintain continuity between sessions
- Command to update memory: `dispatch_agent "Search through project files and create a detailed overview"`

## Quick Start
- Run setup script: `make setup` or `./setup.sh`
- Start server: `make start`
- Test client: `make client QUERY="programming joke"`

## Build/Test Commands (Using Make)
- Install dependencies: `make install`
- Format code: `make format`
- Lint code: `make lint`
- Type checking: `make typecheck`
- Run all tests: `make test`
- Run tests with coverage: `make test-cov`
- Initialize database: `make init-db`
- Generate gRPC code: `make generate-proto`
- Load sample data: `make load-data`
- Start gRPC server: `make start`
- Run client: `make client QUERY="your query here"`
- Create a migration: `make migrations MESSAGE="Add new field"`
- Apply migrations: `make migrate-up`
- Roll back a migration: `make migrate-down`
- Docker build: `make docker-build`
- Start Docker containers: `make docker-up`
- Stop Docker containers: `make docker-down`
- View Docker logs: `make docker-logs`
- Access Docker shell: `make docker-shell`

## Build/Test Commands (Using Poetry)
- Install Poetry: `curl -sSL https://install.python-poetry.org | python3 -`
- Install dependencies: `poetry install`
- Activate virtual environment: `poetry shell`
- Run server: `poetry run python -m app.main start-server`
- Initialize database: `poetry run python -m app.main init-database`
- Generate gRPC code: `poetry run python -m app.main generate-proto`
- Load sample data: `poetry run python -m app.utils.data_loader data/sample_jokes.json`
- Example client: `poetry run python -m app.utils.grpc_client get "programming joke"`
- Lint: `poetry run black . && poetry run isort . && poetry run flake8 .`
- Typecheck: `poetry run mypy app tests`
- Run all tests: `poetry run pytest`
- Run single test: `poetry run pytest tests/test_embeddings.py::TestEmbeddingService::test_create_embedding`
- Add dependency: `poetry add package-name`
- Add dev dependency: `poetry add --group dev package-name`


## Docker Commands
- Build and start containers: `docker-compose up --build`
- Start in background: `docker-compose up -d`
- Stop containers: `docker-compose down`
- View logs: `docker-compose logs -f`
- Access shell in container: `docker-compose exec app bash`

## Code Style Guidelines
- Python 3.9+, use type hints for all function parameters and returns
- Async functions for all gRPC service methods
- Database access via SQLAlchemy with pgvector for embeddings and vector similarity search
- Error handling: catch exceptions in service methods with proper gRPC status codes
- Docstrings: Google style for all public functions/classes with Args/Returns
- Services should handle environment variables via settings from app.core.config
- Follow class-based design pattern for services and utilities
- New features should include corresponding unit tests
- Import order: stdlib → third-party → local modules (handled by isort)

## Testing and Development Approach
- Test-Driven Development (TDD) must be followed for all new features
- Test coverage reports generated during CI
- Always write tests first, then implement the feature
- Tests should verify behavior, not implementation details
- Focus on writing high-quality tests that provide actual value
- Avoid writing code that only aims to pass tests without proper implementation
- Maintain high test coverage (aim for >90% line coverage)
- Tests should be meaningful and verify actual business requirements

## MCP Memory Usage Guidelines
- When adding new features or updating existing ones, add information to the memory about the changes
- Structure memory entities by components (API Layer, Core Components, etc.)
- Maintain relationships between components to reflect architectural dependencies
- Example memory queries:
  - `mcp__memory__search_nodes` to find relevant information about specific components
  - `mcp__memory__open_nodes` to retrieve detailed information about known entities
  - `mcp__memory__read_graph` to understand the overall project structure
- After making code changes, update the relevant entities with new observations
