from __future__ import annotations

from typing import Any, Dict, List

from ..core import stable_seed
from ..schemas import AssetRef, PeriodRef
from .base import BaseGenerator
from .bazi import BRANCHES, STEMS

PALACES = ("Life", "Siblings", "Spouse", "Children", "Wealth", "Health", "Travel", "Friends", "Career", "Property", "Fortune", "Parents")
MAIN_STARS = ("Ziwei", "Tianji", "Taiyang", "Wuqu", "Tiantong", "Lianzhen", "Tianfu", "Taiyin", "Tanlang", "Jumen", "Tianxiang", "Tianliang", "Qisha", "Pojun")
AUX_STARS = ("Zuofu", "Youbi", "Wenchang", "Wenqu", "Lucun", "Qingyang", "Tuoluo", "Huoxing", "Lingxing", "Tiankui", "Tianyue")
TRANSFORMATIONS = ("Hua Lu", "Hua Quan", "Hua Ke", "Hua Ji")


class ZiweiGenerator(BaseGenerator):
    engine_id = "ziwei"

    def generate(self, asset: AssetRef, period: PeriodRef, market_context: Dict[str, Any], seed: int | None = None) -> Dict[str, Any]:
        rng = self.rng(asset, period, seed)
        offset = stable_seed(asset.ticker, period.id) % 12
        life_idx = offset
        body_idx = (offset + 4 + len(asset.region)) % 12
        palaces = []
        for i, name in enumerate(PALACES):
            branch = BRANCHES[(i + offset) % 12]
            palaces.append({
                "index": i + 1,
                "name": name,
                "branch": branch,
                "stem": STEMS[(i + offset) % 10],
                "main_stars": [],
                "aux_stars": [],
                "transformations": [],
            })

        for idx, star in enumerate(MAIN_STARS):
            palaces[(idx * 2 + offset) % 12]["main_stars"].append(star)
        for idx, star in enumerate(AUX_STARS):
            palaces[(idx * 3 + offset + rng.randrange(3)) % 12]["aux_stars"].append(star)
        for idx, trans in enumerate(TRANSFORMATIONS):
            palaces[(offset + idx * 3) % 12]["transformations"].append({"name": trans, "source": "natal"})
            palaces[(offset + idx * 3 + 1) % 12]["transformations"].append({"name": trans, "source": "period"})

        five_element局 = ["Water 2", "Wood 3", "Metal 4", "Earth 5", "Fire 6"][offset % 5]
        major_limits = self._major_limits(offset, market_context["data_start"])
        artifact = self.base_artifact(asset, period, market_context, seed)
        artifact.update({
            "sop": "Sanhe + Qintian Sihua: true solar proxy, twelve palaces, life/body palace, five-element bureau, fourteen main stars, auxiliaries, transformations, major limits, annual flow before interpretation",
            "time_basis": {
                "clock_proxy": market_context["data_start"],
                "true_solar_note": "asset proxy uses market data_start; precise human birth-time conversion is not applicable for index assets",
                "lunar_calendar_note": "v0.1 computes deterministic lunar-style palace proxy for assets",
            },
            "life_palace": palaces[life_idx]["name"],
            "body_palace": palaces[body_idx]["name"],
            "five_element_bureau": five_element局,
            "life_master": MAIN_STARS[offset % len(MAIN_STARS)],
            "body_master": MAIN_STARS[(offset + 6) % len(MAIN_STARS)],
            "palaces": palaces,
            "major_limits": major_limits,
            "annual_flow": {
                "period": period.id,
                "flow_palace": palaces[(offset + int(period.id[5:7])) % 12]["name"],
                "focus": ["Career", "Wealth", "Fortune"],
            },
            "three_sides_four_orthodox": self._triads(palaces, life_idx),
        })
        return artifact

    @staticmethod
    def _major_limits(offset: int, start_date: str) -> List[Dict[str, Any]]:
        start_year = int(str(start_date)[:4])
        return [
            {
                "age_range": f"{2 + i*10}-{11 + i*10}",
                "palace": PALACES[(offset + i) % 12],
                "calendar_years": f"{start_year + 2 + i*10}-{start_year + 11 + i*10}",
            }
            for i in range(12)
        ]

    @staticmethod
    def _triads(palaces: List[Dict[str, Any]], life_idx: int) -> Dict[str, Any]:
        indexes = [life_idx, (life_idx + 4) % 12, (life_idx + 8) % 12, (life_idx + 6) % 12]
        return {"indexes": [i + 1 for i in indexes], "palaces": [palaces[i]["name"] for i in indexes]}
