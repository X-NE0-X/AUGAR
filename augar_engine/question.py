from __future__ import annotations

import json
import os
import re
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .constants import DEFAULT_OUTPUT_ROOT, PROJECT_ROOT, SCHEMA_VERSION
from .core import now_period, scrub_secrets
from .display import build_composite
from .exports import write_json
from .generators import GENERATOR_BY_ENGINE
from .interpreter import build_card
from .llm import LLMClient, LLMParams
from .schemas import AssetRef, PeriodRef, ReadingBundle

QUESTION_ENGINES = ("tarot", "wenwang", "bazi", "ziwei", "astrology")
PINYIN_MAP = {
    "今": "jin", "天": "tian", "明": "ming", "年": "nian", "月": "yue", "日": "ri",
    "会": "hui", "不": "bu", "能": "neng", "可": "ke", "否": "fou", "是": "shi", "吗": "ma",
    "我": "wo", "他": "ta", "她": "ta", "们": "men", "这": "zhe", "个": "ge",
    "事": "shi", "情": "qing", "问": "wen", "题": "ti", "结": "jie", "果": "guo",
    "成": "cheng", "功": "gong", "失": "shi", "败": "bai", "好": "hao", "坏": "huai",
    "涨": "zhang", "跌": "die", "买": "mai", "卖": "mai", "投": "tou", "资": "zi",
    "市": "shi", "场": "chang", "股": "gu", "票": "piao", "指": "zhi", "数": "shu",
    "爱": "ai", "感": "gan", "婚": "hun", "姻": "yin", "工": "gong", "作": "zuo",
    "项": "xiang", "目": "mu", "合": "he", "适": "shi", "机": "ji", "行": "xing", "测": "ce", "试": "shi",
    "去": "qu", "留": "liu", "开": "kai", "始": "shi", "继": "ji", "续": "xu",
    "选": "xuan", "择": "ze", "方": "fang", "向": "xiang", "签": "qian", "约": "yue",
    "通": "tong", "过": "guo", "需": "xu", "要": "yao", "应": "ying", "该": "gai",
}

PINYIN_MAP.update({
    "\u91d1": "jin",
    "\u70bc": "lian",
    "\u4e39": "dan",
    "\u878d": "rong",
    "\u65f6": "shi",
    "\u5e8f": "xu",
})


def load_dotenv(path: Path = PROJECT_ROOT / ".env") -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def slug_title(title: str) -> str:
    parts: list[str] = []
    for char in title.strip():
        if char.isascii() and re.match(r"[A-Za-z0-9._-]", char):
            parts.append(char.lower())
        elif "\u4e00" <= char <= "\u9fff":
            parts.append(PINYIN_MAP.get(char, f"u{ord(char):x}"))
        elif char.isspace() or char in "/\\|:;，。！？、,.!?()[]{}":
            parts.append("-")
    text = re.sub(r"-+", "-", "-".join([p for p in parts if p])).strip("-")
    return (text or "question")[:64].upper()


def question_identifier() -> str:
    return f"Q-{uuid.uuid4().hex[:10].upper()}"


def dummy_context(ticker: str) -> dict[str, Any]:
    return {
        "ticker": ticker,
        "region": "QUESTION",
        "asset_class": "QUESTION",
        "data_start": "2000-01-01",
        "data_end": "2000-01-01",
        "observations": 1,
        "latest_close": 1.0,
        "return_21d": 0.0,
        "return_63d": 0.0,
        "volatility_63d": 0.0,
        "drawdown_252d": 0.0,
        "momentum_label": "question_field",
        "volatility_label": "normal",
        "drawdown_label": "none",
    }


def ask_question(
    *,
    title: str,
    question: str,
    provider: str = "deepseek",
    model: str = "deepseek-v4-flash",
    output_root: Path = DEFAULT_OUTPUT_ROOT,
) -> dict[str, Any]:
    if not title.strip():
        raise ValueError("title is required")
    if not question.strip():
        raise ValueError("question is required")

    load_dotenv()
    period = now_period()
    ticker = question_identifier()
    asset = AssetRef(ticker=ticker, name=title.strip(), region="QUESTION", asset_class="QUESTION")
    market_context = dummy_context(ticker)
    llm = LLMClient(LLMParams(
        provider=provider,
        model=model,
        reasoning_effort=None if provider == "deepseek" else "low",
        api_key=os.getenv("DEEPSEEK_API_KEY") or os.getenv("AUGAR_LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or None,
    ))

    cards = []
    seed = uuid.uuid4().int % 1_000_000
    for engine_id in QUESTION_ENGINES:
        raw = GENERATOR_BY_ENGINE[engine_id]().generate(asset, period, dict(market_context), seed=seed)
        raw["user_question"] = {
            "title": title.strip(),
            "question": question.strip(),
            "instruction": "Answer the user's question directly through this metaphysical engine. The question can be about anything; do not force it into market language.",
        }
        if "question" in raw:
            raw["engine_question"] = raw["question"]
        raw["question"] = question.strip()
        card = build_card(
            engine_id=engine_id,
            asset=asset,
            period=period,
            raw_artifact=raw,
            llm=llm,
            include_market_context=True,
            allow_error_card=False,
        )
        cards.append(card)
        write_json(
            output_root / "questions" / "cards" / period.id / ticker / f"{engine_id}.json",
            card.to_dict(include_raw_artifact=True, include_market_context=True),
        )

    bundle = ReadingBundle(
        schema_version=SCHEMA_VERSION,
        asset=asset,
        period=period,
        composite=build_composite(cards),
        cards=cards,
        run_id=uuid.uuid4().hex[:10],
        generation_params=scrub_secrets({
            "kind": "free_question",
            "title": title.strip(),
            "question": question.strip(),
            "provider": provider,
            "model": model,
            "engines": list(QUESTION_ENGINES),
        }),
    )
    bundle_payload = bundle.to_dict(include_raw_artifact=True, include_market_context=True, include_generation_params=True)
    write_json(output_root / "questions" / "readings" / period.id / ticker / "index.json", bundle_payload)
    write_json(output_root / "questions" / "readings" / period.id / f"{ticker}.json", bundle_payload)
    record = {
        "title": title.strip(),
        "ticker": ticker,
        "period": period.id,
        "question": question.strip(),
        "created_at": period.id,
        "score": bundle.composite.score,
        "polarity": bundle.composite.polarity,
        "href": f"/questions/{period.id}/{ticker}",
    }
    index_path = output_root / "questions" / "index.json"
    records: list[dict[str, Any]] = []
    if index_path.exists():
        try:
            records = json.loads(index_path.read_text(encoding="utf-8")).get("records", [])
        except Exception:
            records = []
    records = [record] + [item for item in records if not (item.get("period") == period.id and item.get("ticker") == ticker)]
    write_json(index_path, {"schema_version": "0.1", "records": records[:200]})
    return {"record": record, "bundle": bundle_payload}
