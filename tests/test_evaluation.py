from pathlib import Path

from contextvault.evaluation import render_markdown, run_evaluation


def test_baseline_evaluation_proves_memory_grounding(tmp_path: Path) -> None:
    report = run_evaluation(
        tmp_path / "evaluation.duckdb", Path("data/demo-vault"),
        Path("data/evaluation/golden_cases.json"),
    )
    assert report["all_expected_passed"]
    assert report["passed_case_count"] == report["case_count"] == 3
    assert report["synthetic_memory_count"] == 60
    assert report["citation_contract_with_memory"] == 1.0
    assert report["citation_contract_without_memory"] == 0.0
    assert report["mean_recall_at_3"] == 1.0
    assert report["mrr"] > 0
    assert all(row["pack_characters"] <= row["budget"] for row in report["results"])
    markdown = render_markdown(report)
    assert "Golden cases: 3/3 passed" in markdown
    assert "Citation-contract coverage with memory: 100%" in markdown
    assert "Citation-contract coverage without memory: 0%" in markdown
    assert "It is not model accuracy" in markdown
