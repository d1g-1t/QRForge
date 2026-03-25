FROM python:3.12-slim AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY alembic/ alembic/
COPY alembic.ini .
COPY src/ src/

ENV PYTHONPATH=/app/src
EXPOSE 8000

CMD ["uvicorn", "qrcode_service.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ── test stage ────────────────────────────────────────────
FROM base AS test

RUN pip install --no-cache-dir ".[dev]"
COPY tests/ tests/

CMD ["pytest", "--tb=short", "-q"]

