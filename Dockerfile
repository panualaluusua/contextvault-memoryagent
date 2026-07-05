FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CONTEXTVAULT_DATABASE=/data/memory.duckdb \
    CONTEXTVAULT_TRACE=/data/trace.jsonl

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir . && useradd --create-home --uid 10001 contextvault \
    && mkdir -p /data && chown contextvault:contextvault /data

USER contextvault
VOLUME ["/data"]
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=2)" || exit 1

CMD ["contextvault", "--trace", "/data/trace.jsonl", "serve", "--host", "0.0.0.0", "--port", "8080", "--database", "/data/memory.duckdb"]
