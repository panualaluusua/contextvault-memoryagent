import hmac
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

from .agent import MemoryAgent
from .providers import MockProvider, OllamaProvider, ProviderError, QwenCompatibleProvider
from .service import MemoryService


MAX_REQUEST_BYTES = 16_384


class ContextVaultHTTPServer(HTTPServer):
    def __init__(self, address, database: Path, trace_path: Path | None, token: str | None, provider_name: str):
        super().__init__(address, ContextVaultHandler)
        self.database = database
        self.trace_path = trace_path
        self.api_token = token
        self.provider_name = provider_name


class ContextVaultHandler(BaseHTTPRequestHandler):
    server: ContextVaultHTTPServer

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _send(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        self.wfile.flush()

    def _discard_request_body(self) -> None:
        """Consume a small rejected POST body so Windows closes the socket cleanly."""
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return
        if 0 < length <= MAX_REQUEST_BYTES:
            self.rfile.read(length)

    def _authorized(self) -> bool:
        if not self.server.api_token:
            return True
        expected = f"Bearer {self.server.api_token}"
        return hmac.compare_digest(self.headers.get("Authorization", ""), expected)

    def _json_body(self) -> dict[str, Any]:
        content_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip()
        if content_type != "application/json":
            raise ValueError("Content-Type must be application/json")
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise ValueError("Invalid Content-Length") from exc
        if length <= 0 or length > MAX_REQUEST_BYTES:
            raise ValueError(f"Request body must be 1..{MAX_REQUEST_BYTES} bytes")
        try:
            value = json.loads(self.rfile.read(length))
        except json.JSONDecodeError as exc:
            raise ValueError("Request body must be valid JSON") from exc
        if not isinstance(value, dict):
            raise ValueError("JSON body must be an object")
        return value

    def do_GET(self) -> None:
        if self.path != "/health":
            self._send(404, {"error": "not_found"})
            return
        service = MemoryService(self.server.database, self.server.trace_path)
        try:
            self._send(200, {"status": "ok", "memory_count": service.memory_count()})
        finally:
            service.connection.close()

    def do_POST(self) -> None:
        if not self._authorized():
            self._discard_request_body()
            self._send(401, {"error": "unauthorized"})
            return
        try:
            body = self._json_body()
            self._dispatch(body)
        except ValueError as exc:
            self._send(400, {"error": "invalid_request", "message": str(exc)})
        except ProviderError as exc:
            self._send(502, {"error": "provider_error", "message": str(exc)})

    def _dispatch(self, body: dict[str, Any]) -> None:
        service = MemoryService(self.server.database, self.server.trace_path)
        try:
            if self.path == "/v1/memories/preferences":
                text, session_id = body.get("text"), body.get("session_id")
                if not isinstance(text, str) or not isinstance(session_id, str):
                    raise ValueError("text and session_id must be strings")
                decision, slug = service.remember_preference(session_id, text)
                status = 201 if slug else 422
                self._send(status, {"outcome": decision.outcome, "reason": decision.reason, "slug": slug})
                return
            task = body.get("task")
            budget = body.get("budget", 1800)
            if not isinstance(task, str) or not task.strip():
                raise ValueError("task must be a non-empty string")
            if not isinstance(budget, int) or not 300 <= budget <= 10_000:
                raise ValueError("budget must be an integer between 300 and 10000")
            if self.path == "/v1/memory-pack":
                pack = service.get_memory_pack(task, budget)
                self._send(200, {"memory_pack": pack, "characters": len(pack), "budget": budget})
                return
            if self.path == "/v1/ask":
                providers = {"mock": MockProvider, "ollama": OllamaProvider, "qwen": QwenCompatibleProvider}
                provider = providers[self.server.provider_name]()
                result = MemoryAgent(service, provider).answer(task, budget, bool(body.get("use_memory", True)))
                self._send(200, {
                    "answer": result.answer, "context_receipt": result.receipt,
                    "provider": result.provider, "model": result.model,
                })
                return
            self._send(404, {"error": "not_found"})
        finally:
            service.connection.close()


def create_server(
    host: str, port: int, database: Path, trace_path: Path | None = None,
    token: str | None = None, provider_name: str = "mock",
) -> ContextVaultHTTPServer:
    if provider_name not in {"mock", "ollama", "qwen"}:
        raise ValueError("provider_name must be mock, ollama or qwen")
    return ContextVaultHTTPServer((host, port), database, trace_path, token, provider_name)
