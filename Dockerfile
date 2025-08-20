# Req2Run Benchmark Evaluation Runner
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    git \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and documentation
COPY requirements.txt .
COPY README.md .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the benchmark framework
COPY req2run/ ./req2run/
COPY tests/ ./tests/
COPY setup.py .

# Install the package
RUN pip install -e .

# Copy problem definitions and baselines
COPY problems/ ./problems/
COPY baselines/ ./baselines/

# Set environment variables
ENV PYTHONPATH=/app:$PYTHONPATH
ENV REQ2RUN_HOME=/app

# Default command
CMD ["python", "-m", "req2run.cli", "--help"]