FROM golang:1.21-alpine AS builder

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache git make gcc musl-dev

# Copy go mod files
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY cmd/ ./cmd/
COPY pkg/ ./pkg/
COPY internal/ ./internal/

# Build the controller
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o orch-controller cmd/controller/main.go

# Runtime stage
FROM alpine:3.19

RUN apk --no-cache add ca-certificates

WORKDIR /app

# Copy binary from builder
COPY --from=builder /app/orch-controller /usr/local/bin/orch-controller

# Copy configuration
COPY config/ ./config/
COPY examples/ ./examples/

# Create necessary directories
RUN mkdir -p /var/lib/orch /etc/orch/tls

# Expose ports
EXPOSE 6443 8080 9090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/healthz || exit 1

# Run the controller
ENTRYPOINT ["orch-controller"]
CMD ["--config=/app/config/controller.yaml"]