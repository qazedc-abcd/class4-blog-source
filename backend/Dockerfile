FROM python:3.12-slim

# git is required for GitHub two-way sync
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY app /app/app

# content (git repo) and site output are volumes; data.db lives under /app/data
RUN mkdir -p /app/data
VOLUME ["/app/content", "/app/data/site"]

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    CONTENT_DIR=/app/content \
    DATA_DIR=/app/data \
    SITE_DIR=/app/data/site

EXPOSE 8000

# uvicorn: 1 worker keeps memory low on 2H2G; bump workers via env if needed
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${UVICORN_WORKERS:-1}"]
