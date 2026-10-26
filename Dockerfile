# Open Agent Hackathon 2026 — MarginWhy Docker Container
# Optimized for reproducible, zero-friction execution on standard CPU hardware
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Prevent Python from writing .pyc files and enable unbuffered streaming logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    SAMPLE_MODE=true \
    PYTHONPATH=/app

# Install system utilities if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency definition and install
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy complete project code
COPY . .

# Ensure trace log directory exists with proper write permissions
RUN mkdir -p /app/logs

# Expose standard dashboard and REST API port
EXPOSE 8000

# Health check against live health endpoint
HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default execution: Launch executive dashboard and FastAPI REST API on all interfaces
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
