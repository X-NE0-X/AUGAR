from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from .constants import DEFAULT_OUTPUT_ROOT, PROJECT_ROOT
from .data import DataProcessing
from .exports import write_json
from .generators import GENERATOR_BY_ENGINE
from .schemas import AssetRef, PeriodRef


MONTH_ZODIACS = [
    "Ox", "Tiger", "Rabbit", "Dragon", "Snake", "Horse", "Goat",
    "Monkey", "Rooster", "Dog", "Pig", "Rat", "Ox",
]


@dataclass
class PriceFeature:
    as_of: str
    close: float
    return_21d: float
    return_63d: float
    return_126d: float
    return_252d: float
    volatility_63d: float
    drawdown_252d: float


def load_dotenv(path: Path = PROJECT_ROOT / ".env") -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text or text.startswith("#") or "=" not in text:
            continue
        key, value = text.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def fetch_clsa_year(year: int) -> dict[str, Any]:
    file_name = "fsichart_cn.js" if year >= 2026 else "fsichart-cn.js"
    url = f"https://www.clsa.com/special/FSI/{year}/js/{file_name}"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    text = response.content.decode("utf-8", errors="replace")
    match = re.search(r"chart\.data\s*=\s*\[(.*?)\];", text, flags=re.S)
    if not match:
        raise ValueError(f"Could not find chart.data in {url}")
    objects = re.findall(r"\{(.*?)\}", match.group(1), flags=re.S)
    points: list[dict[str, Any]] = []
    for index, body in enumerate(objects):
        month = _extract_js_string(body, "month")
        raw_index = _extract_js_number(body, "index")
        start, end = parse_clsa_month_range(year, index, month)
        points.append({
            "ordinal": index,
            "label": month,
            "zodiac": MONTH_ZODIACS[index] if index < len(MONTH_ZODIACS) else "",
            "start": start,
            "end": end,
            "clsa_index": raw_index,
            "source_url": url,
        })
    return {
        "year": year,
        "source_url": f"https://www.clsa.com/special/FSI/{year}/cn/?section=feng-shui-index",
        "chart_js_url": url,
        "points": points,
    }


def parse_clsa_month_range(year: int, ordinal: int, label: str) -> tuple[str, str]:
    nums = [int(x) for x in re.findall(r"(\d+)", label)]
    if len(nums) < 4:
        raise ValueError(f"Unexpected CLSA month label for {year}: {label}")
    start_month, start_day, end_month, end_day = nums[:4]
    start_year = year if ordinal == 0 or start_month >= 2 else year + 1
    end_year = start_year + 1 if end_month < start_month else start_year
    return f"{start_year:04d}-{start_month:02d}-{start_day:02d}", f"{end_year:04d}-{end_month:02d}-{end_day:02d}"


def _extract_js_string(body: str, key: str) -> str:
    match = re.search(rf'"{re.escape(key)}"\s*:\s*"([^"]*)"', body)
    if not match:
        raise ValueError(f"Missing JS string field: {key}")
    return match.group(1)


def _extract_js_number(body: str, key: str) -> float:
    match = re.search(rf'"{re.escape(key)}"\s*:\s*(-?\d+(?:\.\d+)?)', body)
    if not match:
        raise ValueError(f"Missing JS number field: {key}")
    value = float(match.group(1))
    return int(value) if value.is_integer() else value


def nearest_close(df: pd.DataFrame, date_text: str) -> dict[str, Any] | None:
    target = pd.Timestamp(date_text)
    if target > df["Datetime"].max():
        return None
    rows = df.loc[df["Datetime"].le(target)]
    if rows.empty:
        return None
    row = rows.iloc[-1]
    return {"date": str(row["Datetime"].date()), "close": float(row["Close"])}


def price_features(df: pd.DataFrame, as_of: str) -> PriceFeature:
    target = pd.Timestamp(as_of)
    hist = df.loc[df["Datetime"].le(target)].copy()
    if len(hist) < 253:
        raise ValueError(f"Not enough price history as of {as_of}")
    closes = pd.to_numeric(hist["Close"], errors="coerce").dropna()
    returns = closes.pct_change().dropna()
    latest = float(closes.iloc[-1])
    tail_252 = closes.tail(252)
    rolling_high = float(tail_252.max())
    return PriceFeature(
        as_of=str(hist["Datetime"].iloc[-1].date()),
        close=latest,
        return_21d=_window_return(closes, 21),
        return_63d=_window_return(closes, 63),
        return_126d=_window_return(closes, 126),
        return_252d=_window_return(closes, 252),
        volatility_63d=float(returns.tail(63).std() * (252 ** 0.5)),
        drawdown_252d=float((latest / rolling_high) - 1.0) if rolling_high else 0.0,
    )


def _window_return(closes: pd.Series, window: int) -> float:
    return float((closes.iloc[-1] / closes.iloc[-window - 1]) - 1.0)


