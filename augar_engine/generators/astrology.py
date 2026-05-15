from __future__ import annotations

from typing import Any, Dict

from ..schemas import AssetRef, PeriodRef
from .base import BaseGenerator

ZODIAC = ("Capricorn", "Aquarius", "Pisces", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius")


class AstrologyGenerator(BaseGenerator):
    engine_id = "astrology"

    def generate(self, asset: AssetRef, period: PeriodRef, market_context: Dict[str, Any], seed: int | None = None) -> Dict[str, Any]:
        month = int(period.id[5:7]) if period.freq == "M" else 1
        rng = self.rng(asset, period, seed)
        artifact = self.base_artifact(asset, period, market_context, seed)
        artifact.update({
            "sop": "asset zodiac proxy, zodiac season, moon/cycle tags before market mood interpretation",
            "asset_zodiac": ZODIAC[(len(asset.ticker) + rng.randrange(12)) % 12],
            "period_zodiac_season": ZODIAC[(month - 1) % 12],
            "moon_phase_proxy": ["new", "waxing", "full", "waning"][rng.randrange(4)],
            "cycle_tags": [
                market_context.get("momentum_label", "mixed"),
                market_context.get("volatility_label", "normal"),
                "visibility_cycle" if month in (3, 6, 9, 12) else "accumulation_cycle",
            ],
        })
        return artifact
