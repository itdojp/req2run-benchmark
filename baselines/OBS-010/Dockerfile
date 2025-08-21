# OBS-010: OpenTelemetry Comprehensive Tracing Coverage
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ src/
COPY config/ config/

# Set Python path
ENV PYTHONPATH=/app/src

# Environment variables for OpenTelemetry
ENV OTEL_SERVICE_NAME=obs-010-service
ENV OTEL_SERVICE_VERSION=1.0.0
ENV OTEL_RESOURCE_ATTRIBUTES=service.name=obs-010-service,service.version=1.0.0

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Default command
ENTRYPOINT ["python", "src/main.py"]
CMD ["serve", "--config", "config/tracing.yaml"]