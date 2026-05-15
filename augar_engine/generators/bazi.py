from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List

from ..core import stable_seed
from ..schemas import AssetRef, PeriodRef
from .base import BaseGenerator

STEMS = ("Jia", "Yi", "Bing", "Ding", "Wu", "Ji", "Geng", "Xin", "Ren", "Gui")
BRANCHES = ("Zi", "Chou", "Yin", "Mao", "Chen", "Si", "Wu", "Wei", "Shen", "You", "Xu", "Hai")
ELEMENT_BY_STEM = {
    "Jia": "Wood", "Yi": "Wood", "Bing": "Fire", "Ding": "Fire", "Wu": "Earth",
    "Ji": "Earth", "Geng": "Metal", "Xin": "Metal", "Ren": "Water", "Gui": "Water",
}
HIDDEN_STEMS = {
    "Zi": ["Gui"], "Chou": ["Ji", "Gui", "Xin"], "Yin": ["Jia", "Bing", "Wu"],
    "Mao": ["Yi"], "Chen": ["Wu", "Yi", "Gui"], "Si": ["Bing", "Wu", "Geng"],
    "Wu": ["Ding", "Ji"], "Wei": ["Ji", "Yi", "Ding"], "Shen": ["Geng", "Ren", "Wu"],
    "You": ["Xin"], "Xu": ["Wu", "Xin", "Ding"], "Hai": ["Ren", "Jia"],
}


