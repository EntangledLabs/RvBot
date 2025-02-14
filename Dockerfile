FROM python:3.13

WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:0.5.31 /uv /uvx /bin/

COPY requirements.txt /app/requirements.txt
RUN uv pip install --system -r /app/requirements.txt

COPY main.py /app/main.py
COPY .env /app/.env
COPY config.toml /app/config.toml

CMD ["python", "main.py"]