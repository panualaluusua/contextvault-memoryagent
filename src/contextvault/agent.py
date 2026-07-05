from dataclasses import dataclass
from time import perf_counter

from .providers import ModelProvider, ProviderError
from .service import MemoryService


@dataclass(frozen=True)
class AgentResult:
    answer: str
    receipt: str | None
    provider: str
    model: str


class MemoryAgent:
    def __init__(self, memory: MemoryService, provider: ModelProvider) -> None:
        self.memory = memory
        self.provider = provider

    def answer(self, task: str, budget: int = 1800, use_memory: bool = True) -> AgentResult:
        started = perf_counter()
        receipt = self.memory.get_memory_pack(task, budget) if use_memory else None
        try:
            response = self.provider.generate(task, receipt)
        except ProviderError:
            self.memory.trace.emit(
                "agent_answer", provider=self.provider.name, model=self.provider.model,
                outcome="error", latency_ms=round((perf_counter() - started) * 1000, 2),
                used_memory=use_memory,
            )
            raise
        self.memory.trace.emit(
            "agent_answer", provider=response.provider, model=response.model,
            outcome="success", latency_ms=round((perf_counter() - started) * 1000, 2),
            used_memory=use_memory,
        )
        return AgentResult(response.text, receipt, response.provider, response.model)
