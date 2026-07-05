from dataclasses import dataclass, field
from datetime import date, datetime


MEMORY_TYPES = {
    "fact", "preference", "project_decision", "architecture_decision",
    "source_note", "warning",
}
RELATION_TYPES = {
    "supports", "constrains", "contradicts", "supersedes",
    "derived_from", "related_to",
}


@dataclass(frozen=True)
class Memory:
    slug: str
    memory_type: str
    title: str
    body: str
    source: str
    reliability: int
    recorded_at: datetime
    valid_from: date | None = None
    valid_until: date | None = None
    tier: str = "warm"
    relations: dict[str, list[str]] = field(default_factory=dict)

    @property
    def stale(self) -> bool:
        return self.valid_until is not None and self.valid_until < date.today()
