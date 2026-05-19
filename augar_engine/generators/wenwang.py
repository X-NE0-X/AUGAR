from __future__ import annotations

from typing import Any, Dict, List

from ..schemas import AssetRef, PeriodRef
from .base import BaseGenerator

TRIGRAMS = {
    (1, 1, 1): ("Qian", "Heaven", "Metal"),
    (0, 0, 0): ("Kun", "Earth", "Earth"),
    (0, 1, 0): ("Kan", "Water", "Water"),
    (1, 0, 1): ("Li", "Fire", "Fire"),
    (1, 0, 0): ("Zhen", "Thunder", "Wood"),
    (0, 0, 1): ("Gen", "Mountain", "Earth"),
    (1, 1, 0): ("Dui", "Lake", "Metal"),
    (0, 1, 1): ("Xun", "Wind", "Wood"),
}
SIX_RELATIVES = ("Parents", "Siblings", "Offspring", "Wealth", "Officer", "Self")
SIX_SPIRITS = ("Azure Dragon", "Vermilion Bird", "Hook Snake", "White Tiger", "Black Tortoise", "Flying Serpent")
BRANCHES = ("Zi", "Chou", "Yin", "Mao", "Chen", "Si", "Wu", "Wei", "Shen", "You", "Xu", "Hai")


class WenwangGenerator(BaseGenerator):
    engine_id = "wenwang"

    def generate(self, asset: AssetRef, period: PeriodRef, market_context: Dict[str, Any], seed: int | None = None) -> Dict[str, Any]:
        rng = self.rng(asset, period, seed)
        tosses: List[Dict[str, Any]] = []
        line_values: List[int] = []
        primary_bits: List[int] = []
        changed_bits: List[int] = []
        moving_lines: List[int] = []

        for idx in range(1, 7):
            coins = [rng.choice([2, 3]) for _ in range(3)]
            value = sum(coins)
            moving = value in (6, 9)
            yin_yang = 1 if value in (7, 9) else 0
            changed = 1 - yin_yang if moving else yin_yang
            tosses.append({"line": idx, "coins": coins, "value": value, "moving": moving})
            line_values.append(value)
            primary_bits.append(yin_yang)
            changed_bits.append(changed)
            if moving:
                moving_lines.append(idx)

        lower = tuple(primary_bits[:3])
        upper = tuple(primary_bits[3:])
        changed_lower = tuple(changed_bits[:3])
        changed_upper = tuple(changed_bits[3:])
        lower_name, lower_symbol, lower_element = TRIGRAMS[lower]
        upper_name, upper_symbol, upper_element = TRIGRAMS[upper]
        changed_lower_name, changed_lower_symbol, _ = TRIGRAMS[changed_lower]
        changed_upper_name, changed_upper_symbol, _ = TRIGRAMS[changed_upper]
        palace = upper_name if upper_name == lower_name else f"{upper_name} Palace"

        installed_lines = []
        for idx, bit in enumerate(primary_bits, start=1):
            installed_lines.append({
                "line": idx,
                "yin_yang": "yang" if bit else "yin",
                "value": line_values[idx - 1],
                "moving": idx in moving_lines,
                "earthly_branch": BRANCHES[(idx + len(asset.ticker)) % 12],
                "six_relative": SIX_RELATIVES[(idx + len(period.id)) % 6],
                "six_spirit": SIX_SPIRITS[(idx + line_values[idx - 1]) % 6],
                "role": "self" if idx == 3 else ("response" if idx == 6 else "supporting"),
            })

        artifact = self.base_artifact(asset, period, market_context, seed)
        artifact.update({
            "sop": "Wenwang Liuyao NaJia: six coin tosses, primary/changed hexagram, palace, self/response, NaJia labels before interpretation",
            "question": f"{asset.ticker} market tendency during {period.label}",
            "tosses_bottom_to_top": tosses,
            "line_values_bottom_to_top": line_values,
            "moving_lines": moving_lines,
            "primary_hexagram": {
                "upper_trigram": upper_name,
                "lower_trigram": lower_name,
                "image": f"{upper_symbol} over {lower_symbol}",
                "palace": palace,
                "element_frame": [upper_element, lower_element],
            },
            "changed_hexagram": {
                "upper_trigram": changed_upper_name,
                "lower_trigram": changed_lower_name,
                "image": f"{changed_upper_symbol} over {changed_lower_symbol}",
            },
            "installed_lines": installed_lines,
            "month_branch": BRANCHES[(int(period.id[5:7]) + 1) % 12],
            "day_branch": BRANCHES[self.rng(asset, period, seed).randrange(12)],
            "xun_kong": [BRANCHES[(len(asset.ticker) + 2) % 12], BRANCHES[(len(asset.ticker) + 3) % 12]],
            "useful_god": {
                "main": "Wealth",
                "reason": "market price/return question defaults to Wealth; Officer is pressure/risk reference",
            },
            "tags": [market_context.get("momentum_label"), market_context.get("volatility_label")],
        })
        return artifact
