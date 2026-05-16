from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIGS_ROOT = PROJECT_ROOT / "configs"


def _load_json(path: Path) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


_DEFAULTS = _load_json(CONFIGS_ROOT / "defaults.json")
_MARKET = _load_json(CONFIGS_ROOT / "market_thresholds.json")


# ── paths ──────────────────────────────────────────────
_p = _DEFAULTS["paths"]
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / _p["output_root"]
DEFAULT_RUNS_ROOT = PROJECT_ROOT / _p["runs_root"]
DEFAULT_DATA_ROOT = PROJECT_ROOT / _p["data_root"]
DEFAULT_PARQUET_FILES = tuple(_p["parquet_files"])
REGION_BY_FILE = dict(_p["region_by_file"])

# ── engines & providers ────────────────────────────────
ALL_ENGINES = tuple(_DEFAULTS["engines"])
ALL_PROVIDERS = tuple(_DEFAULTS["providers"])

# ── LLM defaults ───────────────────────────────────────
_llm = _DEFAULTS["llm"]
DEFAULT_PROVIDER: str = _llm["provider"]
DEFAULT_MODEL: str = _llm["model"]
DEFAULT_TEMPERATURE: float = _llm["temperature"]
DEFAULT_TOP_P: float = _llm["top_p"]
DEFAULT_MAX_OUTPUT_TOKENS: int = _llm["max_output_tokens"]
DEFAULT_REASONING_EFFORT: str = _llm["reasoning_effort"]
DEFAULT_TIMEOUT: int = _llm["timeout"]
DEFAULT_MAX_RETRIES: int = _llm["max_retries"]
OPENAI_BASE_URL: str = _llm["openai_base_url"]
CODEX_CHECK_TIMEOUT: int = _llm["codex_check_timeout"]

# ── generation defaults ────────────────────────────────
_gen = _DEFAULTS["generation"]
DEFAULT_LANGUAGE: str = _gen["language"]
DEFAULT_TONE: str = _gen["tone"]
DEFAULT_READING_DEPTH: str = _gen["reading_depth"]
DEFAULT_INCLUDE_RAW: bool = _gen["include_raw_artifact"]
DEFAULT_INCLUDE_MARKET: bool = _gen["include_market_context"]
DEFAULT_ALLOW_ERRORS: bool = _gen["allow_error_cards"]

# ── limits ─────────────────────────────────────────────
_lim = _DEFAULTS["limits"]
MAX_SYMBOLS_PER_CARD: int = _lim["max_symbols_per_card"]
MAX_RISK_TAGS: int = _lim["max_risk_tags"]
DEFAULT_RISK_TAG: str = _lim["default_risk_tag"]
DOMINANT_SYMBOLS_COUNT: int = _lim["dominant_symbols_count"]
SCORE_HIGH_THRESHOLD: int = _lim["score_high_threshold"]
SCORE_LOW_THRESHOLD: int = _lim["score_low_threshold"]
RUN_ID_LENGTH: int = _lim["run_id_length"]

# ── misc ───────────────────────────────────────────────
SCHEMA_VERSION: str = _DEFAULTS["schema_version"]
API_TITLE: str = _DEFAULTS["api"]["title"]
API_VERSION: str = _DEFAULTS["api"]["version"]

# ── error card ─────────────────────────────────────────
_ec = _DEFAULTS["error_card"]
ERROR_CARD_SCORE: int = _ec["score"]
ERROR_CARD_POLARITY: str = _ec["polarity"]
ERROR_CARD_INTENSITY: str = _ec["intensity"]
ERROR_CARD_VISUAL: Dict[str, str] = dict(_ec["visual"])

# ── market thresholds (re-export for convenience) ──────
MARKET_THRESHOLDS: Dict[str, Any] = _MARKET

