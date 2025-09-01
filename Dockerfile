# syntax=docker/dockerfile:1.7
FROM ghcr.io/astral-sh/uv:python3.13-alpine AS base
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# Install build dependencies for psycopg if needed (binary wheel usually fine)
RUN apk add --no-cache bash curl

COPY pyproject.toml uv.lock /app/
RUN uv sync --frozen --no-dev

COPY . /app

# Collect static in a later stage after dependencies + source are present.
RUN uv run python manage.py collectstatic --noinput || true

EXPOSE 8000

# Entrypoint handles migrations then launches gunicorn (Render uses PORT env)
ENV PORT=8000
CMD ["bash", "-c", "uv run python wait_for_db.py && uv run python manage.py migrate --noinput && exec uv run gunicorn criminal.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --threads 2 --timeout 60"]
