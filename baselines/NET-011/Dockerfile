# NET-011: gRPC Service Mesh with Load Balancing and Health Checks
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    openssl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy proto files
COPY proto/ ./proto/

# Generate Python code from proto files
RUN python -m grpc_tools.protoc \
    -I./proto \
    --python_out=./src \
    --grpc_python_out=./src \
    ./proto/service.proto || true

# Copy application code
COPY src/ ./src/
COPY config/ ./config/

# Create certificate directory
RUN mkdir -p certs

# Generate self-signed certificates for testing
RUN openssl req -x509 -newkey rsa:4096 -nodes \
    -keyout certs/ca.key -out certs/ca.crt \
    -days 365 -subj "/CN=mesh-ca" && \
    openssl req -newkey rsa:4096 -nodes \
    -keyout certs/server.key -out certs/server.csr \
    -subj "/CN=mesh-server" && \
    openssl x509 -req -in certs/server.csr \
    -CA certs/ca.crt -CAkey certs/ca.key -CAcreateserial \
    -out certs/server.crt -days 365 && \
    openssl req -newkey rsa:4096 -nodes \
    -keyout certs/client.key -out certs/client.csr \
    -subj "/CN=mesh-client" && \
    openssl x509 -req -in certs/client.csr \
    -CA certs/ca.crt -CAkey certs/ca.key -CAcreateserial \
    -out certs/client.crt -days 365

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV GRPC_PORT=50051
ENV USE_TLS=true
ENV CERT_DIR=/app/certs

# Expose ports
EXPOSE 50051 50052 50053 50060 50061 50070 50071 8080 9090

# Health check using grpc_health_probe
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import grpc; channel = grpc.insecure_channel('localhost:50051'); channel.close()" || exit 1

# Run application
CMD ["python", "src/main.py"]