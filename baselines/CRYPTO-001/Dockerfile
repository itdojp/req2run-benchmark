FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY tests/ ./tests/

# Create non-root user
RUN useradd -m -u 1000 cryptouser && \
    chown -R cryptouser:cryptouser /app

USER cryptouser

# Set Python path
ENV PYTHONPATH=/app

# Entry point
ENTRYPOIN ["python", "-m", "src.main"]
CMD ["--help"]