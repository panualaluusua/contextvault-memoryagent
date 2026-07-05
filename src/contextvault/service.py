from datetime import date, datetime, timezone
import hashlib
from pathlib import Path
import re
from threading import Lock, RLock

import duckdb

from .ingest import load_vault
from .governance import WriteDecision, evaluate_write
from .models import Memory
from .trace import JsonlTrace
from .truthiness import resolve_truthiness


_LOCKS_GUARD = Lock()
_WRITE_LOCKS: dict[str, RLock] = {}


def _database_lock(database: str) -> RLock:
    key = database if database == ":memory:" else str(Path(database).resolve())
    with _LOCKS_GUARD:
        return _WRITE_LOCKS.setdefault(key, RLock())


def _compact_text(text: str, maximum: int) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= maximum:
        return normalized
    cutoff = normalized.rfind(" ", 0, max(1, maximum - 3))
    if cutoff < maximum // 2:
        cutoff = maximum - 3
    return normalized[:cutoff].rstrip() + "..."


class MemoryService:
    def __init__(
        self,
        database: str | Path = ":memory:",
        trace_path: str | Path | None = None,
        read_only: bool = False,
    ) -> None:
        self.database = str(database)
        self.read_only = read_only
        self._write_lock = _database_lock(self.database)
        with self._write_lock:
            self.connection = duckdb.connect(self.database, read_only=read_only)
        self.trace = JsonlTrace(trace_path)
        if not read_only:
            with self._write_lock:
                self._create_schema()

    def _create_schema(self) -> None:
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS memories (
              slug TEXT PRIMARY KEY, memory_type TEXT, title TEXT,
              body TEXT, source TEXT, reliability INTEGER,
              recorded_at TEXT, valid_from TEXT, valid_until TEXT, tier TEXT
            );
            CREATE TABLE IF NOT EXISTS relations (
              source_slug TEXT, relation_type TEXT, target_slug TEXT,
              UNIQUE(source_slug, relation_type, target_slug)
            );
        """)

    def _fetch_dicts(self, query: str, parameters: list | None = None) -> list[dict]:
        cursor = self.connection.execute(query, parameters or [])
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def upsert(self, memory: Memory) -> None:
        with self._write_lock:
            self.connection.execute("BEGIN TRANSACTION")
            try:
                self.connection.execute("DELETE FROM relations WHERE source_slug = ?", [memory.slug])
                self.connection.execute("DELETE FROM memories WHERE slug = ?", [memory.slug])
                self.connection.execute(
                    "INSERT INTO memories VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    [memory.slug, memory.memory_type, memory.title, memory.body, memory.source,
                     memory.reliability, memory.recorded_at.isoformat(),
                     memory.valid_from.isoformat() if memory.valid_from else None,
                     memory.valid_until.isoformat() if memory.valid_until else None, memory.tier],
                )
                for relation_type, targets in memory.relations.items():
                    for target in targets:
                        self.connection.execute(
                            "INSERT INTO relations VALUES (?, ?, ?)",
                            [memory.slug, relation_type, target],
                        )
                self.connection.commit()
            except Exception:
                self.connection.rollback()
                raise

    def ingest(self, vault: Path) -> int:
        memories = load_vault(vault)
        for memory in memories:
            self.upsert(memory)
        return len(memories)

    def memory_count(self) -> int:
        row = self.connection.execute("SELECT COUNT(*) FROM memories").fetchone()
        if row is None:
            raise RuntimeError("memory count query returned no row")
        return int(row[0])

    def get_memory(self, slug: str) -> dict | None:
        rows = self._fetch_dicts(
            """
            SELECT slug, memory_type, title, body, source, reliability,
                   recorded_at, valid_from, valid_until, tier
            FROM memories WHERE slug = ?
            """,
            [slug],
        )
        return rows[0] if rows else None

    def remember_preference(self, session_id: str, text: str) -> tuple[WriteDecision, str | None]:
        decision = evaluate_write(text)
        if decision.outcome not in {"allow", "redact"}:
            self.trace.emit("memory_write", outcome=decision.outcome, reason=decision.reason, session_id=session_id)
            return decision, None
        digest = hashlib.sha256(f"{session_id}\0{decision.text}".encode("utf-8")).hexdigest()[:12]
        slug = f"preference-{digest}"
        memory = Memory(
            slug=slug,
            memory_type="preference",
            title="Remembered user preference",
            body=decision.text,
            source=f"session:{session_id}",
            reliability=4,
            recorded_at=datetime.now(timezone.utc),
            valid_from=date.today(),
            tier="hot",
            relations={"derived_from": [f"session-{session_id}"]},
        )
        self.upsert(memory)
        self.trace.emit("memory_write", outcome=decision.outcome, slug=slug, memory_type="preference", session_id=session_id)
        return decision, slug

    def expand_relations(self, slug: str) -> list[dict]:
        return self._fetch_dicts(
            """
            SELECT source_slug, relation_type, target_slug, 'outgoing' AS direction
            FROM relations WHERE source_slug = ?
            UNION ALL
            SELECT source_slug, relation_type, target_slug, 'incoming' AS direction
            FROM relations WHERE target_slug = ?
            ORDER BY direction, relation_type, source_slug, target_slug
            """,
            [slug, slug],
        )

    def _relations_for(self, slugs: list[str]) -> list[dict]:
        if not slugs:
            return []
        placeholders = ",".join("?" for _ in slugs)
        return self._fetch_dicts(
            f"SELECT source_slug, relation_type, target_slug FROM relations "
            f"WHERE source_slug IN ({placeholders}) OR target_slug IN ({placeholders})",
            slugs + slugs,
        )

    def search(self, query: str, limit: int = 8) -> list[dict]:
        terms = [term.lower() for term in re.findall(r"[\w-]+", query, flags=re.UNICODE) if len(term) > 2]
        if not terms or limit <= 0:
            return []
        hit_expression = " + ".join("CASE WHEN haystack LIKE ? THEN 1 ELSE 0 END" for _ in terms)
        preference_bonus = 20 if any(term in {"preference", "preferences", "prefer"} for term in terms) else 0
        query_sql = f"""
            WITH corpus AS (
              SELECT *, lower(title || ' ' || body || ' ' || memory_type) AS haystack
              FROM memories
            ), scored AS (
              SELECT *, ({hit_expression}) AS lexical_hits
              FROM corpus
            )
            SELECT slug, memory_type, title, body, source, reliability,
                   recorded_at, valid_from, valid_until, tier,
                   lexical_hits + reliability / 10.0
                     + CASE WHEN memory_type = 'preference' THEN {preference_bonus} ELSE 0 END AS score,
                   valid_until IS NOT NULL AND valid_until < ? AS stale
            FROM scored
            WHERE lexical_hits > 0
               OR (memory_type = 'preference' AND {preference_bonus} > 0)
            ORDER BY score DESC, reliability DESC, slug ASC
            LIMIT ?
        """
        return self._fetch_dicts(
            query_sql, [f"%{term}%" for term in terms] + [date.today().isoformat(), limit]
        )

    def get_memory_pack(self, task: str, budget: int = 2000) -> str:
        if budget < 300:
            raise ValueError("budget must be at least 300 characters")
        candidates = self.search(task)
        active, exclusions = resolve_truthiness(
            candidates, self._relations_for([item["slug"] for item in candidates])
        )
        task_display = _compact_text(task, min(240, max(60, budget // 4)))
        lines = ["# Memory Pack", "", "## Task", task_display, "", "## Relevant Memories"]
        selected: list[dict] = []
        if not active:
            lines.append("- No supporting memory found.")
        for item in active:
            if len(selected) >= 2:
                break
            compact_body = _compact_text(item["body"], 260)
            entry = f"- [{item['memory_type']}] {item['title']} -- {compact_body} (source: {item['source']})"
            proposed = "\n".join(lines + [entry])
            if len(proposed) + 160 <= budget:
                lines.append(entry)
                selected.append(item)
        relation_lines: list[str] = []
        seen_relations: set[tuple[str, str, str]] = set()
        relation_priority = {"supersedes": 0, "contradicts": 1, "constrains": 2, "supports": 3}
        for item in selected:
            edges = sorted(
                self.expand_relations(item["slug"]),
                key=lambda edge: (
                    relation_priority.get(edge["relation_type"], 9),
                    edge["source_slug"], edge["target_slug"],
                ),
            )
            for edge in edges:
                key = (edge["source_slug"], edge["relation_type"], edge["target_slug"])
                if key not in seen_relations:
                    seen_relations.add(key)
                    relation_lines.append(
                        f"- {edge['source_slug']} -[{edge['relation_type']}]-> {edge['target_slug']}"
                    )
        lines.extend(["", "## Warnings"])
        if exclusions:
            warning_added = False
            candidates_by_slug = {item["slug"]: item for item in candidates}
            for exclusion in exclusions:
                item = candidates_by_slug[exclusion.slug]
                label = {
                    "stale": "stale memory",
                    "superseded": "superseded memory",
                    "contradicted": "contradicted memory",
                }[exclusion.kind]
                warning = (
                    f"- Excluded {label}: {item['title']} -- {exclusion.reason} "
                    f"(source: {item['source']})"
                )
                if len("\n".join(lines + [warning])) <= budget:
                    lines.append(warning)
                    warning_added = True
            if not warning_added:
                fallback = "- Stale memories were excluded; details omitted by context budget."
                if len("\n".join(lines + [fallback])) <= budget:
                    lines.append(fallback)
        else:
            if len("\n".join(lines + ["- None."])) <= budget:
                lines.append("- None.")
        if relation_lines:
            heading_added = False
            for relation_line in relation_lines:
                prefix = ["", "## Related Memory Edges"] if not heading_added else []
                if len("\n".join(lines + prefix + [relation_line])) <= budget:
                    lines.extend(prefix + [relation_line])
                    heading_added = True
                elif not heading_added:
                    break
        result = "\n".join(lines)
        if len(result) > budget:
            raise AssertionError("memory pack builder exceeded its structural budget")
        for exclusion in exclusions:
            self.trace.emit(
                "conflict_resolution", excluded_slug=exclusion.slug,
                kind=exclusion.kind, winner_slug=exclusion.winner_slug,
            )
        self.trace.emit(
            "memory_pack",
            task_sha256=hashlib.sha256(task.encode("utf-8")).hexdigest(),
            selected_slugs=[item["slug"] for item in selected if item["title"] in result],
            excluded_slugs=[item.slug for item in exclusions],
            characters=len(result),
            budget=budget,
        )
        return result
