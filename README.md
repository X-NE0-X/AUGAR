# AUGAR

**Ask Universe, Get A Reading.**

AUGAR is a backend-only multi-oracle card generation pipeline. It reads local index Parquet data, generates engine-specific raw artifacts, asks an LLM interpreter for each engine, and exports static JSON readings.

## Generate

Mock provider, full index universe:

```powershell
python AUGAR.py --period 2026-04-M --all-indexes --provider mock
```

By default, existing cards are reused to avoid unnecessary LLM cost. Regenerate everything or one engine with:

```powershell
python AUGAR.py --period 2026-04-M --all-indexes --provider mock --force
python AUGAR.py --period 2026-04-M --all-indexes --provider mock --force tarot
```

ChatGPT OAuth through Codex CLI:

```powershell
python AUGAR.py --period 2026-04-M --symbols SPX --engines tarot,wenwang,bazi,ziwei,astrology,market_pulse --provider chatgpt_oauth --model gpt-5.5 --reasoning-effort low --timeout 240
```

Config-file run:

```powershell
python AUGAR.py --config configs\augar.chatgpt_oauth.example.json
```

OpenAI API or OpenAI-compatible providers:

```powershell
python AUGAR.py --period 2026-04-M --symbols SPX --provider openai --model gpt-5.5 --reasoning-effort low
python AUGAR.py --period 2026-04-M --symbols SPX --provider openai_compatible --base-url http://localhost:8000/v1 --model local-model
```

## Read Existing Output

Existing generated content is under `public/data`; reading it does not rerun generation.

Read the run index:

```powershell
Get-Content public\data\index.json -Encoding UTF8
```

Read one asset bundle:

```powershell
Get-Content public\data\readings\2026-04-M\SPX.json -Encoding UTF8
```

Read one engine card:

```powershell
Get-Content public\data\cards\2026-04-M\SPX\tarot.json -Encoding UTF8
```

From Python:

```python
import json
from pathlib import Path

reading = json.loads(Path("public/data/readings/2026-04-M/SPX.json").read_text(encoding="utf-8"))
print(reading["composite"])
```

FastAPI read endpoints:

```powershell
python -m uvicorn augar_engine.api.app:app --host 127.0.0.1 --port 8765
```

Then open:

```text
http://127.0.0.1:8765/readings/2026-04-M/SPX
http://127.0.0.1:8765/cards/2026-04-M/SPX/tarot
```

Public artifacts are intentionally slim: they include asset, period, composite, card result, symbols, risk tags, visual, and `raw_ref`. Full raw artifacts, market context, and generation params are kept under `runs/<run_id>/debug`.

## Validation

```powershell
python -m py_compile (Get-ChildItem -Recurse -Filter *.py | ForEach-Object { $_.FullName })
python -m pytest -q
```
