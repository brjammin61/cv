# Multi-stage Dockerfile for ORE Arbitrage Bot
# This creates an optimized production image

# Stage 1: Build
FROM rust:1.75-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    pkg-config \
    libssl-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy workspace manifest
COPY Cargo.toml ./

# Copy all source code
COPY ore-bot ./ore-bot
COPY modules ./modules

# Build the application in release mode
RUN cargo build --release --bin ore-bot

# Stage 2: Runtime
FROM debian:bookworm-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    ca-certificates \
    libssl3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user for security
RUN useradd -m -u 1000 orebot

# Create app directory
WORKDIR /app

# Copy binary from builder
COPY --from=builder /app/target/release/ore-bot /app/ore-bot

# Copy example env file
COPY .env.example /app/.env.example

# Create directory for wallet
RUN mkdir -p /app/wallets && chown -R orebot:orebot /app

# Switch to non-root user
USER orebot

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD pgrep -f ore-bot || exit 1

# Set environment variables
ENV RUST_LOG=info
ENV RUST_BACKTRACE=1

# Run the bot
CMD ["/app/ore-bot"]
