import json
import os
from dataclasses import dataclass
from typing import Callable, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class ProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class ProviderResponse:
    text: str
    provider: str
    model: str


class ModelProvider(Protocol):
    name: str
    model: str

    def generate(self, task: str, memory_pack: str | None) -> ProviderResponse: ...


class MockProvider:
    name = "mock"
    model = "deterministic-memory-mock-v1"

    def generate(self, task: str, memory_pack: str | None) -> ProviderResponse:
        if not memory_pack or "source:" not in memory_pack:
            text = "Baseline: no persistent memory was available, so no source-grounded recommendation can be made."
        else:
            memory_lines = [line for line in memory_pack.splitlines() if line.startswith("- [")]
            source_lines = [line for line in memory_lines if "source:" in line]
            first = source_lines[0] if source_lines else "the retrieved memory pack"
            text = f"Memory-grounded recommendation: follow {first}"
        return ProviderResponse(text=text, provider=self.name, model=self.model)


Transport = Callable[[Request, float], bytes]


def _default_transport(request: Request, timeout: float) -> bytes:
    with urlopen(request, timeout=timeout) as response:
        return response.read()


class QwenCompatibleProvider:
    name = "qwen-cloud"

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = 30.0,
        transport: Transport = _default_transport,
    ) -> None:
        self.api_key = api_key or os.getenv("QWEN_API_KEY")
        self.base_url = (base_url or os.getenv("QWEN_BASE_URL") or "").rstrip("/")
        self.model = model or os.getenv("QWEN_MODEL") or ""
        self.timeout = timeout
        self.transport = transport

    def validate(self) -> None:
        missing = [
            name for name, value in (
                ("QWEN_API_KEY", self.api_key),
                ("QWEN_BASE_URL", self.base_url),
                ("QWEN_MODEL", self.model),
            ) if not value
        ]
        if missing:
            raise ProviderError(f"Missing Qwen configuration: {', '.join(missing)}")

    def generate(self, task: str, memory_pack: str | None) -> ProviderResponse:
        self.validate()
        context = memory_pack or "No persistent memory was selected."
        payload = json.dumps({
            "model": self.model,
            "messages": [
                {"role": "system", "content": "Use only supported memory. Cite its source paths and state uncertainty."},
                {"role": "user", "content": f"Task:\n{task}\n\nMemory pack:\n{context}"},
            ],
        }).encode("utf-8")
        request = Request(
            f"{self.base_url}/chat/completions",
            data=payload,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            raw = self.transport(request, self.timeout)
            data = json.loads(raw.decode("utf-8"))
            text = data["choices"][0]["message"]["content"]
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, KeyError, IndexError) as exc:
            raise ProviderError(f"Qwen provider request failed: {type(exc).__name__}") from exc
        if not isinstance(text, str) or not text.strip():
            raise ProviderError("Qwen provider returned an empty response")
        return ProviderResponse(text=text.strip(), provider=self.name, model=self.model)


class OllamaProvider:
    """Optional real local provider using Ollama's native chat endpoint."""

    name = "ollama"

    def __init__(
        self, base_url: str | None = None, model: str | None = None,
        timeout: float = 60.0, transport: Transport = _default_transport,
    ) -> None:
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL") or "http://127.0.0.1:11434").rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL") or ""
        self.timeout = timeout
        self.transport = transport

    def validate(self) -> None:
        if not self.model:
            raise ProviderError("Missing Ollama configuration: OLLAMA_MODEL")

    def generate(self, task: str, memory_pack: str | None) -> ProviderResponse:
        self.validate()
        context = memory_pack or "No persistent memory was selected."
        payload = json.dumps({
            "model": self.model, "stream": False,
            "messages": [
                {"role": "system", "content": "Use only supported memory. Cite source paths and state uncertainty."},
                {"role": "user", "content": f"Task:\n{task}\n\nMemory pack:\n{context}"},
            ],
        }).encode("utf-8")
        request = Request(
            f"{self.base_url}/api/chat", data=payload,
            headers={"Content-Type": "application/json"}, method="POST",
        )
        try:
            raw = self.transport(request, self.timeout)
            text = json.loads(raw.decode("utf-8"))["message"]["content"]
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, KeyError) as exc:
            raise ProviderError(f"Ollama provider request failed: {type(exc).__name__}") from exc
        if not isinstance(text, str) or not text.strip():
            raise ProviderError("Ollama provider returned an empty response")
        return ProviderResponse(text=text.strip(), provider=self.name, model=self.model)
