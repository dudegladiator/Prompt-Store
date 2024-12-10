FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8989 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir uvicorn[standard]

# Copy application code
COPY . .

# Expose port
EXPOSE $PORT

# Run uvicorn with production settings
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8989", "--proxy-headers", "--forwarded-allow-ips", "*", "--log-level", "info"]