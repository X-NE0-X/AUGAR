from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import pandas as pd

from ..constants import DEFAULT_PARQUET_FILES, MARKET_THRESHOLDS, PROJECT_ROOT, REGION_BY_FILE


@dataclass
class MarketContext:
    ticker: str
    region: str
    asset_class: str
    data_start: str
    data_end: str
    observations: int
    latest_close: float
    return_21d: float
    return_63d: float
    volatility_63d: float
    drawdown_252d: float
    momentum_label: str
    volatility_label: str
    drawdown_label: str

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


class DataProcessing:
    """AUGAR-native market data loader derived from BabyAubergine parquet semantics."""

    REQUIRED_COLUMNS = ("Datetime", "Symbol", "Open", "High", "Low", "Close")

    def __init__(self, root: Path | str = PROJECT_ROOT, parquet_files: Optional[Iterable[str | Path]] = None) -> None:
        self.root = Path(root)
        self.parquet_files = [Path(p) for p in (parquet_files or DEFAULT_PARQUET_FILES)]
        self._data: Optional[pd.DataFrame] = None

    def load(self) -> pd.DataFrame:
        frames: List[pd.DataFrame] = []
        for raw_path in self.parquet_files:
            path = raw_path if raw_path.is_absolute() else self.root / raw_path
            if not path.exists():
                raise FileNotFoundError(f"Parquet source missing: {path}")
            df = pd.read_parquet(path)
            missing = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
            if missing:
                raise KeyError(f"{path.name} missing required columns: {missing}")
            keep_cols = [col for col in df.columns if col in {
                "Datetime", "Symbol", "Open", "High", "Low", "Close", "Volume", "Vwap", "Source"
            }]
            df = df.loc[:, keep_cols].copy()
            df["Datetime"] = pd.to_datetime(df["Datetime"], errors="coerce").dt.tz_localize(None)
            df = df.dropna(subset=["Datetime", "Symbol", "Close"])
            df["Symbol"] = df["Symbol"].astype(str).str.strip().str.upper()
            df["Region"] = REGION_BY_FILE.get(path.name, "")
            frames.append(df)

        data = pd.concat(frames, ignore_index=True)
        data = data.drop_duplicates(subset=["Symbol", "Datetime"], keep="last")
        data = data.sort_values(["Symbol", "Datetime"]).reset_index(drop=True)
        self._data = data
        return data

    @property
    def data(self) -> pd.DataFrame:
        if self._data is None:
            return self.load()
        return self._data

    def discover_symbols(self) -> List[str]:
        return sorted(self.data["Symbol"].dropna().astype(str).unique().tolist())

    def region_for(self, symbol: str) -> str:
        rows = self.data.loc[self.data["Symbol"].eq(symbol.upper()), "Region"]
        return str(rows.iloc[-1]) if not rows.empty else ""

    def frame_for(self, symbol: str) -> pd.DataFrame:
        ticker = symbol.upper()
        df = self.data.loc[self.data["Symbol"].eq(ticker)].copy()
        if df.empty:
            raise ValueError(f"No market data for symbol: {ticker}")
        return df.sort_values("Datetime").reset_index(drop=True)

    def context_for(self, symbol: str) -> MarketContext:
        df = self.frame_for(symbol)
        closes = pd.to_numeric(df["Close"], errors="coerce").dropna()
        if len(closes) < 2:
            raise ValueError(f"Not enough close data for symbol: {symbol}")

        returns = closes.pct_change().dropna()
        latest = float(closes.iloc[-1])
        ret_21 = self._window_return(closes, 21)
        ret_63 = self._window_return(closes, 63)
        vol_63 = float(returns.tail(63).std() * (252 ** 0.5)) if not returns.empty else 0.0
        tail_252 = closes.tail(252)
        rolling_high = float(tail_252.max()) if not tail_252.empty else latest
        drawdown = float((latest / rolling_high) - 1.0) if rolling_high else 0.0

        return MarketContext(
            ticker=symbol.upper(),
            region=self.region_for(symbol),
            asset_class="INDEX",
            data_start=str(df["Datetime"].min().date()),
            data_end=str(df["Datetime"].max().date()),
            observations=int(len(df)),
            latest_close=latest,
            return_21d=ret_21,
            return_63d=ret_63,
            volatility_63d=vol_63,
            drawdown_252d=drawdown,
            momentum_label=self._momentum_label(ret_21, ret_63),
            volatility_label=self._volatility_label(vol_63),
            drawdown_label=self._drawdown_label(drawdown),
        )

    @staticmethod
    def _window_return(closes: pd.Series, window: int) -> float:
        if len(closes) <= window:
            return float((closes.iloc[-1] / closes.iloc[0]) - 1.0)
        return float((closes.iloc[-1] / closes.iloc[-window - 1]) - 1.0)

    @staticmethod
    def _momentum_label(ret_21: float, ret_63: float) -> str:
        mt = MARKET_THRESHOLDS["momentum"]
        su = mt["strong_uptrend"]
        if ret_21 > su["ret_21_min"] and ret_63 > su["ret_63_min"]:
            return "strong_uptrend"
        ri = mt["rising"]
        if ret_21 > ri["ret_21_min"] and ret_63 > ri["ret_63_min"]:
            return "rising"
        sd = mt["strong_downtrend"]
        if ret_21 < sd["ret_21_max"] and ret_63 < sd["ret_63_max"]:
            return "strong_downtrend"
        fa = mt["falling"]
        if ret_21 < fa["ret_21_max"] and ret_63 < fa["ret_63_max"]:
            return "falling"
        return "mixed"

    @staticmethod
    def _volatility_label(volatility: float) -> str:
        vt = MARKET_THRESHOLDS["volatility"]
        if volatility >= vt["extreme"]:
            return "extreme"
        if volatility >= vt["elevated"]:
            return "elevated"
        if volatility >= vt["normal"]:
            return "normal"
        return "quiet"

    @staticmethod
    def _drawdown_label(drawdown: float) -> str:
        dt = MARKET_THRESHOLDS["drawdown"]
        if drawdown <= dt["deep"]:
            return "deep"
        if drawdown <= dt["material"]:
            return "material"
        if drawdown <= dt["shallow"]:
            return "shallow"
        return "near_high"
