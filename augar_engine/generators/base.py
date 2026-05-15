from __future__ import annotations

import random
from dataclasses import asdict
from typing import Any, Dict

from ..core import stable_seed
from ..schemas import AssetRef, PeriodRef


class BaseGenerator:
    engine_id = "base"

    def rng(self, asset: AssetRef, period: PeriodRef, seed: int | None = None) -> random.Random:
        return random.Random(seed if seed is not None else stable_seed(self.engine_id, asset.ticker, period.id))

    def base_artifact(self, asset: AssetRef, period: PeriodRef, market_context: Dict[str, Any], seed: int | None) -> Dict[str, Any]:
        return {
            "seed": f"{self.engine_id}|{asset.ticker}|{period.id}|{seed if seed is not None else 'stable'}",
            "engine_id": self.engine_id,
            "asset": asdict(asset),
            "period": asdict(period),
            "market_context": market_context,
        }
