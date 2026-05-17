from __future__ import annotations

from typing import Any, Dict, Optional

from .constants import (
    DEFAULT_RISK_TAG,
    ERROR_CARD_INTENSITY,
    ERROR_CARD_POLARITY,
    ERROR_CARD_SCORE,
    ERROR_CARD_VISUAL,
    MAX_RISK_TAGS,
    MAX_SYMBOLS_PER_CARD,
    SCHEMA_VERSION,
)
from .llm import LLMClient
from .schemas import AssetRef, CardResult, EngineRef, OracleCard, PeriodRef

ENGINE_META = {
    "tarot": EngineRef("tarot", "Tarot Celtic Cross", "塔罗"),
    "wenwang": EngineRef("wenwang", "Wenwang Liuyao", "文王卦"),
    "bazi": EngineRef("bazi", "Zi Ping BaZi", "子平八字"),
    "ziwei": EngineRef("ziwei", "Ziwei Doushu", "紫微斗数"),
    "astrology": EngineRef("astrology", "Astrology Cycle", "占星"),
    "market_pulse": EngineRef("market_pulse", "Market Pulse", "市场脉冲"),
}


def build_card(
    *,
    engine_id: str,
    asset: AssetRef,
    period: PeriodRef,
    raw_artifact: Dict[str, Any],
    llm: LLMClient,
    include_market_context: bool = True,
    allow_error_card: bool = False,
) -> OracleCard:
    try:
        interpreted = llm.interpret(engine_id, raw_artifact)
        result = _coerce_result(interpreted)
        symbols = _derive_symbols(engine_id, raw_artifact, interpreted)
        risks = [str(x) for x in interpreted.get("risk_tags", [])][:MAX_RISK_TAGS] or [DEFAULT_RISK_TAG]
        visual = interpreted.get("visual") if isinstance(interpreted.get("visual"), dict) else {}
        error = None
        result_en = _translate_result(result)
    except Exception as exc:
        if not allow_error_card:
            raise
        result = CardResult(
            score=ERROR_CARD_SCORE,
            polarity=ERROR_CARD_POLARITY,
            intensity=ERROR_CARD_INTENSITY,
            omen_type=f"{engine_id}_interpreter_error",
            headline=f"{ENGINE_META[engine_id].display_name} interpretation failed",
            subline="Raw artifact was generated, but interpreter failed.",
            short_reading="Interpreter error card.",
            long_reading=str(exc),
        )
        symbols = [engine_id, "interpreter_error"]
        risks = ["interpreter_error"]
        visual = dict(ERROR_CARD_VISUAL)
        error = {"type": type(exc).__name__, "message": str(exc)}
        result_en = None

    return OracleCard(
        schema_version=SCHEMA_VERSION,
        asset=asset,
        period=period,
        engine=ENGINE_META[engine_id],
        result=result,
        symbols=symbols,
        risk_tags=risks,
        raw_artifact=raw_artifact,
        visual=visual,
        market_context=raw_artifact.get("market_context") if include_market_context else None,
        error=error,
        result_en=result_en,
    )


def _derive_symbols(engine_id: str, raw_artifact: Dict[str, Any], interpreted: Dict[str, Any]) -> list[str]:
    """Get symbols intelligently: use deterministic card names for tarot,
    raw artifact fields for other engines, fall back to LLM output."""
    if engine_id == "tarot":
        spread = raw_artifact.get("spread", [])
        cards = [c.get("card", "") for c in spread if c.get("card")]
        if cards:
            return cards[:MAX_SYMBOLS_PER_CARD]
    if engine_id == "wenwang":
        hexagram = raw_artifact.get("primary_hexagram", {})
        changed = raw_artifact.get("changed_hexagram", {})
        parts = []
        if hexagram.get("image"): parts.append(hexagram["image"])
        if changed.get("image"): parts.append(changed["image"])
        if parts:
            return parts[:MAX_SYMBOLS_PER_CARD]
    if engine_id == "bazi":
        s = raw_artifact.get("strength_and_roots", {})
        p = raw_artifact.get("pattern", {})
        parts = []
        if s.get("day_element"): parts.append(s["day_element"])
        if p.get("name"): parts.append(p["name"])
        if parts:
            return parts[:MAX_SYMBOLS_PER_CARD]
    if engine_id == "ziwei":
        parts = []
        if raw_artifact.get("life_master"): parts.append(raw_artifact["life_master"])
        if raw_artifact.get("life_palace"): parts.append(raw_artifact["life_palace"])
        if parts:
            return parts[:MAX_SYMBOLS_PER_CARD]
    if engine_id == "astrology":
        parts = []
        if raw_artifact.get("asset_zodiac"): parts.append(raw_artifact["asset_zodiac"])
        if raw_artifact.get("moon_phase_proxy"): parts.append(raw_artifact["moon_phase_proxy"])
        if parts:
            return parts[:MAX_SYMBOLS_PER_CARD]
    # Fallback: LLM-provided symbols + market context labels
    symbols = [str(x) for x in interpreted.get("symbols", [])][:MAX_SYMBOLS_PER_CARD]
    if symbols:
        return symbols
    ctx = raw_artifact.get("market_context", {})
    return [ctx.get("momentum_label", "mixed"), ctx.get("volatility_label", "normal")][:MAX_SYMBOLS_PER_CARD]


def _coerce_result(data: Dict[str, Any]) -> CardResult:
    score = int(data.get("score", 50))
    score = max(1, min(99, score))
    return CardResult(
        score=score,
        polarity=str(data.get("polarity", "neutral")),
        intensity=str(data.get("intensity", "medium")),
        omen_type=str(data.get("omen_type", "unspecified")),
        headline=str(data.get("headline", "Untitled reading")),
        subline=str(data.get("subline", "")),
        short_reading=str(data.get("short_reading", "")),
        long_reading=str(data.get("long_reading", "")),
    )


def _translate_result(result: CardResult) -> Optional[CardResult]:
    """Translate Chinese card content to English using machine translation.
    Returns None if translation fails — frontend falls back to Chinese."""
    texts = [
        result.headline, result.subline,
        result.short_reading, result.long_reading,
    ]
    try:
        import translators as ts
        translated: list[str] = []
        for text in texts:
            if not text:
                translated.append("")
                continue
            try:
                translated.append(ts.translate_text(text, from_language="zh", to_language="en"))
            except Exception:
                try:
                    translated.append(ts.translate_text(text, from_language="zh", to_language="en"))
                except Exception:
                    translated.append(text)  # fallback: keep original
        return CardResult(
            score=result.score,
            polarity=result.polarity,
            intensity=result.intensity,
            omen_type=result.omen_type,
            headline=translated[0] or result.headline,
            subline=translated[1] or result.subline,
            short_reading=translated[2] or result.short_reading,
            long_reading=translated[3] or result.long_reading,
        )
    except ImportError:
        return None
    except Exception:
        return None
