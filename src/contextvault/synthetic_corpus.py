from datetime import date, datetime, timezone

from .models import Memory


CORPUS_VERSION = 1
TOPICS = (
    "incident response", "data contracts", "release automation", "API governance",
    "cost monitoring", "schema migration", "feature flags", "access control",
    "observability", "documentation quality", "batch processing", "service ownership",
)
MEMORY_TYPES = ("fact", "source_note", "project_decision", "architecture_decision", "warning")


def build_synthetic_corpus() -> list[Memory]:
    """Return 60 deterministic public evaluation distractors, not production data."""
    memories: list[Memory] = []
    for index in range(60):
        topic = TOPICS[index % len(TOPICS)]
        memory_type = MEMORY_TYPES[index % len(MEMORY_TYPES)]
        slug = f"synthetic-v{CORPUS_VERSION}-{index:02d}"
        stale = index % 11 == 0
        body = (
            f"Synthetic team {index % 7} records a {topic} note for evaluation. "
            f"It covers owner team-{index % 7}, review cycle {index % 4 + 1}, "
            f"and operational priority {index % 5 + 1}."
        )
        relations = {"related_to": [f"topic-{topic.replace(' ', '-')}"]}
        if index % 13 == 0:
            relations["contradicts"] = [f"synthetic-v{CORPUS_VERSION}-{(index + 1) % 60:02d}"]
        memories.append(Memory(
            slug=slug, memory_type=memory_type,
            title=f"{topic.title()} evaluation note {index:02d}", body=body,
            source=f"synthetic-corpus/v{CORPUS_VERSION}/{index:02d}.md",
            reliability=index % 5 + 1,
            recorded_at=datetime(2026, 1 + index % 6, 1 + index % 27, tzinfo=timezone.utc),
            valid_from=date(2026, 1, 1),
            valid_until=date(2026, 2, 1) if stale else None,
            tier=("hot", "warm", "cold")[index % 3], relations=relations,
        ))
    return memories
