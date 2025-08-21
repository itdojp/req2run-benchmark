# Universal Framework Adapter Interface (UFAI) Docker Image
# Supports multiple languages and frameworks through bench.yaml

FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

# Install system dependencies and common tools
RUN apt-get update && apt-get install -y \
    # Basic tools
    curl wget git vim nano \
    build-essential gcc g++ make cmake \
    # Python
    python3 python3-pip python3-venv \
    # Node.js
    nodejs npm \
    # Go
    golang-go \
    # Java
    openjdk-17-jdk maven gradle \
    # Ruby
    ruby-full \
    # Rust
    rustc cargo \
    # PHP
    php php-cli php-mbstring php-xml \
    # .NET
    dotnet-sdk-7.0 \
    # Database clients
    postgresql-client mysql-client redis-tools \
    # Performance testing tools
    apache2-utils wrk \
    # System monitoring
    htop iotop sysstat \
    # Network tools
    netcat telnet dnsutils \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip3 install --no-cache-dir \
    # Testing
    pytest pytest-cov pytest-asyncio \
    # Performance
    locust \
    # Security
    bandit safety \
    # Linting
    black flake8 mypy pylint \
    # Utilities
    pyyaml jsonschema click requests

# Install Node.js packages globally
RUN npm install -g \
    # Testing
    jest mocha chai \
    # Performance
    autocannon \
    # Security
    snyk \
    # Linting
    eslint prettier \
    # Build tools
    typescript webpack

# Install Go tools
RUN go install github.com/securego/gosec/v2/cmd/gosec@latest && \
    go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest

# Install Rust tools
RUN cargo install cargo-audit

# Copy bench CLI tool
COPY bench /usr/local/bin/bench
RUN chmod +x /usr/local/bin/bench

# Copy default configuration
COPY config/default.yaml /etc/bench/default.yaml

# Create output directories
RUN mkdir -p /output/reports /output/artifacts /output/logs

# Set environment variables
ENV BENCH_HOME=/etc/bench
ENV BENCH_OUTPUT=/output
ENV PATH="${PATH}:/usr/local/go/bin:/root/go/bin:/root/.cargo/bin"

# Default user (can be overridden)
USER root

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
    CMD bench version || exit 1

# Entry point
ENTRYPOINT ["/usr/local/bin/bench"]
CMD ["--help"]