def build_period_raw_artifacts(year: int, symbol: str, features: PriceFeature, point: dict[str, Any]) -> dict[str, Any]:
    asset = AssetRef(ticker=symbol, name=symbol, region="HK")
    period = PeriodRef(
        id=f"{point['start']}-0000",
        label=f"{point['start']} to {point['end']} forecast as of {features.as_of}",
        freq="monthly",
    )
    market_context = {
        "ticker": symbol,
        "region": "HK",
        "asset_class": "INDEX",
        "data_start": "1986-12-31",
        "data_end": features.as_of,
        "observations": 0,
        "latest_close": features.close,
        "return_21d": features.return_21d,
        "return_63d": features.return_63d,
        "return_126d": features.return_126d,
        "return_252d": features.return_252d,
        "volatility_63d": features.volatility_63d,
        "drawdown_252d": features.drawdown_252d,
        "momentum_label": _momentum_label(features.return_21d, features.return_63d),
        "volatility_label": _volatility_label(features.volatility_63d),
        "drawdown_label": _drawdown_label(features.drawdown_252d),
    }
    artifacts = []
    for engine_id in ("tarot", "wenwang", "bazi", "ziwei", "astrology", "market_pulse"):
        raw = GENERATOR_BY_ENGINE[engine_id]().generate(asset, period, dict(market_context), seed=year * 100 + int(point["ordinal"]))
        raw["comparison_task"] = {
            "kind": "historical_year_start_forecast",
            "instruction": "Interpret this engine as one input to this future monthly Hang Seng forecast. Use only information available as of the as_of date.",
            "year": year,
            "as_of": features.as_of,
            "target_period": {"start": point["start"], "end": point["end"], "label": point["label"]},
        }
        artifacts.append(raw)
    return {
        "ordinal": point["ordinal"],
        "start": point["start"],
        "end": point["end"],
        "label": point["label"],
        "artifacts": artifacts,
    }


def deepseek_year_composites(year: int, symbol: str, features: PriceFeature, periods: list[dict[str, Any]], model: str) -> dict[str, Any]:
    api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("AUGAR_LLM_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY or AUGAR_LLM_API_KEY is required")
    prompt = {
        "task": "Generate AUGAR six-engine monthly composite forecast scores for Hang Seng Index.",
        "year": year,
        "symbol": symbol,
        "as_of": features.as_of,
        "rules": [
            "Use all six engine raw artifacts for each period: tarot, wenwang, bazi, ziwei, astrology, market_pulse.",
            "Return one score per engine, then the arithmetic mean rounded to integer as composite_score.",
            "Score range is 1..99. Higher means more favorable for Hang Seng during that target period.",
            "Do not use future prices. Use only the as_of price features and supplied artifacts.",
            "Return both Chinese and English text fields. Chinese fields must be native Simplified Chinese. English fields must be natural English.",
            "Return strict JSON only.",
        ],
        "price_features": asdict(features),
        "periods": periods,
        "schema": {
            "headline": "string",
            "summary_zh": "string",
            "summary_en": "string",
            "monthly": [
                {
                    "ordinal": "integer",
                    "engine_scores": {"tarot": 50, "wenwang": 50, "bazi": 50, "ziwei": 50, "astrology": 50, "market_pulse": 50},
                    "composite_score": "integer 1..99",
                    "polarity": "bullish|bearish|neutral|volatile",
                    "rationale_zh": "short Simplified Chinese string",
                    "rationale_en": "short English string",
                }
            ],
        },
    }
    response = requests.post(
        "https://api.deepseek.com/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": "You are AUGAR's six-engine composite scoring layer. Output strict JSON only."},
                {"role": "user", "content": json.dumps(prompt, ensure_ascii=False, default=str)},
            ],
            "temperature": 0.25,
            "top_p": 0.9,
            "max_tokens": 6000,
            "thinking": {"type": "disabled"},
        },
        timeout=120,
    )
    response.raise_for_status()
    return json.loads(response.json()["choices"][0]["message"]["content"])


def _annual_bias(scores: list[Any]) -> str:
    nums = [float(score) for score in scores if score is not None]
    if not nums:
        return "neutral"
    avg = sum(nums) / len(nums)
    if avg >= 60:
        return "bullish"
    if avg <= 40:
        return "bearish"
    return "neutral"


def _momentum_label(ret_21: float, ret_63: float) -> str:
    if ret_21 > 0.03 and ret_63 > 0.06:
        return "strong_uptrend"
    if ret_21 > 0 and ret_63 > 0:
        return "rising"
    if ret_21 < -0.03 and ret_63 < -0.06:
        return "strong_downtrend"
    if ret_21 < 0 and ret_63 < 0:
        return "falling"
    return "mixed"


def _volatility_label(volatility: float) -> str:
    if volatility >= 0.35:
        return "extreme"
    if volatility >= 0.25:
        return "elevated"
    if volatility >= 0.15:
        return "normal"
    return "quiet"


def _drawdown_label(drawdown: float) -> str:
    if drawdown <= -0.25:
        return "deep"
    if drawdown <= -0.12:
        return "material"
    if drawdown <= -0.04:
        return "shallow"
    return "near_high"


