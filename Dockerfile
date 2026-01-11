FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
COPY src/ src/
RUN pip install --no-cache-dir .

# Copy the database (you'll need to build this locally first)
COPY data/marvel.db data/marvel.db

# Expose port
EXPOSE 8080

# Run the API
CMD ["python", "-m", "uvicorn", "marvel_metadata.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8080"]
