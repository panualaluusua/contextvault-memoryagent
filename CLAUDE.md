# Claude Code instructions

Follow all project rules in `AGENTS.md`; it is the shared canonical agent guide.

When the user asks about cross-project architecture, technology, security, or
engineering practices and the `agent-memory` MCP server is connected:

1. call `get_context` with the concrete task and a small initial budget;
2. use `get_memory` or `get_relations` only when the selected record needs
   inspection;
3. use `get_receipt` when exclusions or provenance affect the answer;
4. cite the returned source path;
5. prefer local `CLAUDE.md`, `AGENTS.md`, code, and tests for repository facts.

Do not use shared memory for every edit. Do not infer permission to write shared
memory: the current FastMCP server is intentionally read-only.

Useful checks:

```powershell
claude mcp list
claude mcp get agent-memory
python -m pytest tests\test_mcp_server.py -q
python -m pytest -q
```
