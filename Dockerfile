# syntax=docker/dockerfile:1.7
FROM ghcr.io/astral-sh/uv:python3.13-alpine AS base
WORKDIR /app
COPY pyproject.toml uv.lock /app/
RUN uv sync --frozen --no-dev
COPY . /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["uv", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]
