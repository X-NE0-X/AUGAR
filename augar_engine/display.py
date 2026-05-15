from __future__ import annotations

from collections import Counter
from statistics import mean
from typing import List

from .schemas import OracleCard, ReadingComposite


def build_composite(cards: List[OracleCard]) -> ReadingComposite:
    if not cards:
        return ReadingComposite(50, "neutral", "low", [], "No oracle cards were generated")

    score = int(round(mean(card.result.score for card in cards)))
    polarities = Counter(card.result.polarity for card in cards)
    intensities = Counter(card.result.intensity for card in cards)
    symbol_counts = Counter(symbol for card in cards for symbol in card.symbols)
    polarity = polarities.most_common(1)[0][0]
    intensity = "high" if score >= 65 or score <= 35 else intensities.most_common(1)[0][0]
    dominant_symbols = [symbol for symbol, _ in symbol_counts.most_common(6)]
    headline = f"The oracles lean {polarity} with {intensity} intensity"
    return ReadingComposite(score, polarity, intensity, dominant_symbols, headline)
