# =========================================================================
# MetroGuard AI — Production Cloud Dockerfile
# =========================================================================
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=10000

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source, models, pre-compiled frontend, and scenario caches
COPY backend/ ./backend/
COPY frontend/dist/ ./frontend/dist/
COPY models/ ./models/
COPY data/processed/ ./data/processed/
COPY docs/ ./docs/

# Expose cloud port
EXPOSE 10000

# Start production server
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
