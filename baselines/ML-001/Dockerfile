# Dockerfile for ML-001: ML Pipeline with Model Serving
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for ML libraries
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    gfortran \
    libopenblas-dev \
    liblapack-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and configuration
COPY src/ ./src/
COPY config/ ./config/
COPY models/ ./models/
COPY test_data/ ./test_data/

# Create directories for ML artifacts
RUN mkdir -p /app/artifacts /app/logs /app/data

# Set environment variables
ENV PYTHONPATH=/app/src
ENV MLFLOW_TRACKING_URI=file:///app/artifacts/mlflow
ENV MODEL_REGISTRY_PATH=/app/models/model_registry.json

# Create non-root user for security
RUN useradd -m -u 1000 mluser && \
    chown -R mluser:mluser /app
USER mluser

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Default command
ENTRYPOINT ["python", "-m", "src.main"]
CMD ["--host", "0.0.0.0", "--port", "8000"]