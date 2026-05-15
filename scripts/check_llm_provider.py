from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from augar_engine.llm import LLMClient, LLMParams


def main() -> None:
    parser = argparse.ArgumentParser(description="Check AUGAR LLM provider connectivity")
    parser.add_argument("--provider", default="mock")
    parser.add_argument("--model", default="gpt-5.5")
    parser.add_argument("--base-url")
    parser.add_argument("--codex-auth-path")
    parser.add_argument("--codex-home")
    parser.add_argument("--codex-path")
    parser.add_argument("--max-output-tokens", type=int, default=200)
    args = parser.parse_args()

    if args.provider == "chatgpt_oauth":
        print_chatgpt_oauth_scope(args.codex_auth_path)

    client = LLMClient(LLMParams(
        provider=args.provider,
        model=args.model,
        base_url=args.base_url,
        codex_auth_path=args.codex_auth_path,
        codex_home=args.codex_home,
        codex_path=args.codex_path,
        max_output_tokens=args.max_output_tokens,
        timeout=45,
        max_retries=0,
    ))
    artifact = {
        "engine_id": "market_pulse",
        "asset": {"ticker": "SPX"},
        "period": {"id": "2026-04-M", "label": "April 2026"},
        "market_context": {"ticker": "SPX", "return_63d": 0.01, "volatility_63d": 0.15, "drawdown_252d": -0.02, "momentum_label": "rising", "volatility_label": "normal"},
    }
    result = client.interpret("market_pulse", artifact)
    print({"ok": True, "provider": args.provider, "model": args.model, "score": result.get("score"), "headline": result.get("headline")})


def print_chatgpt_oauth_scope(path: str | None) -> None:
    auth_path = Path(path) if path else Path.home() / ".codex" / "auth.json"
    auth = json.loads(auth_path.read_text(encoding="utf-8"))
    token = auth["tokens"]["access_token"]
    payload = token.split(".")[1]
    payload += "=" * ((4 - len(payload) % 4) % 4)
    claims = json.loads(base64.urlsafe_b64decode(payload.encode()))
    print({
        "auth_mode": auth.get("auth_mode"),
        "aud": claims.get("aud"),
        "scopes": claims.get("scp"),
        "plan_type": claims.get("https://api.openai.com/auth", {}).get("chatgpt_plan_type"),
    })


if __name__ == "__main__":
    main()
