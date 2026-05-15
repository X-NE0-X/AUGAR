from __future__ import annotations

from typing import Any, Dict

from ..schemas import AssetRef, PeriodRef
from .base import BaseGenerator


class MarketPulseGenerator(BaseGenerator):
    engine_id = "market_pulse"

    def generate(self, asset: AssetRef, period: PeriodRef, market_context: Dict[str, Any], seed: int | None = None) -> Dict[str, Any]:
        artifact = self.base_artifact(asset, period, market_context, seed)
        artifact.update({
            "sop": "market pulse program: momentum, volatility, drawdown and trend labels before narrative interpretation",
            "pulse": {
                "latest_close": market_context["latest_close"],
                "return_21d": market_context["return_21d"],
                "return_63d": market_context["return_63d"],
                "volatility_63d": market_context["volatility_63d"],
                "drawdown_252d": market_context["drawdown_252d"],
                "momentum_label": market_context["momentum_label"],
                "volatility_label": market_context["volatility_label"],
                "drawdown_label": market_context["drawdown_label"],
            },
        })
        return artifact
