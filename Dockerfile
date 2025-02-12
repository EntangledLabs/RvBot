FROM python:3.13-bookworm
COPY --from=ghcr.io/astral-sh/uv:0.5.31 /uv /uvx /bin/

COPY . /app
WORKDIR /app
RUN uv sync --frozen