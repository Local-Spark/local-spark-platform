FROM ghcr.io/astral-sh/uv:0.10.6 AS uv
FROM python:3.13.7-slim AS build
COPY --from=uv /uv /bin/uv
WORKDIR /src
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

FROM python:3.13.7-slim
WORKDIR /src
ENV PATH="/src/.venv/bin:$PATH" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
RUN useradd --uid 10001 --create-home application
COPY --from=build /src/.venv /src/.venv
COPY app ./app
COPY alembic.ini ./
COPY migrations ./migrations
USER 10001
EXPOSE 8000
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
