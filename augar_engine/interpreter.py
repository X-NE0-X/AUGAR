from __future__ import annotations

from typing import Any, Dict

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
        symbols = [str(x) for x in interpreted.get("symbols", [])][:8] or [engine_id]
        risks = [str(x) for x in interpreted.get("risk_tags", [])][:8] or ["timing_risk"]
        visual = interpreted.get("visual") if isinstance(interpreted.get("visual"), dict) else {}
        error = None
    except Exception as exc:
        if not allow_error_card:
            raise
        result = CardResult(
            score=50,
            polarity="neutral",
            intensity="low",
            omen_type=f"{engine_id}_interpreter_error",
            headline=f"{ENGINE_META[engine_id].display_name} interpretation failed",
            subline="Raw artifact was generated, but interpreter failed.",
            short_reading="Interpreter error card.",
            long_reading=str(exc),
        )
        symbols = [engine_id, "interpreter_error"]
        risks = ["interpreter_error"]
        visual = {"palette": "gray", "icon": "alert", "card_style": "low"}
        error = {"type": type(exc).__name__, "message": str(exc)}

    return OracleCard(
        schema_version="0.1",
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
    )


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
