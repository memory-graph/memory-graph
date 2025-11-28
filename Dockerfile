# Dockerfile for MemoryGraph MCP Server
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml ./
COPY src/ ./src/

# Install package
RUN pip install --no-cache-dir -e .

# Create data directory for SQLite
RUN mkdir -p /data

# Set default environment variables
ENV MEMORY_BACKEND=sqlite \
    MEMORY_SQLITE_PATH=/data/memory.db \
    MEMORY_TOOL_PROFILE=lite \
    MEMORY_LOG_LEVEL=INFO

# Expose port (not used for MCP stdio, but useful for future web UI)
EXPOSE 8000

# Run the memory server
# Note: MCP uses stdio transport, so stdin_open and tty are required in docker-compose
CMD ["python", "-m", "memorygraph.server"]
