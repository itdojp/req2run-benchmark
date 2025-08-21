# WEB-011: Secure File Upload with Presigned URLs
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    clamav \
    clamav-daemon \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Update ClamAV database
RUN freshclam

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ src/
COPY config/ config/

# Create data directory
RUN mkdir -p /app/data

# Set environment variables
ENV PYTHONPATH=/app/src
ENV DATABASE_URL=sqlite:///./data/uploads.db

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Start ClamAV daemon and FastAPI app
CMD clamd & python src/main.py