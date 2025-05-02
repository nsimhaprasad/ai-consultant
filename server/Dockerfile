# --- Stage 1: Build image (for future use, e.g., dependencies with native extensions)
FROM python:3.12-slim AS builder
WORKDIR /app

# Copy project files first
COPY pyproject.toml poetry.lock ./
RUN mkdir baid_server
RUN touch baid_server/__init__.py

# Install dependencies
RUN pip install --upgrade pip && pip install poetry
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi

# --- Stage 2: Production image ---
FROM python:3.12-slim
WORKDIR /app

# Create a non-root user for security
RUN useradd -m appuser

# Copy installed dependencies from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy requirements.txt for runtime dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY baid_server ./baid_server

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PORT=8080

# Use non-root user
USER appuser

# Default command (can be overridden by docker-compose or k8s)
CMD ["uvicorn", "baid_server.main:app", "--host", "0.0.0.0", "--port", "8080"]

# --- Development override ---
# To enable hot reload in dev, override CMD and mount source code
# Example: docker run -e ENV=dev -p 8080:8080 -v $(pwd):/app <image>
