import json
from pathlib import Path
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from contextvault.api import create_server


@pytest.fixture
def api_server(tmp_path: Path):
    trace = tmp_path / "api.jsonl"
    server = create_server("127.0.0.1", 0, tmp_path / "api.duckdb", trace, token="test-token")
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", trace
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def request(base: str, method: str, path: str, body=None, token: str | None = "test-token"):
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"} if body is not None else {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(base + path, data=data, headers=headers, method=method)
    with urlopen(req, timeout=5) as response:
        return response.status, json.loads(response.read())


def test_http_e2e_persists_preference_and_answers_with_receipt(api_server) -> None:
    base, trace = api_server
    status, health = request(base, "GET", "/health")
    assert status == 200 and health["status"] == "ok"
    status, write = request(base, "POST", "/v1/memories/preferences", {
        "session_id": "http-e2e", "text": "I prefer portable auditable APIs",
    })
    assert status == 201 and write["outcome"] == "allow"
    status, answer = request(base, "POST", "/v1/ask", {
        "task": "What are my API preferences?", "budget": 900,
    })
    assert status == 200
    assert "I prefer portable auditable APIs" in answer["answer"]
    assert "source: session:http-e2e" in answer["context_receipt"]
    events = [json.loads(line)["event"] for line in trace.read_text(encoding="utf-8").splitlines()]
    assert events[-2:] == ["memory_pack", "agent_answer"]


def test_http_auth_validation_and_governance(api_server) -> None:
    base, _ = api_server
    for _ in range(10):
        with pytest.raises(HTTPError) as unauthorized:
            request(base, "POST", "/v1/memory-pack", {"task": "test"}, token=None)
        assert unauthorized.value.code == 401
    with pytest.raises(HTTPError) as invalid:
        request(base, "POST", "/v1/memory-pack", {"task": "test", "budget": 2})
    assert invalid.value.code == 400
    with pytest.raises(HTTPError) as blocked:
        request(base, "POST", "/v1/memories/preferences", {
            "session_id": "unsafe", "text": "api_key=sk-abcdefghijklmnop",
        })
    assert blocked.value.code == 422
