#!/bin/bash

# Setup script for Joke Retrieval Service
set -e

# Print with colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up Joke Retrieval Service...${NC}"

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo -e "${YELLOW}Poetry not found. Installing...${NC}"
    curl -sSL https://install.python-poetry.org | python3 -
    echo -e "${GREEN}Poetry installed!${NC}"
fi

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
poetry install
echo -e "${GREEN}Dependencies installed!${NC}"

# Create environment file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file from template...${NC}"
    cp .env.example .env
    echo -e "${GREEN}.env file created!${NC}"
fi

# Generate gRPC code
echo -e "${YELLOW}Generating gRPC code...${NC}"
poetry run python -m app.main generate-proto
echo -e "${GREEN}gRPC code generated!${NC}"

# Check PostgreSQL extensions
echo -e "${YELLOW}Checking for PostgreSQL with pgvector extension...${NC}"
if ! command -v psql &> /dev/null; then
    echo -e "${YELLOW}PostgreSQL client not found. Please install PostgreSQL.${NC}"
    exit 1
fi

# Source .env file if it exists for DB connection info
if [ -f .env ]; then
    source .env
else
    source .env.example
fi

# Try to check if pgvector extension exists and create it if not found
if ! PGPASSWORD="${POSTGRES_PASSWORD:-postgres}" psql -h "${POSTGRES_SERVER:-localhost}" -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-joke_service}" -c "SELECT * FROM pg_extension WHERE extname = 'vector'" -t | grep -q vector; then
    echo -e "${YELLOW}pgvector extension not found in database. Installing it now...${NC}"
    PGPASSWORD="${POSTGRES_PASSWORD:-postgres}" psql -h "${POSTGRES_SERVER:-localhost}" -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-joke_service}" -c "CREATE EXTENSION IF NOT EXISTS vector;"
    echo -e "${GREEN}pgvector extension installed!${NC}"
else
    echo -e "${GREEN}pgvector extension found!${NC}"
fi

# Initialize database
echo -e "${YELLOW}Initializing database...${NC}"
# Drop any existing tables to ensure clean schema
PGPASSWORD="${POSTGRES_PASSWORD:-postgres}" psql -h "${POSTGRES_SERVER:-localhost}" -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-joke_service}" -c "DROP TABLE IF EXISTS jokes, joke_tags, tags, joke_feedback, query_logs CASCADE;"
# Create new tables
poetry run python -m app.main init-database
echo -e "${GREEN}Database initialized!${NC}"

# Load sample data
echo -e "${YELLOW}Loading sample data...${NC}"
poetry run python -m app.utils.data_loader data/puns.json
echo -e "${GREEN}Sample data loaded!${NC}"

echo -e "${GREEN}Setup complete! You can now run the service with:${NC}"
echo -e "${YELLOW}poetry run python -m app.main start-server${NC}"
echo -e "${GREEN}or${NC}"
echo -e "${YELLOW}make start${NC}"