# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 mcp && \
    chown -R mcp:mcp /app

# Copy wheels from builder
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .

# Install dependencies
RUN pip install --no-cache /wheels/*

# Copy application code
COPY migrations_mcp ./migrations_mcp
COPY docker/entrypoint.sh .

# Set permissions
RUN chmod +x entrypoint.sh && \
    chown -R mcp:mcp /app

USER mcp

# Environment variables
ENV PYTHONPATH=/app
ENV DJANGO_SETTINGS_MODULE=""
ENV MCP_SERVICE_PORT=8000

# Expose port
EXPOSE 8000

# Run the service
ENTRYPOINT ["./entrypoint.sh"] 