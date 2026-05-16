from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from ..constants import (
    ALL_ENGINES,
    ALL_PROVIDERS,
    API_TITLE,
    API_VERSION,
    DEFAULT_ALLOW_ERRORS,
    DEFAULT_INCLUDE_MARKET,
    DEFAULT_INCLUDE_RAW,
    DEFAULT_LANGUAGE,
    DEFAULT_MAX_OUTPUT_TOKENS,
    DEFAULT_MAX_RETRIES,
    DEFAULT_MODEL,
    DEFAULT_OUTPUT_ROOT,
    DEFAULT_PROVIDER,
    DEFAULT_READING_DEPTH,
    DEFAULT_REASONING_EFFORT,
    DEFAULT_TEMPERATURE,
    DEFAULT_TIMEOUT,
    DEFAULT_TONE,
    DEFAULT_TOP_P,
)
from ..data import DataProcessing
from ..pipeline import GenerateRequest, run_generation

app = FastAPI(title=API_TITLE, version=API_VERSION)


class GenerateBody(BaseModel):
    period: str
    symbols: Optional[list[str]] = None
    engines: list[str] = Field(default_factory=lambda: list(ALL_ENGINES))
    seed: Optional[int] = None
    force: Union[bool, str, list[str]] = False
    output_root: str = str(DEFAULT_OUTPUT_ROOT)
    provider: str = DEFAULT_PROVIDER
    model: str = DEFAULT_MODEL
    base_url: Optional[str] = None
    temperature: float = DEFAULT_TEMPERATURE
    top_p: float = DEFAULT_TOP_P
    max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS
    reasoning_effort: Optional[str] = DEFAULT_REASONING_EFFORT
    timeout: int = DEFAULT_TIMEOUT
    max_retries: int = DEFAULT_MAX_RETRIES
    codex_auth_path: Optional[str] = None
    codex_home: Optional[str] = None
    codex_path: Optional[str] = None
    history_run_id: Optional[str] = None
    language: str = DEFAULT_LANGUAGE
    tone: str = DEFAULT_TONE
    reading_depth: str = DEFAULT_READING_DEPTH
    include_raw_artifact: bool = DEFAULT_INCLUDE_RAW
    include_market_context: bool = DEFAULT_INCLUDE_MARKET
    allow_error_cards: bool = DEFAULT_ALLOW_ERRORS
    engine_overrides: dict = Field(default_factory=dict)
    api_key: Optional[str] = None


@app.get("/health/codex")
def health_codex() -> dict:
    try:
        from ..llm import LLMClient
        path = LLMClient._find_codex_executable()
        import subprocess, os
        home = os.getenv("CODEX_HOME", str(Path.home() / ".codex"))
        result = subprocess.run(
            [path, "login", "status"],
            env={**os.environ, "CODEX_HOME": home},
            capture_output=True, text=True, timeout=15,
        )
        return {"available": True, "logged_in": result.returncode == 0, "path": path}
    except Exception as e:
        return {"available": False, "reason": str(e)}
@app.get("/health")
def health() -> dict:
    data = DataProcessing()
    return {"status": "ok", "symbols": data.discover_symbols(), "engines": list(ALL_ENGINES)}


@app.get("/metadata/options")
def metadata_options() -> dict:
    return {
        "engines": list(ALL_ENGINES),
        "providers": list(ALL_PROVIDERS),
        "model_params": [
            "model", "provider", "base_url", "temperature", "top_p", "max_output_tokens",
            "reasoning_effort", "timeout", "max_retries",
            "codex_auth_path",
            "codex_home", "codex_path",
            "history_run_id",
        ],
        "generation_params": [
            "period", "symbols", "engines", "seed", "force", "output_root", "language",
            "tone", "reading_depth", "include_raw_artifact", "include_market_context", "engine_overrides",
            "allow_error_cards",
        ],
    }


@app.post("/generate")
def generate(body: GenerateBody) -> dict:
    payload = body.model_dump() if hasattr(body, "model_dump") else body.dict()
    return run_generation(GenerateRequest(**payload))


@app.get("/readings/{period}/{ticker}")
def get_reading(period: str, ticker: str) -> dict:
    path = Path(DEFAULT_OUTPUT_ROOT) / "readings" / period / f"{ticker.upper()}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="reading not found")
    import json
    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/cards/{period}/{ticker}/{engine}")
def get_card(period: str, ticker: str, engine: str) -> dict:
    path = Path(DEFAULT_OUTPUT_ROOT) / "cards" / period / ticker.upper() / f"{engine}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="card not found")
    import json
    return json.loads(path.read_text(encoding="utf-8"))
