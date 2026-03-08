FROM python:3.13-slim AS builder
WORKDIR /build
COPY pyproject.toml .
RUN pip install --no-cache-dir --prefix=/install .

FROM python:3.13-slim AS builder-dev
WORKDIR /build
COPY pyproject.toml .
RUN pip install --no-cache-dir --prefix=/install ".[dev]"

FROM python:3.13-slim AS runtime
RUN adduser --disabled-password --no-create-home appuser
COPY --from=builder /install /usr/local
COPY app/ /app/app/
COPY alembic/ /app/alembic/
COPY alembic.ini /app/
WORKDIR /app
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM python:3.13-slim AS test
COPY --from=builder-dev /install /usr/local
COPY app/ /app/app/
COPY alembic/ /app/alembic/
COPY alembic.ini /app/
COPY tests/ /app/tests/
COPY pyproject.toml /app/
WORKDIR /app
CMD ["pytest", "tests/", "-v", "--tb=short", "--ignore=tests/integration"]
