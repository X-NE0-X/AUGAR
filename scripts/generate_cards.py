from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from augar_engine.constants import ALL_ENGINES
from augar_engine.pipeline import GenerateRequest, run_generation


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate AUGAR oracle cards. Main entrypoint: python AUGAR.py ...")
    parser.add_argument("--config", help="Optional JSON config file. CLI flags override config values.")
    parser.add_argument("--period")
    parser.add_argument("--all-indexes", action="store_true")
    parser.add_argument("--symbols", default="")
    parser.add_argument("--engines")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--force", nargs="?", const="all", default=None, help="Skip existing cards by default. Use --force or --force all to regenerate all, or --force tarot,wenwang for selected engines.")
    parser.add_argument("--output-root", default="")
    parser.add_argument("--provider")
    parser.add_argument("--model")
    parser.add_argument("--base-url")
    parser.add_argument("--temperature", type=float)
    parser.add_argument("--top-p", type=float)
    parser.add_argument("--max-output-tokens", type=int)
    parser.add_argument("--reasoning-effort")
    parser.add_argument("--timeout", type=int)
    parser.add_argument("--max-retries", type=int)
    parser.add_argument("--codex-auth-path")
    parser.add_argument("--codex-home")
    parser.add_argument("--codex-path")
    parser.add_argument("--history-run-id")
    parser.add_argument("--allow-error-cards", action="store_true")
    parser.add_argument("--include-raw-artifact", action="store_true")
    parser.add_argument("--include-market-context", action="store_true")
    args = parser.parse_args()
    config = {}
    if args.config:
        config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    period = args.period or config.get("period")
    if not period:
        parser.error("--period is required unless provided by --config")

    symbols = None if args.all_indexes or not (args.symbols or config.get("symbols")) else [
        s.strip().upper() for s in str(args.symbols or ",".join(config.get("symbols", []))).split(",") if s.strip()
    ]
    request = GenerateRequest(
        period=period,
        symbols=symbols,
        engines=[e.strip() for e in str(args.engines or ",".join(config.get("engines", ALL_ENGINES))).split(",") if e.strip()],
        seed=args.seed if args.seed is not None else config.get("seed"),
        force=args.force if args.force is not None else config.get("force", False),
        provider=args.provider or config.get("provider", "mock"),
        model=args.model or config.get("model", "gpt-5.5"),
        base_url=args.base_url or config.get("base_url"),
        temperature=args.temperature if args.temperature is not None else config.get("temperature", 0.4),
        top_p=args.top_p if args.top_p is not None else config.get("top_p", 1.0),
        max_output_tokens=args.max_output_tokens if args.max_output_tokens is not None else config.get("max_output_tokens", 1200),
        reasoning_effort=args.reasoning_effort or config.get("reasoning_effort", "low"),
        timeout=args.timeout if args.timeout is not None else config.get("timeout", 90),
        max_retries=args.max_retries if args.max_retries is not None else config.get("max_retries", 2),
        codex_auth_path=args.codex_auth_path or config.get("codex_auth_path"),
        codex_home=args.codex_home or config.get("codex_home"),
        codex_path=args.codex_path or config.get("codex_path"),
        history_run_id=args.history_run_id or config.get("history_run_id"),
        include_raw_artifact=args.include_raw_artifact or bool(config.get("include_raw_artifact", False)),
        include_market_context=args.include_market_context or bool(config.get("include_market_context", False)),
        allow_error_cards=args.allow_error_cards or bool(config.get("allow_error_cards", False)),
    )
    if args.output_root:
        request.output_root = args.output_root
    print(run_generation(request))


if __name__ == "__main__":
    main()
