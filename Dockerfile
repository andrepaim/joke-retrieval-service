FROM python:3.9-slim

WORKDIR /app

# Install Poetry
RUN pip install poetry==1.4.2

# Copy poetry configuration files
COPY pyproject.toml poetry.lock* ./

# Configure poetry to not use a virtual environment in the container
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-dev

# Copy the content of the project
COPY . .

# Generate gRPC code if needed
RUN python -m app.main generate-proto

# Expose port for gRPC server
EXPOSE 50051

# Only using gRPC server

# Run the application
CMD ["python", "-m", "app.main", "start-server"]