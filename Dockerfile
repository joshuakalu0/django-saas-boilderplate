FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:${PATH}"

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl libpq-dev netcat-openbsd \
    && pip install --no-cache-dir uv \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
RUN uv sync --no-dev

COPY . .

RUN chmod +x docker/app/entrypoint.sh

ENTRYPOINT ["./docker/app/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "-c", "gunicorn.conf.py"]

