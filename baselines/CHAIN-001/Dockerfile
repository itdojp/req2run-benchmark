FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libssl-dev \
    libleveldb-dev \
    libsnappy-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/
COPY test_data/ ./test_data/

# Create data directory
RUN mkdir -p /data/blockchain

# Expose ports
EXPOSE 8545 30303 8546

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8545/health').raise_for_status()"

# Run the blockchain node
CMD ["python", "-m", "src.main"]