from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from .constants import DEFAULT_OUTPUT_ROOT, DEFAULT_RUNS_ROOT
from .core import scrub_secrets
from .schemas import OracleCard, ReadingBundle


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def public_card_path(card: OracleCard, period_id: str, output_root: Path = DEFAULT_OUTPUT_ROOT) -> Path:
    return output_root / "cards" / period_id / card.asset.ticker / f"{card.engine.id}.json"


def export_card(
    card: OracleCard,
    period_id: str,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    *,
    include_raw_artifact: bool = False,
    include_market_context: bool = False,
) -> Path:
    path = public_card_path(card, period_id, output_root)
    write_json(
        path,
        card.to_dict(
            include_raw_artifact=include_raw_artifact,
            include_market_context=include_market_context,
        ),
    )
    return path


def export_bundle(
    bundle: ReadingBundle,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    *,
    include_raw_artifact: bool = False,
    include_market_context: bool = False,
    include_generation_params: bool = False,
) -> Path:
    path = output_root / "readings" / bundle.period.id / bundle.asset.ticker / "index.json"
    payload = bundle.to_dict(
        include_raw_artifact=include_raw_artifact,
        include_market_context=include_market_context,
        include_generation_params=include_generation_params,
    )
    write_json(path, payload)
    flat_path = output_root / "readings" / bundle.period.id / f"{bundle.asset.ticker}.json"
    write_json(flat_path, payload)
    return path


def export_index(*, period: str, symbols: Iterable[str], engines: Iterable[str], run_id: str, output_root: Path, generated_at: str, data_coverage: Dict[str, Any], params: Dict[str, Any]) -> Path:
    payload = {
        "schema_version": "0.1",
        "period": period,
        "symbols": list(symbols),
        "engines": list(engines),
        "run_id": run_id,
        "generated_at": generated_at,
        "data_coverage": data_coverage,
        "params": scrub_secrets(params),
    }
    path = output_root / "index.json"
    write_json(path, payload)
    return path


def export_manifest(*, run_id: str, manifest: Dict[str, Any], runs_root: Path = DEFAULT_RUNS_ROOT) -> Path:
    path = runs_root / run_id / "manifest.json"
    write_json(path, scrub_secrets(manifest))
    return path


def export_debug_card(*, run_id: str, card: OracleCard, runs_root: Path = DEFAULT_RUNS_ROOT) -> Path:
    path = runs_root / run_id / "debug" / "cards" / card.period.id / card.asset.ticker / f"{card.engine.id}.json"
    write_json(
        path,
        scrub_secrets(
            card.to_dict(include_raw_artifact=True, include_market_context=True)
        ),
    )
    return path


def export_debug_bundle(*, run_id: str, bundle: ReadingBundle, runs_root: Path = DEFAULT_RUNS_ROOT) -> Path:
    path = runs_root / run_id / "debug" / "readings" / bundle.period.id / f"{bundle.asset.ticker}.json"
    write_json(
        path,
        scrub_secrets(
            bundle.to_dict(
                include_raw_artifact=True,
                include_market_context=True,
                include_generation_params=True,
            )
        ),
    )
    return path


def load_public_card(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