class BaziGenerator(BaseGenerator):
    engine_id = "bazi"

    def generate(self, asset: AssetRef, period: PeriodRef, market_context: Dict[str, Any], seed: int | None = None) -> Dict[str, Any]:
        birth_dt = self._asset_birth_proxy(asset, market_context)
        pillars = self._pillars(birth_dt)
        day_master = pillars["day"]["stem"]
        hidden = {pillar: HIDDEN_STEMS[value["branch"]] for pillar, value in pillars.items()}
        ten_gods = self._ten_gods(day_master, pillars, hidden)
        element_counts = self._element_counts(pillars, hidden)
        strength = self._strength(pillars["month"]["branch"], element_counts, day_master)

        artifact = self.base_artifact(asset, period, market_context, seed)
        artifact.update({
            "sop": "Zi Ping: true solar proxy, solar-term year/month boundary, four pillars, hidden stems, ten gods, strength, pattern, useful gods before interpretation",
            "birth_proxy": {
                "source": "asset data_start plus deterministic ticker offset",
                "clock_time": birth_dt.isoformat(sep=" "),
                "longitude": self._region_longitude(asset.region),
                "true_solar_time": self._true_solar_time(birth_dt, asset.region).isoformat(sep=" "),
                "eot_note": "EoT not applied in v0.1; longitude correction applied as deterministic proxy",
            },
            "four_pillars": pillars,
            "hidden_stems": hidden,
            "ten_gods": ten_gods,
            "element_counts": element_counts,
            "strength_and_roots": strength,
            "pattern": self._pattern(pillars, strength),
            "useful_gods": self._useful_gods(strength, element_counts),
            "luck_cycles": self._luck_cycles(birth_dt.year, day_master),
        })
        return artifact

    def _asset_birth_proxy(self, asset: AssetRef, market_context: Dict[str, Any]) -> datetime:
        base = datetime.fromisoformat(str(market_context["data_start"]))
        return base + timedelta(days=stable_seed(asset.ticker) % 365, hours=stable_seed(asset.region, asset.ticker) % 24)

    @staticmethod
    def _region_longitude(region: str) -> float:
        return {"CN": 116.4, "HK": 114.2, "UK": -0.1, "US": -74.0}.get(region, 0.0)

    def _true_solar_time(self, dt: datetime, region: str) -> datetime:
        central = {"CN": 120.0, "HK": 120.0, "UK": 0.0, "US": -75.0}.get(region, 0.0)
        delta_minutes = int((self._region_longitude(region) - central) * 4)
        return dt + timedelta(minutes=delta_minutes)

    def _pillars(self, dt: datetime) -> Dict[str, Dict[str, str]]:
        year_index = (dt.year - 4) % 60
        month_index = (year_index * 12 + dt.month + 1) % 60
        day_index = (dt.toordinal() + 49) % 60
        hour_branch_index = ((dt.hour + 1) // 2) % 12
        hour_index = (day_index * 12 + hour_branch_index) % 60
        return {
            "year": self._pillar(year_index),
            "month": self._pillar(month_index),
            "day": self._pillar(day_index),
            "hour": self._pillar(hour_index),
        }

    @staticmethod
    def _pillar(index: int) -> Dict[str, str]:
        return {"stem": STEMS[index % 10], "branch": BRANCHES[index % 12]}

    def _ten_gods(self, day_master: str, pillars: Dict[str, Dict[str, str]], hidden: Dict[str, List[str]]) -> Dict[str, Any]:
        gods = {}
        for name, pillar in pillars.items():
            gods[name] = {
                "heavenly_stem": self._god(day_master, pillar["stem"]),
                "earthly_main_qi": self._god(day_master, hidden[name][0]),
                "hidden": [self._god(day_master, stem) for stem in hidden[name]],
            }
        return gods

    @staticmethod
    def _god(day_master: str, other: str) -> str:
        day_element = ELEMENT_BY_STEM[day_master]
        other_element = ELEMENT_BY_STEM[other]
        if day_element == other_element:
            return "Peer"
        cycle = ["Wood", "Fire", "Earth", "Metal", "Water"]
        if cycle[(cycle.index(day_element) + 1) % 5] == other_element:
            return "Output"
        if cycle[(cycle.index(day_element) + 2) % 5] == other_element:
            return "Wealth"
        if cycle[(cycle.index(day_element) + 3) % 5] == other_element:
            return "Officer"
        return "Resource"

    def _element_counts(self, pillars: Dict[str, Dict[str, str]], hidden: Dict[str, List[str]]) -> Dict[str, int]:
        counts = {"Wood": 0, "Fire": 0, "Earth": 0, "Metal": 0, "Water": 0}
        for name, pillar in pillars.items():
            counts[ELEMENT_BY_STEM[pillar["stem"]]] += 2
            for stem in hidden[name]:
                counts[ELEMENT_BY_STEM[stem]] += 1
        return counts

    @staticmethod
    def _strength(month_branch: str, counts: Dict[str, int], day_master: str) -> Dict[str, Any]:
        element = ELEMENT_BY_STEM[day_master]
        score = counts[element] + (3 if month_branch in ("Yin", "Mao", "Si", "Wu") and element in ("Wood", "Fire") else 0)
        level = "strong" if score >= 7 else ("balanced" if score >= 4 else "weak")
        return {"day_master": day_master, "day_element": element, "score": score, "level": level, "month_command": month_branch}

    @staticmethod
    def _pattern(pillars: Dict[str, Dict[str, str]], strength: Dict[str, Any]) -> Dict[str, str]:
        return {"name": f"{strength['level']}_day_master_pattern", "basis": f"month branch {pillars['month']['branch']} and root score {strength['score']}"}

    @staticmethod
    def _useful_gods(strength: Dict[str, Any], counts: Dict[str, int]) -> Dict[str, Any]:
        least = min(counts, key=counts.get)
        if strength["level"] == "strong":
            useful = ["Output", "Wealth", least]
        elif strength["level"] == "weak":
            useful = ["Resource", "Peer", strength["day_element"]]
        else:
            useful = [least, "balance"]
        return {"useful": useful, "harmful": ["excess_" + max(counts, key=counts.get)], "basis": "pattern + support/suppress + seasonal balance"}

    @staticmethod
    def _luck_cycles(year: int, day_master: str) -> List[Dict[str, Any]]:
        start_age = 3 + (STEMS.index(day_master) % 6)
        return [{"age_range": f"{start_age + i*10}-{start_age + i*10 + 9}", "pillar": f"{STEMS[(i+2)%10]}{BRANCHES[(i+3)%12]}", "calendar_years": f"{year + start_age + i*10}-{year + start_age + i*10 + 9}"} for i in range(8)]
