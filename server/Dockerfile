# --- Stage 1: Build image (for future use, e.g., dependencies with native extensions)
FROM python:3.12-slim AS builder
WORKDIR /app

# Install build dependencies for Tree-sitter and PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    make \
    pkg-config \
    git \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy project files first
COPY pyproject.toml poetry.lock ./
RUN mkdir baid_server
RUN touch baid_server/__init__.py

# Install dependencies using environment variable instead of config command
RUN pip install --upgrade pip && pip install poetry
ENV POETRY_VIRTUALENVS_CREATE=false
RUN poetry install --no-interaction --no-ansi

# --- Stage 2: Production image ---
FROM python:3.12-slim
WORKDIR /app

# Create a non-root user for security
RUN useradd -m appuser

# Install runtime dependencies for Tree-sitter and PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    libstdc++6 \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy installed dependencies from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy requirements.txt for runtime dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY baid_server ./baid_server

# Ensure scripts and migrations directories exist
RUN mkdir -p /app/scripts /app/migrations

# Create git_info directory
RUN mkdir -p /app/baid_server/git_info

# Capture git commit SHA during build and write to a file
# This is done in the build context, not in the container
ARG GIT_COMMIT_SHA
RUN if [ -z "$GIT_COMMIT_SHA" ]; then echo "unknown" > /app/baid_server/git_info/commit_sha.txt; else echo "$GIT_COMMIT_SHA" > /app/baid_server/git_info/commit_sha.txt; fi

# Copy migration files and scripts
COPY scripts/run_migrations.py /app/scripts/
COPY migrations/*.sql /app/migrations/

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PORT=8080 \
    PYTHONPATH=/app

# Make script executable
RUN chmod +x /app/scripts/run_migrations.py

# Change ownership of app files to appuser
RUN chown -R appuser:appuser /app

# Use non-root user
USER appuser

# Default command (can be overridden by docker-compose or k8s)
CMD ["sh", "-c", "python /app/scripts/run_migrations.py && uvicorn baid_server.main:app --host 0.0.0.0 --port 8080"]

# --- Development override ---
# To enable hot reload in dev, override CMD and mount source code
# Example: docker run -e ENV=dev -p 8080:8080 -v $(pwd):/app <image>