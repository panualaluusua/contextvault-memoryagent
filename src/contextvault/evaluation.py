import json
from dataclasses import dataclass, asdict
from pathlib import Path
from statistics import mean
from time import perf_counter

from .agent import MemoryAgent
from .providers import MockProvider
from .service import MemoryService
from .synthetic_corpus import CORPUS_VERSION, build_synthetic_corpus


@dataclass(frozen=True)
class EvaluationResult:
    case_id: str
    budget: int
    pack_characters: int
    expected_checks: int
    expected_passed: int
    citation_contract_with_memory: bool
    citation_contract_without_memory: bool
    recall_at_3: float
    reciprocal_rank: float
    retrieval_latency_ms: float


def run_evaluation(database: Path, vault: Path, fixture_path: Path) -> dict:
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    service = MemoryService(database)
    service.ingest(vault)
    synthetic = build_synthetic_corpus()
    for memory in synthetic:
        service.upsert(memory)
    agent = MemoryAgent(service, MockProvider())
    results: list[EvaluationResult] = []
    for case in fixture["cases"]:
        started = perf_counter()
        candidates = service.search(case["task"], limit=3)
        retrieval_latency_ms = (perf_counter() - started) * 1000
        retrieved = [candidate["slug"] for candidate in candidates]
        expected = case["expected_slugs"]
        recall_at_3 = len(set(retrieved) & set(expected)) / len(expected)
        ranks = [retrieved.index(slug) + 1 for slug in expected if slug in retrieved]
        reciprocal_rank = 1 / min(ranks) if ranks else 0.0
        with_memory = agent.answer(case["task"], case["budget"], use_memory=True)
        baseline = agent.answer(case["task"], case["budget"], use_memory=False)
        receipt = with_memory.receipt or ""
        checks = case["must_contain"]
        results.append(EvaluationResult(
            case_id=case["id"], budget=case["budget"], pack_characters=len(receipt),
            expected_checks=len(checks), expected_passed=sum(value in receipt for value in checks),
            citation_contract_with_memory="source:" in with_memory.answer,
            citation_contract_without_memory="source:" in baseline.answer,
            recall_at_3=recall_at_3, reciprocal_rank=reciprocal_rank,
            retrieval_latency_ms=round(retrieval_latency_ms, 3),
        ))
    return {
        "fixture_version": fixture["version"],
        "case_count": len(results),
        "all_expected_passed": all(r.expected_passed == r.expected_checks for r in results),
        "synthetic_corpus_version": CORPUS_VERSION,
        "synthetic_memory_count": len(synthetic),
        "citation_contract_with_memory": mean(r.citation_contract_with_memory for r in results),
        "citation_contract_without_memory": mean(r.citation_contract_without_memory for r in results),
        "mean_recall_at_3": mean(r.recall_at_3 for r in results),
        "mrr": mean(r.reciprocal_rank for r in results),
        "mean_retrieval_latency_ms": mean(r.retrieval_latency_ms for r in results),
        "max_retrieval_latency_ms": max(r.retrieval_latency_ms for r in results),
        "results": [asdict(result) for result in results],
    }


def render_markdown(report: dict) -> str:
    lines = [
        "# ContextVault baseline evaluation", "",
        f"Fixture version: {report['fixture_version']}",
        f"Cases: {report['case_count']}",
        f"All expected memory-pack checks passed: {report['all_expected_passed']}",
        f"Synthetic distractor corpus: v{report['synthetic_corpus_version']} / {report['synthetic_memory_count']} memories",
        f"Citation-contract coverage with memory: {report['citation_contract_with_memory']:.0%}",
        f"Citation-contract coverage without memory: {report['citation_contract_without_memory']:.0%}",
        f"Mean recall@3: {report['mean_recall_at_3']:.3f}",
        f"MRR: {report['mrr']:.3f}",
        f"Mean retrieval latency: {report['mean_retrieval_latency_ms']:.3f} ms",
        "", "| Case | Pack/budget | Checks | Recall@3 | RR | Citation with memory | Citation baseline | Latency ms |",
        "|---|---:|---:|---:|---:|---|---|---:|",
    ]
    for result in report["results"]:
        lines.append(
            f"| {result['case_id']} | {result['pack_characters']}/{result['budget']} | "
            f"{result['expected_passed']}/{result['expected_checks']} | {result['recall_at_3']:.3f} | "
            f"{result['reciprocal_rank']:.3f} | {result['citation_contract_with_memory']} | "
            f"{result['citation_contract_without_memory']} | {result['retrieval_latency_ms']:.3f} |"
        )
    lines.extend([
        "", "The deterministic mock isolates memory-system behavior from model variability.",
        "Citation-contract coverage only checks whether the deterministic stub carries a selected `source:` reference.",
        "It is not model accuracy, answer quality, semantic relevance, or production performance.",
    ])
    return "\n".join(lines) + "\n"
