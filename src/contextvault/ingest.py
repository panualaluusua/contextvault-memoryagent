from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml

from .models import MEMORY_TYPES, RELATION_TYPES, Memory


class MemoryValidationError(ValueError):
    pass


def _parse_date(value: Any, field: str) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise MemoryValidationError(f"{field} must be an ISO date") from exc


def _parse_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if value in (None, ""):
        raise MemoryValidationError("recorded_at is required")
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise MemoryValidationError("recorded_at must be an ISO datetime") from exc


def parse_memory(path: Path, source_root: Path | None = None) -> Memory:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        raise MemoryValidationError(f"{path}: YAML frontmatter is required")
    raw_header, body = text[4:].split("\n---\n", 1)
    data = yaml.safe_load(raw_header) or {}
    required = ("type", "slug", "title", "reliability", "recorded_at")
    missing = [key for key in required if data.get(key) in (None, "")]
    if missing:
        raise MemoryValidationError(f"{path}: missing fields: {', '.join(missing)}")
    memory_type = str(data["type"])
    if memory_type not in MEMORY_TYPES:
        raise MemoryValidationError(f"{path}: unsupported type {memory_type!r}")
    reliability = int(data["reliability"])
    if not 1 <= reliability <= 5:
        raise MemoryValidationError(f"{path}: reliability must be 1..5")
    tier = str(data.get("tier", "warm"))
    if tier not in {"hot", "warm", "cold"}:
        raise MemoryValidationError(f"{path}: tier must be hot, warm or cold")
    raw_relations = data.get("relations") or {}
    if not isinstance(raw_relations, dict):
        raise MemoryValidationError(f"{path}: relations must be a mapping")
    unknown = set(raw_relations) - RELATION_TYPES
    if unknown:
        raise MemoryValidationError(f"{path}: unknown relations: {', '.join(sorted(unknown))}")
    relations = {kind: [str(v) for v in values or []] for kind, values in raw_relations.items()}
    source = path.relative_to(source_root).as_posix() if source_root else path.as_posix()
    return Memory(
        slug=str(data["slug"]), memory_type=memory_type, title=str(data["title"]),
        body=body.strip(), source=source, reliability=reliability,
        recorded_at=_parse_datetime(data["recorded_at"]),
        valid_from=_parse_date(data.get("valid_from"), "valid_from"),
        valid_until=_parse_date(data.get("valid_until"), "valid_until"),
        tier=tier, relations=relations,
    )


def load_vault(root: Path) -> list[Memory]:
    memories = [parse_memory(path, root) for path in sorted(root.rglob("*.md"))]
    slugs = [memory.slug for memory in memories]
    duplicates = sorted({slug for slug in slugs if slugs.count(slug) > 1})
    if duplicates:
        raise MemoryValidationError(f"duplicate slugs: {', '.join(duplicates)}")
    return memories
