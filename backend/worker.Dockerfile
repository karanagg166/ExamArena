FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:0.13.7@sha256:96f40d3904aad8d0bd010539001d36c8e2188b981e1334471a90c4a1d93bb490 /uv /uvx /usr/local/bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_NO_CACHE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_HTTP_TIMEOUT=100 \
    UV_HTTP_RETRIES=10

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libpq-dev \
    ffmpeg libsm6 libxext6 \
    tesseract-ocr \
    tesseract-ocr-eng \
    libtesseract-dev \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

COPY ./backend/requirements.txt ./requirements.txt
RUN uv pip install --system --no-cache setuptools wheel \
    && uv pip install --system --no-cache --no-build-isolation -r requirements.txt

COPY ./backend .

CMD ["python", "-m", "arq", "app.imports.worker.WorkerSettings"]
