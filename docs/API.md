# ContextVault HTTP API

Run locally:

```powershell
$env:PYTHONPATH = "src"
$env:CONTEXTVAULT_API_TOKEN = "replace-with-a-local-token"
python -m contextvault --trace .tmp/api-trace.jsonl serve `
  --host 127.0.0.1 --port 8080 --database .tmp/api.duckdb
```

Docker:

```powershell
$env:CONTEXTVAULT_API_TOKEN = "replace-with-a-local-token"
docker compose up --build
```

`GET /health` is public. All POST endpoints require
`Authorization: Bearer <token>` when `CONTEXTVAULT_API_TOKEN` is configured.
The request body limit is 16 KiB.

## Endpoints

- `GET /health`: service status and memory count.
- `POST /v1/memories/preferences`: governed preference write; requires `session_id` and `text`.
- `POST /v1/memory-pack`: budgeted retrieval; requires `task`, optional `budget`.
- `POST /v1/ask`: provider-backed answer and context receipt; requires `task`, optional `budget` and `use_memory`.

Example:

```bash
curl -X POST http://127.0.0.1:8080/v1/memories/preferences \
  -H "Authorization: Bearer replace-with-a-local-token" \
  -H "Content-Type: application/json" \
  -d '{"session_id":"demo","text":"I prefer auditable APIs"}'

curl -X POST http://127.0.0.1:8080/v1/ask \
  -H "Authorization: Bearer replace-with-a-local-token" \
  -H "Content-Type: application/json" \
  -d '{"task":"What are my API preferences?","budget":900}'
```

The server is intentionally single-process. Writes are serialized among threads
inside that process, but multiple writer processes or replicas are unsupported.
Put TLS and public rate limiting at the hosting platform or reverse proxy.
