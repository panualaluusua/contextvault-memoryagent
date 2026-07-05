import json
from pathlib import Path

import pytest

from contextvault.agent import MemoryAgent
from contextvault.providers import MockProvider, ProviderError
from contextvault.service import MemoryService


class RecordingProvider(MockProvider):
    def __init__(self) -> None:
        self.received_pack: str | None = None

    def generate(self, task: str, memory_pack: str | None):
        self.received_pack = memory_pack
        return super().generate(task, memory_pack)


class FailingProvider(MockProvider):
    name = "failing"
    model = "failure-fixture"

    def generate(self, task: str, memory_pack: str | None):
        raise ProviderError("simulated provider outage")


def test_agent_retrieves_pack_before_provider_and_changes_baseline(tmp_path: Path) -> None:
    service = MemoryService(tmp_path / "memory.db")
    service.remember_preference("agent-test", "I prefer auditable command-line tools")
    provider = RecordingProvider()
    agent = MemoryAgent(service, provider)
    with_memory = agent.answer("What are my preferences for tools?", 900)
    assert provider.received_pack and "source: session:agent-test" in provider.received_pack
    without_memory = agent.answer("What are my preferences for tools?", 900, use_memory=False)
    assert with_memory.answer != without_memory.answer
    assert "source: session:agent-test" in with_memory.answer


def test_provider_failure_does_not_mutate_memory_and_is_traced(tmp_path: Path) -> None:
    trace = tmp_path / "trace.jsonl"
    service = MemoryService(tmp_path / "memory.db", trace)
    service.remember_preference("failure-test", "I prefer stable tools")
    before = service.memory_count()
    with pytest.raises(ProviderError, match="simulated"):
        MemoryAgent(service, FailingProvider()).answer("What tools?", 600)
    assert service.memory_count() == before
    records = [json.loads(line) for line in trace.read_text(encoding="utf-8").splitlines()]
    event = records[-1]
    assert event["event"] == "agent_answer" and event["outcome"] == "error"
    assert "prompt" not in event and "I prefer stable tools" not in json.dumps(event)
