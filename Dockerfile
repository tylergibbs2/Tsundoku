FROM oven/bun:1 AS frontend-builder
WORKDIR /app
COPY . .

RUN bun install
RUN bun run build
RUN ls -la tsundoku/blueprints/ux/static/js/

FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
LABEL maintainer="Tyler Gibbs <gibbstyler7@gmail.com>"

RUN apt -y update && apt -y upgrade
RUN apt install -y ffmpeg git sqlite3

ENV IS_DOCKER=1

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

COPY . /app

# Copy built frontend files from the bun stage
COPY --from=frontend-builder /app/tsundoku/blueprints/ux/static/js ./tsundoku/blueprints/ux/static/js

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

EXPOSE 6439
CMD [ "uv", "run", "python", "-m", "tsundoku" ]
