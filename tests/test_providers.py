import json
from urllib.request import Request

import pytest

from contextvault.providers import MockProvider, OllamaProvider, ProviderError, QwenCompatibleProvider


def test_providers_share_generate_contract() -> None:
    response = MockProvider().generate("task", None)
    assert response.provider == "mock"
    assert response.model

    def transport(request: Request, timeout: float) -> bytes:
        assert request.full_url == "https://qwen.example/v1/chat/completions"
        assert request.headers["Authorization"] == "Bearer test-key"
        body = json.loads(request.data.decode("utf-8"))
        assert body["model"] == "qwen-test"
        return b'{"choices":[{"message":{"content":"grounded answer"}}]}'

    qwen = QwenCompatibleProvider("test-key", "https://qwen.example/v1", "qwen-test", transport=transport)
    qwen_response = qwen.generate("task", "memory")
    assert qwen_response.text == "grounded answer"
    assert qwen_response.provider == "qwen-cloud"


def test_qwen_missing_configuration_fails_before_transport() -> None:
    called = False

    def transport(request: Request, timeout: float) -> bytes:
        nonlocal called
        called = True
        return b"{}"

    provider = QwenCompatibleProvider(api_key="", base_url="", model="", transport=transport)
    with pytest.raises(ProviderError) as error:
        provider.generate("task", "memory")
    assert "QWEN_API_KEY" in str(error.value)
    assert "QWEN_BASE_URL" in str(error.value)
    assert "QWEN_MODEL" in str(error.value)
    assert not called


def test_ollama_provider_uses_real_local_api_contract_with_fake_transport() -> None:
    def transport(request: Request, timeout: float) -> bytes:
        assert request.full_url == "http://127.0.0.1:11434/api/chat"
        body = json.loads(request.data.decode("utf-8"))
        assert body["model"] == "local-test-model"
        assert body["stream"] is False
        assert "source: memory.md" in body["messages"][1]["content"]
        return b'{"message":{"content":"Answer grounded in source: memory.md"}}'

    provider = OllamaProvider(model="local-test-model", transport=transport)
    response = provider.generate("task", "source: memory.md")
    assert response.provider == "ollama"
    assert response.text == "Answer grounded in source: memory.md"


def test_ollama_requires_model_before_network_access() -> None:
    called = False

    def transport(request: Request, timeout: float) -> bytes:
        nonlocal called
        called = True
        return b"{}"

    provider = OllamaProvider(model="", transport=transport)
    with pytest.raises(ProviderError, match="OLLAMA_MODEL"):
        provider.generate("task", None)
    assert not called
