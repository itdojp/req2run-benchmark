# Dockerfile for LANG-001: SQL-like Query Language Interpreter
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY config.yaml ./
COPY test_data/ ./test_data/

# Create data directories
RUN mkdir -p /var/lib/querydb /tmp/querydb-wal

# Set environment variables
ENV PYTHONPATH=/app/src
ENV QUERYDB_DATA_DIR=/var/lib/querydb
ENV QUERYDB_LOG_LEVEL=INFO

# Create non-root user for security
RUN useradd -m -u 1000 querydb && \
    chown -R querydb:querydb /app /var/lib/querydb /tmp/querydb-wal
USER querydb

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from src.main import health_check; health_check()" || exit 1

# Default command
ENTRYPOINT ["python", "-m", "src.main"]
CMD ["--help"]