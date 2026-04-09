FROM python:3.13-slim-bookworm AS builder
WORKDIR /build
COPY pyproject.toml .
RUN pip install --no-cache-dir --prefix=/install .

FROM python:3.13-slim-bookworm AS builder-dev
WORKDIR /build
COPY pyproject.toml .
RUN pip install --no-cache-dir --prefix=/install ".[dev]"

FROM python:3.13-slim-bookworm AS runtime
RUN apt-get update \
    && apt-get install --no-install-recommends -y libssl3 openssl \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /build
COPY pyproject.toml .
RUN pip install --no-cache-dir .
RUN adduser --disabled-password --no-create-home appuser
COPY app/ /app/app/
COPY alembic/ /app/alembic/
COPY alembic.ini /app/
WORKDIR /app
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM python:3.13-slim-bookworm AS test
WORKDIR /app
COPY pyproject.toml /app/
RUN pip install --no-cache-dir ".[dev]"
COPY app/ /app/app/
COPY alembic/ /app/alembic/
COPY alembic.ini /app/
COPY tests/ /app/tests/
CMD ["pytest", "tests/", "-v", "--tb=short", "--ignore=tests/integration"]

# Keep runtime as default final image for plain `docker build`.
FROM runtime AS final
