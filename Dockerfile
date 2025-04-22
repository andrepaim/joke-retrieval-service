FROM python:3.10.12-slim

WORKDIR /app

# Install Poetry
RUN pip install poetry==1.4.2

# Copy poetry configuration files
COPY pyproject.toml poetry.lock* ./

# Configure poetry to not use a virtual environment in the container
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --without dev

# Copy the content of the project
COPY . .

# Verify app directory exists
RUN ls -la

# Generate gRPC code if needed
RUN python -m app.main generate-proto

# Expose port for gRPC server
EXPOSE 50051

# Only using gRPC server

# Run the application
CMD ["python", "-m", "app.main", "start-server"]