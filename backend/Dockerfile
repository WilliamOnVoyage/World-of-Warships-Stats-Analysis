FROM python:3.10-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1

# Install system dependencies for psycopg2
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# Install Python dependencies directly (avoid hatchling wheel build issues)
COPY pyproject.toml ./
RUN pip install --no-cache-dir \
    "fastapi>=0.100.0" \
    "uvicorn>=0.22.0" \
    "sqlmodel>=0.0.8" \
    "psycopg2-binary>=2.9.6" \
    "httpx>=0.24.1" \
    "pydantic>=2.0" \
    "aiolimiter>=1.1.0" \
    "python-dotenv>=1.0.0"

COPY . .

# Run the FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
