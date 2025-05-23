.PHONY: help install clean lint format typecheck test test-cov generate-proto init-db load-data start start-grpc start-mcp client mcp-client docker-build docker-up docker-down docker-logs docker-shell setup

# Default target executed when no arguments are given to make.
help:
	@echo "Available commands:"
	@echo "  make install         - Install dependencies"
	@echo "  make clean           - Remove Python artifacts"
	@echo "  make lint            - Run linters (flake8)"
	@echo "  make format          - Format code (black, isort)"
	@echo "  make typecheck       - Run type checking (mypy)"
	@echo "  make test            - Run tests"
	@echo "  make test-cov        - Run tests with coverage"
	@echo "  make generate-proto  - Generate Python code from proto files"
	@echo "  make init-db         - Initialize database"
	@echo "  make load-data FILE=\"data/sample_jokes.json\" - Load data from JSON file"
	@echo "  make start           - Start the default gRPC server"
	@echo "  make start-grpc      - Start the gRPC server (explicit)"
	@echo "  make start-mcp       - Start the FastMCP server"
	@echo ""
	@echo "  make client QUERY=\"joke about science\" - Run gRPC client with a query"
	@echo "  make mcp-client QUERY=\"joke about science\" - Run MCP client with a query"
	@echo "  make docker-build    - Build Docker images"
	@echo "  make docker-up       - Start Docker containers"
	@echo "  make docker-down     - Stop Docker containers"
	@echo "  make docker-logs     - View Docker container logs"
	@echo "  make docker-shell    - Access shell in app container"
	@echo "  make setup           - Run the setup script"

# Install dependencies
install:
	poetry install

# Clean up Python artifacts
clean:
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -delete
	find . -name '*.egg-info' -delete
	find . -name '.coverage' -delete
	find . -name '.pytest_cache' -delete
	find . -name '.mypy_cache' -delete
	rm -rf htmlcov/ dist/ build/ .coverage

# Run linters
lint:
	poetry run flake8 app tests

# Format code
format:
	poetry run black app tests
	poetry run isort app tests

# Type checking
typecheck:
	poetry run mypy app tests

# Run tests
test:
	poetry run pytest

# Run tests with coverage
test-cov:
	poetry run pytest --cov=app --cov-report=html

# Generate Python code from proto files
generate-proto:
	poetry run python -m app.main generate-proto

# Initialize database
init-db:
	poetry run python -m app.main init-database

# Load data from specified JSON file
load-data:
	@if [ -z "$(FILE)" ]; then \
		echo "Please provide a file using FILE=..."; \
		exit 1; \
	fi
	poetry run python -m app.utils.data_loader "$(FILE)"

# Start the default server (gRPC)
start:
	poetry run python -m app.main start-server

# Start the gRPC server explicitly
start-grpc:
	poetry run python -m app.main start-server --type grpc

# Start the FastMCP server
start-mcp:
	poetry run python -m app.main start-server --type mcp --port 8080

# Run gRPC client with a query
client:
	@if [ -z "$(QUERY)" ]; then \
		echo "Please provide a query using QUERY=..."; \
		exit 1; \
	fi
	poetry run python -m app.utils.grpc_client get "$(QUERY)"

# Run MCP client with a query
mcp-client:
	@if [ -z "$(QUERY)" ]; then \
		echo "Please provide a query using QUERY=..."; \
		exit 1; \
	fi
	poetry run python -m app.utils.mcp_client get "$(QUERY)" --port 8080


# Docker commands
docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-shell:
	docker-compose exec app bash

# Run setup script
setup:
	./setup.sh