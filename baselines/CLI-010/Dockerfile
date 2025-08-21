FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/
COPY test_data/ ./test_data/
COPY tests/ ./tests/

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Set environment for terminal capabilities
ENV TERM=xterm-256color
ENV COLORTERM=truecolor

# Run the application
ENTRYPOINT ["python", "-m", "src.main"]