# Travel Optimization Engine - Docker Environment
# Provides a containerized Python environment for running the API client scripts.

FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set Python to run unbuffered (better for Docker logs)
ENV PYTHONUNBUFFERED=1

# Default env vars (override at runtime)
ENV KIWI_API_KEY=""
ENV AMADEUS_API_KEY=""
ENV AMADEUS_API_SECRET=""
ENV AMADEUS_ENV="test"

# Health check: verify Python and requests are available
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import requests; print('OK')" || exit 1

# Default command: show help
CMD ["python", "scripts/kiwi_tequila.py", "--help"]
