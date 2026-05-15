from .astrology import AstrologyGenerator
from .bazi import BaziGenerator
from .market_pulse import MarketPulseGenerator
from .tarot import TarotGenerator
from .wenwang import WenwangGenerator
from .ziwei import ZiweiGenerator

GENERATOR_BY_ENGINE = {
    "tarot": TarotGenerator,
    "wenwang": WenwangGenerator,
    "bazi": BaziGenerator,
    "ziwei": ZiweiGenerator,
    "astrology": AstrologyGenerator,
    "market_pulse": MarketPulseGenerator,
}

__all__ = ["GENERATOR_BY_ENGINE"]