def normalize_percent(values: list[float | int | None]) -> list[float | None]:
    nums = [float(v) for v in values if v is not None]
    if not nums:
        return [None for _ in values]
    lo = min(nums)
    hi = max(nums)
    if hi == lo:
        return [50.0 if v is not None else None for v in values]
    return [((float(v) - lo) / (hi - lo) * 100.0) if v is not None else None for v in values]


def build_comparison(symbol: str, years: list[int], model: str, output_root: Path) -> dict[str, Any]:
    load_dotenv()
    data = DataProcessing()
    df = data.frame_for(symbol)
    all_years: list[dict[str, Any]] = []
    for year in years:
        clsa = fetch_clsa_year(year)
        as_of = clsa["points"][0]["end"]
        features = price_features(df, as_of)
        raw_periods = [build_period_raw_artifacts(year, symbol, features, point) for point in clsa["points"]]
        year_forecast = deepseek_year_composites(year, symbol, features, raw_periods, model)
        forecast_by_ordinal = {int(item["ordinal"]): item for item in year_forecast.get("monthly", [])}
        base_price = nearest_close(df, clsa["points"][0]["end"])
        base_close = base_price["close"] if base_price else None
        monthly = []
        for point in clsa["points"]:
            forecast = forecast_by_ordinal.get(int(point["ordinal"]), {})
            actual = nearest_close(df, point["end"])
            actual_return = None
            price_index = None
            if actual and base_close:
                actual_return = (actual["close"] / base_close) - 1.0
                price_index = 100.0 * actual["close"] / base_close
            item = dict(point)
            item.update({
                "augar_score": forecast.get("composite_score"),
                "augar_index": forecast.get("composite_score"),
                "augar_rationale": forecast.get("rationale_en", "") or forecast.get("rationale", ""),
                "augar_rationale_zh": forecast.get("rationale_zh", ""),
                "augar_rationale_en": forecast.get("rationale_en", "") or forecast.get("rationale", ""),
                "augar_engine_scores": forecast.get("engine_scores", {}),
                "price_date": actual["date"] if actual else None,
                "price_close": actual["close"] if actual else None,
                "price_index": price_index,
                "actual_return": actual_return,
            })
            monthly.append(item)
        clsa_percent = normalize_percent([row["clsa_index"] for row in monthly])
        augar_percent = normalize_percent([row["augar_index"] for row in monthly])
        price_percent = normalize_percent([row["price_index"] for row in monthly])
        for idx, item in enumerate(monthly):
            item["clsa_percent"] = clsa_percent[idx]
            item["augar_percent"] = augar_percent[idx]
            item["price_percent"] = price_percent[idx]
        all_years.append({
            "year": year,
            "symbol": symbol,
            "source_url": clsa["source_url"],
            "chart_js_url": clsa["chart_js_url"],
            "price_as_of": asdict(features),
            "augar": {
                "model": model,
                "headline": f"{symbol} {year} six-engine monthly composite",
                "summary": year_forecast.get("summary_en", "") or year_forecast.get("summary", "Each AUGAR point is a six-engine composite generated with only year-start price context."),
                "summary_zh": year_forecast.get("summary_zh", ""),
                "summary_en": year_forecast.get("summary_en", "") or year_forecast.get("summary", ""),
                "annual_bias": _annual_bias([row.get("augar_score") for row in monthly]),
                "confidence": "medium",
                "engine_mode": "six_engine_fast_year_batch",
            },
            "monthly": monthly,
        })
    payload = {
        "schema_version": "0.1",
        "title": "AUGAR vs CLSA vs Price",
        "symbol": symbol,
        "generated_at": pd.Timestamp.utcnow().isoformat(),
        "methodology": {
            "clsa": "Raw monthly chart.data index from CLSA Feng Shui Index JS files.",
            "augar": "AUGAR six-engine composite for each future period, generated with HSI history available as of the first CLSA point end date.",
            "price": "Actual HSI close nearest to or before each CLSA period end date; future points are null when local data is unavailable.",
        },
        "years": all_years,
    }
    out = output_root / "comparison" / "hsi_fsi_2020_2026.json"
    write_json(out, payload)
    return payload


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build AUGAR vs CLSA vs price comparison artifact.")
    parser.add_argument("--symbol", default="HSI")
    parser.add_argument("--start-year", type=int, default=2020)
    parser.add_argument("--end-year", type=int, default=2026)
    parser.add_argument("--model", default="deepseek-v4-flash")
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    args = parser.parse_args(argv)
    years = list(range(args.start_year, args.end_year + 1))
    payload = build_comparison(args.symbol.upper(), years, args.model, Path(args.output_root))
    print(json.dumps({
        "symbol": payload["symbol"],
        "years": [item["year"] for item in payload["years"]],
        "output": str(Path(args.output_root) / "comparison" / "hsi_fsi_2020_2026.json"),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
