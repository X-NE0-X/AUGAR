from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .constants import DEFAULT_OUTPUT_ROOT, DEFAULT_RUNS_ROOT
from .core import scrub_secrets
from .schemas import OracleCard, ReadingBundle


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def export_card(card: OracleCard, period_id: str, output_root: Path = DEFAULT_OUTPUT_ROOT) -> Path:
    path = output_root / "cards" / period_id / card.asset.ticker / f"{card.engine.id}.json"
    write_json(path, card.to_dict())
    return path


def export_bundle(bundle: ReadingBundle, output_root: Path = DEFAULT_OUTPUT_ROOT) -> Path:
    path = output_root / "readings" / bundle.period.id / bundle.asset.ticker / "index.json"
    write_json(path, bundle.to_dict())
    flat_path = output_root / "readings" / bundle.period.id / f"{bundle.asset.ticker}.json"
    write_json(flat_path, bundle.to_dict())
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
