FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Pre-populate and bake the demo database directly into the Docker image
ENV DATABASE_URL=sqlite:///./oepms_fallback.db
RUN python app/seed.py

ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "python app/seed.py && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
