from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "public" / "data"
DEFAULT_RUNS_ROOT = PROJECT_ROOT / "runs"
DEFAULT_DATA_ROOT = PROJECT_ROOT / "data"

ALL_ENGINES = ("tarot", "wenwang", "bazi", "ziwei", "astrology", "market_pulse")
DEFAULT_PARQUET_FILES = (
    "data/Data_INDEX_CN_D.parquet",
    "data/Data_INDEX_HK_D.parquet",
    "data/Data_INDEX_UK_D.parquet",
    "data/Data_INDEX_US_D.parquet",
)

REGION_BY_FILE = {
    "Data_INDEX_CN_D.parquet": "CN",
    "Data_INDEX_HK_D.parquet": "HK",
    "Data_INDEX_UK_D.parquet": "UK",
    "Data_INDEX_US_D.parquet": "US",
}
