# --- Stage 1: Build image (for future use, e.g., dependencies with native extensions)
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt ./
RUN pip install --user --upgrade pip && \
    pip install --user -r requirements.txt

# --- Stage 2: Production image ---
FROM python:3.11-slim
WORKDIR /app

# Create a non-root user for security
RUN useradd -m appuser

# Copy installed dependencies from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy app code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PORT=8080

# Use non-root user
USER appuser

# Default command (can be overridden by docker-compose or k8s)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

# --- Development override ---
# To enable hot reload in dev, override CMD and mount source code
# Example: docker run -e ENV=dev -p 8080:8080 -v $(pwd):/app <image>
