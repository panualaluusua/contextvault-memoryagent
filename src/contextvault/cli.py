import argparse
import os
import sys
from pathlib import Path

from .agent import MemoryAgent
from .providers import MockProvider, OllamaProvider, ProviderError, QwenCompatibleProvider
from .service import MemoryService
from .trace import load_trace, render_receipt
from .api import create_server
from .evaluation import render_markdown, run_evaluation
from .demo import run_portfolio_demo


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="contextvault")
    parser.add_argument("--trace", type=Path, help="append safe JSONL trace events")
    sub = parser.add_subparsers(dest="command", required=True)
    ingest = sub.add_parser("ingest", help="validate and index a Markdown vault")
    ingest.add_argument("vault", type=Path)
    ingest.add_argument("--database", type=Path, default=Path("memory.duckdb"))
    remember = sub.add_parser("remember", help="store a governed preference")
    remember.add_argument("text")
    remember.add_argument("--session", required=True)
    remember.add_argument("--database", type=Path, default=Path("memory.duckdb"))
    recall = sub.add_parser("recall", help="retrieve a budgeted memory pack")
    recall.add_argument("task")
    recall.add_argument("--database", type=Path, default=Path("memory.duckdb"))
    recall.add_argument("--budget", type=int, default=1800)
    relations = sub.add_parser("relations", help="show one-hop typed relations")
    relations.add_argument("slug")
    relations.add_argument("--database", type=Path, default=Path("memory.duckdb"))
    ask = sub.add_parser("ask", help="answer through a memory-enabled model provider")
    ask.add_argument("task")
    ask.add_argument("--database", type=Path, default=Path("memory.duckdb"))
    ask.add_argument("--budget", type=int, default=1800)
    ask.add_argument("--provider", choices=("mock", "ollama", "qwen"), default="mock")
    ask.add_argument("--without-memory", action="store_true")
    receipt = sub.add_parser("receipt", help="render a human-readable JSONL context receipt")
    receipt.add_argument("trace_file", type=Path)
    serve = sub.add_parser("serve", help="run the portable ContextVault HTTP API")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8080)
    serve.add_argument("--database", type=Path, default=Path("memory.duckdb"))
    serve.add_argument("--provider", choices=("mock", "ollama", "qwen"), default="mock")
    demo = sub.add_parser("demo", help="run the deterministic memory demo")
    demo.add_argument("--vault", type=Path, default=Path("data/demo-vault"))
    demo.add_argument("--database", type=Path, default=Path(".tmp/portfolio-demo.duckdb"))
    demo.add_argument("--trace-output", type=Path, default=Path(".tmp/portfolio-demo.jsonl"))
    demo.add_argument("--budget", type=int, default=1800)
    demo.add_argument(
        "--color", choices=("auto", "always", "never"), default="auto",
        help="highlight demo events with terminal colors",
    )
    evaluate = sub.add_parser("evaluate", help="run deterministic with/without-memory evaluation")
    evaluate.add_argument("--vault", type=Path, default=Path("data/demo-vault"))
    evaluate.add_argument("--fixtures", type=Path, default=Path("data/evaluation/golden_cases.json"))
    evaluate.add_argument("--database", type=Path, default=Path(".tmp/evaluation.duckdb"))
    evaluate.add_argument("--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "receipt":
        print(render_receipt(load_trace(args.trace_file)))
        return 0
    if args.command == "serve":
        server = create_server(
            args.host, args.port, args.database, args.trace,
            os.getenv("CONTEXTVAULT_API_TOKEN"), args.provider,
        )
        print(f"ContextVault listening on http://{args.host}:{server.server_port}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()
        return 0
    if args.command == "evaluate":
        args.database.parent.mkdir(parents=True, exist_ok=True)
        report = run_evaluation(args.database, args.vault, args.fixtures)
        markdown = render_markdown(report)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(markdown, encoding="utf-8")
            print(f"Wrote evaluation report to {args.output}")
        print(markdown, end="")
        return 0 if report["all_expected_passed"] else 1
    if args.command == "demo":
        use_color = args.color == "always" or (
            args.color == "auto" and sys.stdout.isatty() and "NO_COLOR" not in os.environ
        )
        print(run_portfolio_demo(
            args.vault, args.database, args.trace_output, args.budget, color=use_color
        ))
        return 0
    service = MemoryService(args.database, args.trace)
    if args.command == "ingest":
        print(f"Indexed {service.ingest(args.vault)} memories into {args.database}")
        return 0
    if args.command == "remember":
        decision, slug = service.remember_preference(args.session, args.text)
        print(f"{decision.outcome.upper()}: {decision.reason}" + (f" ({slug})" if slug else ""))
        return 0 if decision.outcome in {"allow", "redact"} else 2
    if args.command == "recall":
        print(service.get_memory_pack(args.task, args.budget))
        return 0
    if args.command == "relations":
        edges = service.expand_relations(args.slug)
        for edge in edges:
            print(f"{edge['direction']}: {edge['source_slug']} -[{edge['relation_type']}]-> {edge['target_slug']}")
        return 0
    if args.command == "ask":
        providers = {"mock": MockProvider, "ollama": OllamaProvider, "qwen": QwenCompatibleProvider}
        provider = providers[args.provider]()
        agent = MemoryAgent(service, provider)
        try:
            result = agent.answer(args.task, args.budget, not args.without_memory)
        except ProviderError as exc:
            print(f"PROVIDER ERROR: {exc}")
            return 3
        print(f"ANSWER [{result.provider}/{result.model}]")
        print(result.answer)
        if result.receipt:
            print("\nCONTEXT RECEIPT")
            print(result.receipt)
        return 0
    return 0
