FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libpq-dev \
    ffmpeg libsm6 libxext6 \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

COPY ./backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY ./prisma ./prisma

# ── Dev Stage ─────────────────────────────────────────────────
FROM base AS dev
COPY ./backend .
EXPOSE 8000
CMD ["sh", "-c", "prisma generate --generator pyclient && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"]

# ── Production Stage ───────────────────────────────────────────
FROM base AS production
COPY ./backend .
EXPOSE 8000
CMD ["sh", "-c", "prisma generate --generator pyclient && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]