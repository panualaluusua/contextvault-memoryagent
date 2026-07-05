from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Exclusion:
    slug: str
    kind: str
    reason: str
    winner_slug: str | None = None


def _winner(left: dict, right: dict) -> tuple[dict, dict]:
    left_rank = (left["reliability"], datetime.fromisoformat(left["recorded_at"]))
    right_rank = (right["reliability"], datetime.fromisoformat(right["recorded_at"]))
    if left_rank != right_rank:
        return (left, right) if left_rank > right_rank else (right, left)
    return (left, right) if left["slug"] < right["slug"] else (right, left)


def resolve_truthiness(candidates: list[dict], edges: list[dict]) -> tuple[list[dict], list[Exclusion]]:
    by_slug = {item["slug"]: item for item in candidates}
    excluded: dict[str, Exclusion] = {}
    for item in candidates:
        if item["stale"]:
            excluded[item["slug"]] = Exclusion(
                item["slug"], "stale", f"valid_until {item['valid_until']} has passed"
            )
    for edge in sorted(edges, key=lambda item: (item["relation_type"], item["source_slug"], item["target_slug"])):
        source = by_slug.get(edge["source_slug"])
        target = by_slug.get(edge["target_slug"])
        if not source or not target or source["slug"] in excluded:
            continue
        if edge["relation_type"] == "supersedes" and target["slug"] not in excluded:
            excluded[target["slug"]] = Exclusion(
                target["slug"], "superseded", f"superseded by {source['slug']}", source["slug"]
            )
        elif edge["relation_type"] == "contradicts" and target["slug"] not in excluded:
            winner, loser = _winner(source, target)
            excluded[loser["slug"]] = Exclusion(
                loser["slug"], "contradicted",
                f"contradicted by higher-ranked {winner['slug']}", winner["slug"],
            )
    selected = [item for item in candidates if item["slug"] not in excluded]
    return selected, [excluded[slug] for slug in sorted(excluded)]
