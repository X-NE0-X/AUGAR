# A.U.G.A.R.
**Ask Universe, Get A Reading.**


## The Six-Dimension Divination Market Reading Engine
***"When the charts offer no answers, perhaps the stars do."***

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![License: WTFPL](https://img.shields.io/badge/License-WTFPL-brightgreen.svg)](http://www.wtfpl.net/about/)
[![Build Status](https://img.shields.io/badge/accuracy-consult%20your%20horoscope-red)]()
[![Coverage](https://img.shields.io/badge/woo--woo%20coverage-500%25-purple)]()
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)]()

> 中文版本：[README.zh.md](README.zh.md)


## What Is This
AUGAR is a multi-oracle market cycle reading system built on BaZi, Liuyao, Ziwei Doushu, Western astrology, Tarot, and quantitative market pulse analysis.

It does **not** promise to make you money. It doesn't even promise to outperform a chimpanzee with darts.

The core philosophy: **if markets are unpredictable, then stacking six unpredictable systems together must cancel out the unpredictability, right?**

*(Answer: No.)*


## 🧠 The Six Engines
| Engine | Tradition | Role | Method |
|--------|-----------|------|--------|
| **🔴 BaZi** | Four Pillars | Macro tenor | `Day Master` × `Ten Gods` × `Five Elements` |
| **🟣 Ziwei** | Purple Star | Sentiment & capital flow | `Annual Transformations` × 12 Palaces |
| **🟢 Wenwang** | I Ching | Inflection signals | `Three-coin Toss` → `Moving Lines` |
| **🔵 Astrology** | Western | Global risk | `Planetary aspects` → `Exaltation`/`Fall` |
| **🟡 Tarot** | Rider-Waite | Cycle narrative | `Celtic Cross` (10 cards) |
| **⚪ Market Pulse** | Quantitative | Reality check | `Momentum` · `Volatility` · `Drawdown` |

Six cards displayed side by side. Composite score is arithmetic mean + modal polarity — purely programmatic, no LLM judge.


## 🎲 Actual Features

### 1. Code-Generated Oracles
Every engine's Program Generator (`generators/`) is pure Python — no LLM involved. Tarot shuffles via RNG and draws ten cards. Liuyao tosses three coins six times. BaZi derives four pillars from listing dates. The LLM only handles interpretation.

### 2. Bilingual Output
LLM interprets in Chinese. Backend auto-translates to English via `translators` (Google primary, Bing fallback). Each card stores `result` (Chinese) + `result_en` (English). Frontend switches by language.

### 3. Multi-Provider Support
Same pipeline: DeepSeek, OpenAI, ChatGPT OAuth (local Codex CLI), any OpenAI-compatible endpoint. Keys via `--api-key` or `.env`.

### 4. Static JSON Deployment
All output lands as JSON in `public/data/`. Frontend is pure static — deploy to Vercel or Cloudflare Pages. No runtime database. No live LLM calls.


## 🚀 Quick Start

```bash
git clone https://github.com/X-NE0-X/AUGAR.git
cd AUGAR
pip install -e .

# Start the full app
augar serve
# Open http://127.0.0.1:8765

# Generate readings
$env:DEEPSEEK_API_KEY = "sk-xxx"
augar generate --all-indexes --provider deepseek --model deepseek-v4-flash

augar generate --symbols SPX --provider openai --model gpt-5.5

augar --help
```

Copy `.env.example` → `.env`, fill in your keys. `augar` loads `.env` on startup.


## 🏗️ Architecture
```
CLI (augar generate / serve)         Web Frontend (React + Vite)
            │                                    │
            └────────── FastAPI (:8765) ─────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   Market Loader       6× Generators        LLM Interpreter
   (4× Parquet)        (pure Python)        (OpenAI / DeepSeek
   CN/HK/UK/US         tarot, wenwang        / ChatGPT OAuth)
                        bazi, ziwei               │
                        astrology,          CN prompt → CN
                        market_pulse        → translators → EN
        │                    │                    │
        └──────────────── JSON Export ───────────┘
                public/data/cards/{period}/{ticker}/{engine}.json
                public/data/readings/{period}/{ticker}.json
```

Card-drawing, hexagram-casting, and chart-plotting are pure code. The LLM only interprets, producing standardized OracleCard JSON.


## 📦 Project Structure
```
AUGAR/
  augar_engine/           ← Python libs
    api/app.py            ← FastAPI backend
    cli.py                ← generate commands
    entry.py              ← augar entrance（serve/build/check/generate）
    pipeline.py           ← pipeline
    interpreter.py        ← LLM + translation
    llm.py                ← LLM APIs (OpenAI/DeepSeek/ChatGPT OAuth)
    generators/           ← Coded generators
    exports.py            ← JSON exports
    schemas.py            ← OracleCard / ReadingBundle
    constants.py          ← configs/defaults.json
  configs/
    defaults.json         ← LLM Configs
    llm.json              ← LLM Provider defaults
    market_thresholds.json ← Something finance
  public/data/            ← Cards and readings（JSON）
  frontend/               ← React + TypeScript + Vite
    src/views/            ← Ask / Readings / Almanac / Methodology
  data/                   ← Parquet market data (CN/HK/UK/US)
```


## 📄 Standard Output Format
```json
{
  "schema_version": "0.1",
  "asset": { "ticker": "SPX", "name": "SPX", "region": "US" },
  "engine": { "id": "tarot", "name": "Tarot Celtic Cross", "display_name": "塔罗" },
  "result": {
    "score": 72, "polarity": "positive", "intensity": "moderate",
    "headline": "Turning of the Wheel: From Conflict to Stability",
    "subline": "...", "short_reading": "...", "long_reading": "..."
  },
  "result_en": { "headline": "...", "..." : "..." },
  "symbols": ["Nine of Swords reversed", "Seven of Cups", "..."],
  "risk_tags": ["volatility", "mixed_momentum"]
}
```

Bilingual storage (`result` + `result_en`). Frontend picks by language.


## 🔌 Supported Providers
| Provider | Auth | Model |
|----------|------|-------|
| `deepseek` | `DEEPSEEK_API_KEY` | v4-flash / v4-pro |
| `openai` | `OPENAI_API_KEY` | gpt-5.5 |
| `chatgpt_oauth` | Codex CLI OAuth | gpt-5.5 (no key needed) |
| `openai_compatible` | `OPENAI_API_KEY` | Any compatible endpoint |
| `local` | None | vllm / ollama |


## 📄 License
**[WTFPL](http://www.wtfpl.net/about/) —— Do What The Fuck You Want To Public License**

Actually it's **MIT**.


## ⚠️ Disclaimer
Entertainment purposes only. Not investment advice.

- If you profit from a reading, that's fate.
- If you lose, maybe you cloned it wrong.
- The author accepts no responsibility for financial losses or existential crises.


## 🙏 Acknowledgments
This project is deeply inspired by the [**CITIC CLSA Feng Shui Index**](https://www.clsa.com/special/FSI/2026/).

For years, CLSA has been packaging metaphysics in the rigorous format of equity research, proving that finance isn't just cold hard numbers—it also runs on red-hot Five Elements. AUGAR aims to open-source this spirit, crank it into five dimensions, and put a personal feng shui department in everyone's pocket.

Major shout-out to the **CITIC CLSA**.
