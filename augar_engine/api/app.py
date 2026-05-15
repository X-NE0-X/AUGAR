from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from ..constants import ALL_ENGINES, DEFAULT_OUTPUT_ROOT
from ..data import DataProcessing
from ..pipeline import GenerateRequest, run_generation

app = FastAPI(title="AUGAR Backend", version="0.1.0")


class GenerateBody(BaseModel):
    period: str
    symbols: Optional[list[str]] = None
    engines: list[str] = Field(default_factory=lambda: list(ALL_ENGINES))
    seed: Optional[int] = None
    force: Union[bool, str, list[str]] = False
    output_root: str = str(DEFAULT_OUTPUT_ROOT)
    provider: str = "mock"
    model: str = "gpt-5.5"
    base_url: Optional[str] = None
    temperature: float = 0.4
    top_p: float = 1.0
    max_output_tokens: int = 1200
    reasoning_effort: Optional[str] = "low"
    timeout: int = 90
    max_retries: int = 2
    codex_auth_path: Optional[str] = None
    codex_home: Optional[str] = None
    codex_path: Optional[str] = None
    language: str = "zh-CN"
    tone: str = "calm_analytical"
    reading_depth: str = "standard"
    include_raw_artifact: bool = False
    include_market_context: bool = False
    allow_error_cards: bool = False
    engine_overrides: dict = Field(default_factory=dict)


@app.get("/health")
def health() -> dict:
    data = DataProcessing()
    return {"status": "ok", "symbols": data.discover_symbols(), "engines": list(ALL_ENGINES)}


@app.get("/metadata/options")
def metadata_options() -> dict:
    return {
        "engines": list(ALL_ENGINES),
        "providers": ["mock", "openai", "chatgpt_oauth", "openai_compatible", "local", "custom"],
        "model_params": [
            "model", "provider", "base_url", "temperature", "top_p", "max_output_tokens",
            "reasoning_effort", "timeout", "max_retries",
            "codex_auth_path",
            "codex_home", "codex_path",
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
