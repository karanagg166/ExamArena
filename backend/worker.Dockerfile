FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

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
RUN pip install --no-cache-dir setuptools wheel \
    && pip install --no-cache-dir --no-build-isolation --retries 10 --timeout 100 --prefer-binary -r requirements.txt

COPY ./backend .

CMD ["python", "-m", "arq", "app.imports.worker.WorkerSettings"]
