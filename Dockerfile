FROM python:3.12-slim

LABEL org.opencontainers.image.title="notification-service" \
      org.opencontainers.image.description="Microblogging notification consumer and sender"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

RUN poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock ./

# Production dependencies only (exclude dev: pytest, black, ruff, mypy)
RUN poetry install --no-interaction --no-ansi --no-root --only main

COPY . .

# Run as non-root user
RUN adduser --disabled-password --gecos "" appuser \
    && chown -R appuser:appuser /app
USER appuser

CMD ["python", "-m", "src.main"]
