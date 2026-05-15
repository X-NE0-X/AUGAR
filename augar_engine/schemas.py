from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AssetRef:
    ticker: str
    name: str
    region: str
    asset_class: str = "INDEX"


@dataclass
class PeriodRef:
    id: str
    label: str
    freq: str


@dataclass
class EngineRef:
    id: str
    name: str
    display_name: str


@dataclass
class CardResult:
    score: int
    polarity: str
    intensity: str
    omen_type: str
    headline: str
    subline: str
    short_reading: str
    long_reading: str


@dataclass
class OracleCard:
    schema_version: str
    asset: AssetRef
    period: PeriodRef
    engine: EngineRef
    result: CardResult
    symbols: List[str]
    risk_tags: List[str]
    raw_artifact: Dict[str, Any]
    visual: Dict[str, Any]
    market_context: Optional[Dict[str, Any]] = None
    raw_ref: Optional[str] = None
    error: Optional[Dict[str, Any]] = None

    def to_dict(self, *, include_raw_artifact: bool = True, include_market_context: bool = True) -> Dict[str, Any]:
        data = asdict(self)
        if not include_raw_artifact:
            data.pop("raw_artifact", None)
            if self.raw_ref:
                data["raw_ref"] = self.raw_ref
        if not include_market_context:
            data.pop("market_context", None)
        return data


@dataclass
class ReadingComposite:
    score: int
    polarity: str
    intensity: str
    dominant_symbols: List[str]
    headline: str


@dataclass
class ReadingBundle:
    schema_version: str
    asset: AssetRef
    period: PeriodRef
    composite: ReadingComposite
    cards: List[OracleCard]
    run_id: str
    generation_params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(
        self,
        *,
        include_raw_artifact: bool = True,
        include_market_context: bool = True,
        include_generation_params: bool = True,
    ) -> Dict[str, Any]:
        data = {
            "schema_version": self.schema_version,
            "asset": asdict(self.asset),
            "period": asdict(self.period),
            "composite": asdict(self.composite),
            "cards": [
                card.to_dict(
                    include_raw_artifact=include_raw_artifact,
                    include_market_context=include_market_context,
                )
                for card in self.cards
            ],
            "run_id": self.run_id,
        }
        if include_generation_params:
            data["generation_params"] = self.generation_params
        return data
