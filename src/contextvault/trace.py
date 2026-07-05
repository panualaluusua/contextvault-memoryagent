import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class JsonlTrace:
    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else None

    def emit(self, event: str, **fields: Any) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            **fields,
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def load_trace(path: str | Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def render_receipt(records: list[dict[str, Any]]) -> str:
    lines = ["# Context Receipt"]
    for record in records:
        event = record.get("event")
        if event == "memory_write":
            lines.append(f"- write: {record.get('outcome')} {record.get('slug', '(not persisted)')}")
        elif event == "conflict_resolution":
            winner = f"; winner={record['winner_slug']}" if record.get("winner_slug") else ""
            lines.append(f"- excluded: {record.get('excluded_slug')} ({record.get('kind')}{winner})")
        elif event == "memory_pack":
            selected = ", ".join(record.get("selected_slugs", [])) or "none"
            excluded = ", ".join(record.get("excluded_slugs", [])) or "none"
            lines.append(
                f"- pack: selected={selected}; excluded={excluded}; "
                f"characters={record.get('characters')}/{record.get('budget')}"
            )
        elif event == "agent_answer":
            lines.append(
                f"- answer: {record.get('outcome')} via {record.get('provider')}/{record.get('model')} "
                f"in {record.get('latency_ms')} ms"
            )
    return "\n".join(lines)
