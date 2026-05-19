from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Union

from .constants import (
    ALL_ENGINES,
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
    PROJECT_ROOT,
    RUN_ID_LENGTH,
    SCHEMA_VERSION,
)
from .core import now_period, parse_period, scrub_secrets, utc_now_iso
from .data import DataProcessing
from .display import build_composite
from .exports import export_bundle, export_card, export_debug_bundle, export_debug_card, export_index, export_manifest, public_card_path
from .generators import GENERATOR_BY_ENGINE
from .interpreter import build_card
from .llm import LLMClient, LLMParams
from .schemas import AssetRef, CardResult, EngineRef, OracleCard, PeriodRef, ReadingBundle


@dataclass
class GenerateRequest:
    period: str
    symbols: Optional[List[str]] = None
    engines: List[str] = field(default_factory=lambda: list(ALL_ENGINES))
    seed: Optional[int] = None
    force: Union[bool, str, List[str]] = False
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
    engine_overrides: Dict[str, Any] = field(default_factory=dict)
    api_key: Optional[str] = None

    def llm_params(self) -> LLMParams:
        return LLMParams(
            provider=self.provider,
            model=self.model,
            base_url=self.base_url,
            temperature=self.temperature,
            top_p=self.top_p,
            max_output_tokens=self.max_output_tokens,
            reasoning_effort=self.reasoning_effort,
            timeout=self.timeout,
            max_retries=self.max_retries,
            codex_auth_path=self.codex_auth_path,
            codex_home=self.codex_home,
            codex_path=self.codex_path,
            history_run_id=self.history_run_id,
            api_key=self.api_key,
        )


def run_generation(request: GenerateRequest) -> Dict[str, Any]:
    period = parse_period(request.period)
    engines = _normalize_engines(request.engines)
    output_root = Path(request.output_root)
    run_id = uuid.uuid4().hex[:RUN_ID_LENGTH]
    generated_at = utc_now_iso()
    data = DataProcessing(PROJECT_ROOT)
    available_symbols = data.discover_symbols()
    symbols = [s.upper() for s in (request.symbols or available_symbols)]
    unknown = sorted(set(symbols) - set(available_symbols))
    if unknown:
        raise ValueError(f"Unknown symbols: {unknown}; available: {available_symbols}")

    llm = LLMClient(request.llm_params())
    bundles: List[ReadingBundle] = []
    card_paths: List[str] = []
    skipped_cards = 0
    generated_cards = 0
    force_engines = _normalize_force(request.force)
    for ticker in symbols:
        context = data.context_for(ticker).to_dict()
        asset = AssetRef(ticker=ticker, name=ticker, region=str(context["region"]))
        cards = []
        for engine_id in engines:
            existing_public_path = public_card_path(
                OracleCard(
                    schema_version=SCHEMA_VERSION,
                    asset=asset,
                    period=period,
                    engine=EngineRef(engine_id, engine_id, engine_id),
                    result=CardResult(50, "neutral", "low", "existing", "", "", "", ""),
                    symbols=[],
                    risk_tags=[],
                    raw_artifact={},
                    visual={},
                ),
                period.id,
                output_root,
            )
            if not _should_force_engine(engine_id, force_engines) and existing_public_path.exists():
                card = _card_from_public_json(existing_public_path)
                cards.append(card)
                card_paths.append(str(existing_public_path))
                skipped_cards += 1
                continue

            generator = GENERATOR_BY_ENGINE[engine_id]()
            raw_artifact = generator.generate(asset, period, context, seed=request.seed)
            raw_artifact["frontend_params"] = {
                "language": request.language,
                "tone": request.tone,
                "reading_depth": request.reading_depth,
                "engine_overrides": request.engine_overrides.get(engine_id, {}),
            }
            card = build_card(
                engine_id=engine_id,
                asset=asset,
                period=period,
                raw_artifact=raw_artifact,
                llm=llm,
                include_market_context=request.include_market_context,
                allow_error_card=request.allow_error_cards,
            )
            debug_path = export_debug_card(run_id=run_id, card=card)
            card.raw_ref = _relative_posix(debug_path, PROJECT_ROOT)
            cards.append(card)
            card_paths.append(
                str(
                    export_card(
                        card,
                        period.id,
                        output_root,
                        include_raw_artifact=request.include_raw_artifact,
                        include_market_context=request.include_market_context,
                    )
                )
            )
            generated_cards += 1

        bundle = ReadingBundle(
            schema_version=SCHEMA_VERSION,
            asset=asset,
            period=period,
            composite=build_composite(cards),
            cards=cards,
            run_id=run_id,
            generation_params=_debug_request_dict(request),
        )
        export_debug_bundle(run_id=run_id, bundle=bundle)
        export_bundle(
            bundle,
            output_root,
            include_raw_artifact=request.include_raw_artifact,
            include_market_context=request.include_market_context,
            include_generation_params=False,
        )
        bundles.append(bundle)

    coverage = {
        ticker: {
            "data_start": data.context_for(ticker).data_start,
            "data_end": data.context_for(ticker).data_end,
            "observations": data.context_for(ticker).observations,
        }
        for ticker in symbols
    }
    export_index(
        period=period.id,
        symbols=symbols,
        engines=engines,
        run_id=run_id,
        output_root=output_root,
        generated_at=generated_at,
        data_coverage=coverage,
        params=_public_request_dict(request),
    )
    manifest = {
        "run_id": run_id,
        "generated_at": generated_at,
        "period": period.id,
        "period_label": period.label,
        "symbols": symbols,
        "engines": engines,
        "request": _debug_request_dict(request),
        "card_paths": card_paths,
        "bundle_count": len(bundles),
        "generated_cards": generated_cards,
        "skipped_cards": skipped_cards,
    }
    export_manifest(run_id=run_id, manifest=manifest)
    return {
        "run_id": run_id,
        "period": period.id,
        "symbols": symbols,
        "engines": engines,
        "bundle_count": len(bundles),
        "card_count": len(card_paths),
        "generated_cards": generated_cards,
        "skipped_cards": skipped_cards,
        "output_root": str(output_root),
    }


