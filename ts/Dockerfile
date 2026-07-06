FROM oven/bun:1.1 AS base
WORKDIR /app

# Copy package files and install dependencies
COPY ts/package.json ts/bun.lockb* ./
RUN bun install --frozen-lockfile

# Copy source code
COPY ts/ ./

# Build the CLI
RUN bun build src/cli.ts --compile --outfile memorygraph

# Runtime stage
FROM oven/bun:1.1-slim AS runtime
WORKDIR /app

COPY --from=base /app/memorygraph /usr/local/bin/memorygraph

# Create data directory
RUN mkdir -p /root/.memorygraph

ENTRYPOINT ["memorygraph"]
CMD ["--help"]
