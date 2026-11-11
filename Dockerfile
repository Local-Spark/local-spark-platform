FROM ghcr.io/astral-sh/uv:0.10.6 AS uv
FROM docker:28.0.4-cli AS docker-cli
FROM python:3.13.7-slim AS build
COPY --from=uv /uv /bin/uv
WORKDIR /src
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY pyproject.toml uv.lock README.md ./
ARG MOTION_SPEECH=0
RUN if [ "$MOTION_SPEECH" = "1" ]; then uv sync --frozen --no-dev --no-install-project --extra speech; \
    else uv sync --frozen --no-dev --no-install-project; fi

FROM python:3.13.7-slim AS runtime-base
WORKDIR /src
ENV PATH="/src/.venv/bin:$PATH" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
RUN useradd --uid 10001 --create-home application

FROM runtime-base AS media-worker
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
COPY --from=build /src/.venv /src/.venv
COPY app ./app
COPY catalog/kits/cafe-pausas/v1/manifest.json ./catalog/kits/cafe-pausas/v1/manifest.json
COPY catalog/kits/cafe-pausas/v1/fonts ./catalog/kits/cafe-pausas/v1/fonts
COPY alembic.ini ./
COPY migrations ./migrations
USER 10001
EXPOSE 8000
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]

FROM media-worker AS motion-worker
COPY --from=docker-cli /usr/local/bin/docker /usr/local/bin/docker

FROM runtime-base AS app
COPY --from=build /src/.venv /src/.venv
COPY app ./app
COPY catalog/kits/cafe-pausas/v1/manifest.json ./catalog/kits/cafe-pausas/v1/manifest.json
COPY alembic.ini ./
COPY migrations ./migrations
USER 10001
EXPOSE 8000
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
