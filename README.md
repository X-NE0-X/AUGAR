# AUGAR

**Ask Universe, Get A Reading.**

AUGAR is a multi-oracle market cycle reading engine.  Six oracle engines
(Tarot, Wenwang Liuyao, Zi Ping BaZi, Ziwei Doushu, Astrology Cycle, Market
Pulse) read market index data and produce structured interpretative cards
powered by an LLM interpreter.

## Quick Start

```powershell
pip install -e .
augar serve
```

Open http://127.0.0.1:8765 — frontend + API, ready to browse.

## CLI

```
augar                    # start the full application
augar serve              # same as above
augar generate ...       # generate oracle cards
augar check ...          # check LLM provider connectivity
augar build              # rebuild the frontend static assets
```

### Generate Cards

```powershell
augar generate --period 2026-04-M --all-indexes --provider mock
augar generate --period 2026-04-M --symbols SPX --provider openai --model gpt-5.5
augar generate --period 2026-04-M --symbols SPX --provider deepseek --model deepseek-chat
augar generate --period 2026-04-M --symbols SPX --engines tarot --provider history --history-run-id 9e3792908386 --force
augar generate --config configs\augar.chatgpt_oauth.example.json
```

`mock` reuses real LLM history when available, falling back to deterministic
fixtures.  `--force` (or `--force tarot,wenwang`) regenerates selected engines.

### Dev / Manual Backend

```powershell
python -m uvicorn augar_engine.api.app:app --host 127.0.0.1 --port 8765
```

## Read Existing Output

```powershell
Get-Content public\data\readings\2026-04-M\SPX.json -Encoding UTF8
Get-Content public\data\cards\2026-04-M\SPX\tarot.json -Encoding UTF8
```

From Python:

```python
import json, pathlib
reading = json.loads(pathlib.Path("public/data/readings/2026-04-M/SPX.json").read_text("utf-8"))
print(reading["composite"])
```

## Validation

```powershell
python -m pytest -q
```