def _normalize_engines(raw: Iterable[str]) -> List[str]:
    engines = [str(e).strip().lower() for e in raw if str(e).strip()]
    invalid = [e for e in engines if e not in ALL_ENGINES]
    if invalid:
        raise ValueError(f"Unsupported engines: {invalid}; allowed: {list(ALL_ENGINES)}")
    return engines or list(ALL_ENGINES)


def _public_request_dict(request: GenerateRequest) -> Dict[str, Any]:
    data = asdict(request)
    for key in ("base_url", "codex_auth_path", "codex_home", "codex_path"):
        data.pop(key, None)
    return scrub_secrets(data)


def _debug_request_dict(request: GenerateRequest) -> Dict[str, Any]:
    return scrub_secrets(asdict(request))


def _normalize_force(force: Union[bool, str, List[str]]) -> set[str]:
    if force is True:
        return {"all"}
    if not force:
        return set()
    if isinstance(force, str):
        text = force.strip().lower()
        if not text:
            return set()
        return {item.strip() for item in text.split(",") if item.strip()}
    return {str(item).strip().lower() for item in force if str(item).strip()}


def _should_force_engine(engine_id: str, force_engines: set[str]) -> bool:
    return "all" in force_engines or engine_id in force_engines


def _relative_posix(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _card_from_public_json(path: Path) -> OracleCard:
    data = json.loads(path.read_text(encoding="utf-8"))
    asset = AssetRef(**data["asset"])
    period = PeriodRef(**data["period"])
    engine = EngineRef(**data["engine"])
    result = CardResult(**data["result"])
    result_en = CardResult(**data["result_en"]) if isinstance(data.get("result_en"), dict) else None
    return OracleCard(
        schema_version=data.get("schema_version", SCHEMA_VERSION),
        asset=asset,
        period=period,
        engine=engine,
        result=result,
        symbols=list(data.get("symbols", [])),
        risk_tags=list(data.get("risk_tags", [])),
        raw_artifact=dict(data.get("raw_artifact", {})),
        visual=dict(data.get("visual", {})),
        market_context=data.get("market_context"),
        raw_ref=data.get("raw_ref"),
        error=data.get("error"),
        result_en=result_en,
    )
