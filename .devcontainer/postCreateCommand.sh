#!/bin/bash

# Install dependencies
poetry install

# Initialize database and generate proto files
python -m app.main init-database
python -m app.main generate-proto

# Load sample data
python -m app.utils.data_loader data/puns.json
