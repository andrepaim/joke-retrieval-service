# Joke Retrieval Service

A Python gRPC service for retrieving jokes based on vector similarity search.

## Features

- gRPC API for joke retrieval and feedback
- Vector embedding and similarity search using sentence-transformers and PostgreSQL pgvector
- PostgreSQL database for relational data storage with vector search capabilities
- User feedback collection to improve joke recommendations
- Clarification prompts for ambiguous queries
- Sample joke data included for immediate testing

## Architecture

This service uses:

- **Python 3.9+** as the core language
- **gRPC** for API communication
- **sentence-transformers** for text embeddings
- **PostgreSQL** with **pgvector** extension for vector similarity search
- **SQLAlchemy** with pgvector for relational data and vector storage
- **Poetry** for dependency management
- **Docker** for containerization
- **Make** for task automation

## Project Structure

```
joke-retrieval-service/
├── app/                # Main application code
│   ├── api/            # gRPC server implementation
│   ├── core/           # Core functionality (config, embeddings)
│   ├── db/             # Database connection and utilities
│   ├── models/         # SQLAlchemy models
│   └── utils/          # Utility functions
├── data/               # Sample data
├── proto/              # Protocol Buffer definitions
├── tests/              # Unit and integration tests
├── .env.example        # Environment variables example (rename to .env)
├── docker-compose.yml  # Docker Compose configuration
├── Dockerfile          # Docker configuration
├── Makefile            # Task automation
├── setup.sh            # Setup script
└── pyproject.toml      # Poetry project configuration
```

## Getting Started

### Prerequisites

- Python 3.9+
- Poetry (dependency management)
- PostgreSQL with pgvector extension
- Make (optional, for running commands)

### Quick Start

The fastest way to get started is using the setup script:

```bash
# Clone the repository
git clone https://github.com/your-username/joke-retrieval-service.git
cd joke-retrieval-service

# Run the setup script (this handles all setup steps including database setup)
./setup.sh

# Start the server
make start

# In another terminal, test with a client request
make client QUERY="programming joke"
```

The setup script will:
- Install Poetry if not found
- Install dependencies
- Create .env file from .env.example
- Generate gRPC code
- Set up PostgreSQL with pgvector extension
- Initialize the database
- Load sample data from data/puns.json

### Installation Options

#### Using Make

The project includes a Makefile with all common commands:

1. Clone the repository:
   ```
   git clone https://github.com/your-username/joke-retrieval-service.git
   cd joke-retrieval-service
   ```

2. Install dependencies:
   ```
   make install
   ```

3. Set up environment variables (copy from example):
   ```
   cp .env.example .env
   ```

4. Initialize the database, generate gRPC code, and load sample data:
   ```
   make init-db
   make generate-proto
   make load-data FILE="data/puns.json"
   ```

#### Using Poetry Directly

1. Clone the repository:
   ```
   git clone https://github.com/your-username/joke-retrieval-service.git
   cd joke-retrieval-service
   ```

2. Install Poetry if you don't have it:
   ```
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. Install dependencies:
   ```
   poetry install
   ```

4. Set up environment variables (copy from example):
   ```
   cp .env.example .env
   ```

5. Set up the database:
   ```
   poetry run python -m app.main init-database
   ```

6. Generate gRPC code:
   ```
   poetry run python -m app.main generate-proto
   ```

7. Load sample data:
   ```
   poetry run python -m app.utils.data_loader data/puns.json
   ```

#### Using Docker

1. Clone the repository:
   ```
   git clone https://github.com/your-username/joke-retrieval-service.git
   cd joke-retrieval-service
   ```

2. Build and start the containers:
   ```
   make docker-up
   ```
   
   Or using Docker Compose directly:
   ```
   docker-compose up --build
   ```

This will set up PostgreSQL with the pgvector extension, initialize the database, load sample data, and start the service. Note that you'll need to ensure the PostgreSQL server is accessible with the credentials specified in your .env file or docker-compose.yml.

### Running the Service

#### With Make

```
make start        # Start the gRPC server
```

#### With Poetry

```
poetry run python -m app.main start-server
```

#### With Docker

```
make docker-up
```

## Commands Reference

### Using Make

```bash
# Development
make help             # Show help message
make install          # Install dependencies
make clean            # Remove Python artifacts
make lint             # Run linters (flake8)
make format           # Format code (black, isort)
make typecheck        # Run type checking (mypy)

# Testing
make test             # Run tests
make test-cov         # Run tests with coverage

# Application
make generate-proto   # Generate Python code from proto files
make init-db          # Initialize database
make load-data FILE="data/puns.json"  # Load sample data
make start            # Start the gRPC server
make client QUERY="..." # Run client with a query

# Docker
make docker-build     # Build Docker images
make docker-up        # Start Docker containers
make docker-down      # Stop Docker containers
make docker-logs      # View Docker container logs
make docker-shell     # Access shell in app container

# Setup
make setup            # Run the setup script
```

Note: The Makefile requires specifying the FILE parameter for the load-data command.

## Usage

### gRPC API

The service provides the following gRPC methods:

- `GetJoke(JokeRequest) -> JokeResponse`: Get a single joke based on query
- `GetJokes(JokeRequest) -> JokesResponse`: Get multiple jokes based on query
- `RecordFeedback(FeedbackRequest) -> FeedbackResponse`: Record user feedback
- `AddJoke(AddJokeRequest) -> JokeResponse`: Add a new joke to the database

See `proto/joke_service.proto` for detailed API specifications.

### Example Client

The project includes an example client for interacting with the gRPC service:

```
# Using Make
make client QUERY="programming joke"

# Or directly with Poetry
poetry run python -m app.utils.grpc_client get "programming joke"
poetry run python -m app.utils.grpc_client multi "science joke" --max 3
poetry run python -m app.utils.grpc_client feedback 123 --liked

# Make sure the server is running before using the client
```

## Development

### Testing

Run tests with:
```
make test
```

Run tests with coverage:
```
make test-cov
```

### Formatting and Linting

Format code:
```
make format
```

Lint code:
```
make lint
```

### Docker Development

For development with Docker:
```
make docker-up     # Start containers in the background
make docker-logs   # View logs
make docker-shell  # Get a shell in the app container
```

Note that the Docker setup automatically:
1. Starts a PostgreSQL container with pgvector extension
2. Initializes the database
3. Loads sample joke data
4. Starts the gRPC server

## License

MIT