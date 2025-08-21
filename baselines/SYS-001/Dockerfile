# SYS-001: Distributed Lock Coordinator Service
FROM golang:1.21-alpine AS builder

# Install build dependencies
RUN apk add --no-cache gcc musl-dev git make

# Set working directory
WORKDIR /build

# Copy go mod files
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY . .

# Build the application
RUN make build

# Runtime stage
FROM alpine:3.19

# Install runtime dependencies
RUN apk add --no-cache ca-certificates

# Create non-root user
RUN adduser -D -u 1000 lockservice

# Set working directory
WORKDIR /app

# Copy binary from builder
COPY --from=builder /build/bin/distributed-lock /app/
COPY --from=builder /build/config /app/config

# Set ownership
RUN chown -R lockservice:lockservice /app

# Switch to non-root user
USER lockservice

# Expose ports
EXPOSE 8080 9090

# Health check
HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

# Run the service
ENTRYPOINT ["/app/distributed-lock"]
CMD ["--config", "/app/config/cluster.yaml"]