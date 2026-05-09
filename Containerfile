FROM python:3.13-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.5.4 /uv /uvx /bin/

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY src/ ./src/
COPY web/ ./web/
COPY seeds/ ./seeds/
RUN uv sync --frozen --no-dev

ENV DATABASE_PATH=/var/lib/clean-rock/data/scores.db \
    SITE_DIR=/app/site \
    WEB_DIR=/app/web \
    SEEDS_DIR=/app/seeds

EXPOSE 8000

CMD ["uvicorn", "clean_rock.main:app", "--host", "0.0.0.0", "--port", "8000"]
