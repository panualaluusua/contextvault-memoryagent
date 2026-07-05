# ContextVault baseline evaluation

Fixture version: 1
Golden cases: 3/3 passed
All expected memory-pack checks passed: True
Synthetic distractor corpus: v1 / 60 memories
Citation-contract coverage with memory: 100%
Citation-contract coverage without memory: 0%
Mean recall@3: 1.000
MRR: 0.833
Mean retrieval latency: 11.518 ms

| Case | Pack/budget | Checks | Recall@3 | RR | Citation with memory | Citation baseline | Latency ms |
|---|---:|---:|---:|---:|---|---|---:|
| preference-recall | 652/800 | 2/2 | 1.000 | 1.000 | True | False | 13.148 |
| stale-correction | 1379/1400 | 3/3 | 1.000 | 0.500 | True | False | 11.548 |
| strict-budget | 633/700 | 2/2 | 1.000 | 1.000 | True | False | 9.857 |

The deterministic mock isolates memory-system behavior from model variability.
Citation-contract coverage only checks whether the deterministic stub carries a selected `source:` reference.
It is not model accuracy, answer quality, semantic relevance, or production performance.
