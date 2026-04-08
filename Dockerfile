# Customer Support Inbox Automation - OpenEnv Environment
# Hugging Face Spaces compatible Dockerfile

FROM python:3.11-slim

# HF Spaces runs as non-root user 1000
RUN useradd -m -u 1000 user
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first (layer caching)
COPY server/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy all application code
COPY . /app/

# Set Python path so imports resolve correctly
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# HF Spaces uses port 7860
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# Switch to non-root user
USER user

# Start the FastAPI server
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
