import argparse
import json
from pathlib import Path
import sys

from .service import MemoryService
from .trace import load_trace


def run_operation(operation: str, payload: dict, database: Path, trace: Path) -> dict:
    service = MemoryService(database, trace, read_only=True)
    try:
        if operation == "get_context":
            budget = int(payload["budget"])
            memory_pack = service.get_memory_pack(str(payload["task"]), budget)
            records = load_trace(trace)
            event = next(
                record for record in reversed(records) if record.get("event") == "memory_pack"
            )
            return {
                "memory_pack": memory_pack,
                "selected": list(event.get("selected_slugs", [])),
                "excluded": list(event.get("excluded_slugs", [])),
                "characters": int(event.get("characters", len(memory_pack))),
                "budget": budget,
            }
        if operation == "get_memory":
            slug = str(payload["slug"])
            memory = service.get_memory(slug)
            if memory is None:
                return {
                    "found": False, "slug": slug, "memory_type": "", "title": "", "body": "",
                    "source": "", "recorded_at": "", "valid_from": "", "valid_until": "", "tier": "",
                }
            return {
                "found": True,
                "slug": str(memory["slug"]),
                "memory_type": str(memory["memory_type"]),
                "title": str(memory["title"]),
                "body": str(memory["body"]),
                "source": str(memory["source"]),
                "recorded_at": str(memory["recorded_at"] or ""),
                "valid_from": str(memory["valid_from"] or ""),
                "valid_until": str(memory["valid_until"] or ""),
                "tier": str(memory["tier"]),
            }
        if operation == "get_relations":
            slug = str(payload["slug"])
            return {
                "slug": slug,
                "relations": [
                    {key: str(value) for key, value in relation.items()}
                    for relation in service.expand_relations(slug)
                ],
            }
        raise ValueError(f"unsupported backend operation: {operation}")
    finally:
        service.connection.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="contextvault-mcp-backend")
    parser.add_argument("operation", choices=("get_context", "get_memory", "get_relations"))
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--trace", type=Path, required=True)
    args = parser.parse_args(argv)
    payload = json.load(sys.stdin)
    result = run_operation(args.operation, payload, args.database, args.trace)
    json.dump(result, sys.stdout, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
