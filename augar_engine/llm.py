from __future__ import annotations

import json
import os
import hashlib
import shutil
import subprocess
import tempfile
from pathlib import Path
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional

import requests

from .constants import PROJECT_ROOT


@dataclass
class LLMParams:
    provider: str = "mock"
    model: str = "gpt-5.5"
    base_url: Optional[str] = None
    temperature: float = 0.4
    top_p: float = 1.0
    max_output_tokens: int = 1200
    reasoning_effort: Optional[str] = "low"
    timeout: int = 90
    max_retries: int = 2
    codex_auth_path: Optional[str] = None
    codex_home: Optional[str] = None
    codex_path: Optional[str] = None
    history_run_id: Optional[str] = None

    def public_dict(self) -> Dict[str, Any]:
        return asdict(self)


class LLMClient:
    def __init__(self, params: LLMParams) -> None:
        self.params = params

    def interpret(self, engine_id: str, raw_artifact: Dict[str, Any]) -> Dict[str, Any]:
        if self.params.provider in {"history", "replay"}:
            return self._history_interpret(engine_id, raw_artifact, allow_mock_history=True)
        if self.params.provider == "mock":
            historical = self._history_interpret(engine_id, raw_artifact, allow_mock_history=False, required=False)
            if historical is not None:
                return historical
            return self._mock_interpret(engine_id, raw_artifact)
        if self.params.provider == "chatgpt_oauth":
            return self._chatgpt_oauth(engine_id, raw_artifact)
        if self.params.provider in {"openai", "openai_compatible", "local", "custom"}:
            return self._openai_compatible(engine_id, raw_artifact)
        raise ValueError(f"Unsupported LLM provider: {self.params.provider}")

    def _history_interpret(
        self,
        engine_id: str,
        raw_artifact: Dict[str, Any],
        *,
        allow_mock_history: bool,
        required: bool = True,
    ) -> Optional[Dict[str, Any]]:
        period_id = str(raw_artifact.get("period", {}).get("id", ""))
        ticker = str(raw_artifact.get("asset", {}).get("ticker", ""))
        candidates = self._history_candidates(period_id, ticker, engine_id, allow_mock_history=allow_mock_history)
        for path in candidates:
            try:
                card = json.loads(path.read_text(encoding="utf-8"))
                result = dict(card.get("result", {}))
                if not result:
                    continue
                result["symbols"] = card.get("symbols", [])
                result["risk_tags"] = card.get("risk_tags", [])
                result["visual"] = card.get("visual", {})
                return result
            except Exception:
                continue
        if required:
            raise FileNotFoundError(f"No historical LLM card found for {period_id}/{ticker}/{engine_id}")
        return None

    def _history_candidates(self, period_id: str, ticker: str, engine_id: str, *, allow_mock_history: bool) -> list[Path]:
        runs_root = PROJECT_ROOT / "runs"
        if not runs_root.exists():
            return []
        manifests = []
        for manifest_path in runs_root.glob("*/manifest.json"):
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if self.params.history_run_id and manifest.get("run_id") != self.params.history_run_id:
                continue
            if manifest.get("period") != period_id:
                continue
            if ticker not in set(manifest.get("symbols", [])):
                continue
            if engine_id not in set(manifest.get("engines", [])):
                continue
            provider = str(manifest.get("request", {}).get("provider", ""))
            if not allow_mock_history and provider in {"mock", "history", "replay"}:
                continue
            card_path = manifest_path.parent / "debug" / "cards" / period_id / ticker / f"{engine_id}.json"
            if not card_path.exists():
                continue
            manifests.append((provider in {"mock", "history", "replay"}, str(manifest.get("generated_at", "")), card_path))
        manifests.sort(key=lambda item: (item[0], item[1]))
        manifests.reverse()
        manifests.sort(key=lambda item: item[0])
        return [item[2] for item in manifests]

    def _mock_interpret(self, engine_id: str, raw_artifact: Dict[str, Any]) -> Dict[str, Any]:
        ctx = raw_artifact.get("market_context", {})
        ret = float(ctx.get("return_63d", 0.0))
        vol = float(ctx.get("volatility_63d", 0.0))
        dd = float(ctx.get("drawdown_252d", 0.0))
        engine_signal = self._mock_engine_signal(engine_id, raw_artifact)
        score = int(max(1, min(99, 50 + ret * 90 - vol * 12 + dd * 18 + engine_signal)))
        polarity = "favorable" if score >= 60 else ("unfavorable" if score <= 42 else "neutral")
        intensity = "high" if abs(score - 50) >= 18 or vol >= 0.25 else ("medium" if abs(score - 50) >= 8 else "low")
        symbols = self._symbols(engine_id, raw_artifact, ctx)
        risks = self._risks(ctx)
        return {
            "score": score,
            "polarity": polarity,
            "intensity": intensity,
            "omen_type": f"{engine_id}_{polarity}_{intensity}",
            "headline": f"{engine_id.replace('_', ' ').title()} reads {ctx.get('ticker', raw_artifact.get('asset', {}).get('ticker', 'asset'))} as {polarity}",
            "subline": f"{symbols[0]} colors the reading; market pulse remains {ctx.get('momentum_label', 'mixed')}.",
            "short_reading": f"The mock {engine_id} reading intentionally mixes market pulse with engine-specific artifact signals for frontend contrast.",
            "long_reading": "This deterministic mock is not a forecast. It is designed to make cards diverge visually while preserving the same schema as real LLM output.",
            "symbols": symbols,
            "risk_tags": risks,
            "visual": {"palette": "ember" if polarity == "favorable" else "indigo", "icon": symbols[0].lower().replace(" ", "_"), "card_style": intensity},
        }

    @staticmethod
    def _mock_engine_signal(engine_id: str, raw_artifact: Dict[str, Any]) -> int:
        if engine_id == "tarot":
            key = raw_artifact.get("spread", [{}])[-1]
        elif engine_id == "wenwang":
            key = {
                "moving_lines": raw_artifact.get("moving_lines", []),
                "image": raw_artifact.get("primary_hexagram", {}).get("image"),
            }
        elif engine_id == "bazi":
            key = raw_artifact.get("useful_gods", {})
        elif engine_id == "ziwei":
            palaces = raw_artifact.get("palaces", [])
            key = [p for p in palaces if p.get("transformations")]
        elif engine_id == "astrology":
            key = {
                "moon": raw_artifact.get("moon_phase_proxy"),
                "zodiac": raw_artifact.get("asset_zodiac"),
            }
        else:
            key = raw_artifact.get("pulse", {})
        digest = hashlib.sha256(json.dumps(key, sort_keys=True, default=str).encode("utf-8")).hexdigest()
        return int(digest[:4], 16) % 45 - 22

    @staticmethod
    def _symbols(engine_id: str, raw_artifact: Dict[str, Any], ctx: Dict[str, Any]) -> list[str]:
        if engine_id == "tarot":
            return [raw_artifact["spread"][0]["card"], raw_artifact["spread"][-1]["card"]]
        if engine_id == "wenwang":
            return [raw_artifact["primary_hexagram"]["image"], raw_artifact["useful_god"]["main"]]
        if engine_id == "bazi":
            return [raw_artifact["strength_and_roots"]["day_element"], raw_artifact["pattern"]["name"]]
        if engine_id == "ziwei":
            return [raw_artifact["life_master"], raw_artifact["life_palace"]]
        if engine_id == "astrology":
            return [raw_artifact["asset_zodiac"], raw_artifact["moon_phase_proxy"]]
        return [ctx.get("momentum_label", "mixed"), ctx.get("volatility_label", "normal")]

    @staticmethod
    def _risks(ctx: Dict[str, Any]) -> list[str]:
        risks = []
        if "elevated" in str(ctx.get("volatility_label")) or "extreme" in str(ctx.get("volatility_label")):
            risks.append("volatility")
        if ctx.get("drawdown_label") in {"deep", "material"}:
            risks.append("drawdown")
        if ctx.get("momentum_label") == "mixed":
            risks.append("mixed_momentum")
        return risks or ["timing_risk"]

    def _openai_compatible(self, engine_id: str, raw_artifact: Dict[str, Any]) -> Dict[str, Any]:
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("AUGAR_LLM_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY or AUGAR_LLM_API_KEY is required for non-mock providers")
        base_url = (self.params.base_url or "https://api.openai.com/v1").rstrip("/")
        url = f"{base_url}/chat/completions"
        prompt = (
            "You are an AUGAR oracle interpreter. Return strict JSON with keys: "
            "score, polarity, intensity, omen_type, headline, subline, short_reading, long_reading, symbols, risk_tags, visual. "
            "Do not include markdown. Raw artifact:\n"
            + json.dumps(raw_artifact, ensure_ascii=False, default=str)
        )
        payload = {
            "model": self.params.model,
            "messages": [
                {"role": "system", "content": "Return only valid JSON for the requested schema."},
                {"role": "user", "content": prompt},
            ],
            "temperature": self.params.temperature,
            "top_p": self.params.top_p,
            "max_tokens": self.params.max_output_tokens,
        }
        last_error: Exception | None = None
        for _ in range(max(1, self.params.max_retries + 1)):
            try:
                resp = requests.post(url, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, json=payload, timeout=self.params.timeout)
                resp.raise_for_status()
                content = resp.json()["choices"][0]["message"]["content"]
                return json.loads(content)
            except Exception as exc:
                last_error = exc
        raise RuntimeError(f"LLM provider failed for {engine_id}: {last_error}")

    def _chatgpt_oauth(self, engine_id: str, raw_artifact: Dict[str, Any]) -> Dict[str, Any]:
        codex_path = self.params.codex_path or self._find_codex_executable()
        codex_home = Path(self.params.codex_home or os.getenv("CODEX_HOME", Path.home() / ".codex"))
        prompt = (
            "You are an AUGAR oracle interpreter. Return strict JSON with keys: "
            "score, polarity, intensity, omen_type, headline, subline, short_reading, long_reading, symbols, risk_tags, visual. "
            "visual must be an object. symbols and risk_tags must be arrays. Do not include markdown. Raw artifact:\n"
            + json.dumps(raw_artifact, ensure_ascii=False, default=str)
        )
        schema = {
            "type": "object",
            "properties": {
                "score": {"type": "integer", "minimum": 1, "maximum": 99},
                "polarity": {"type": "string"},
                "intensity": {"type": "string"},
                "omen_type": {"type": "string"},
                "headline": {"type": "string"},
                "subline": {"type": "string"},
                "short_reading": {"type": "string"},
                "long_reading": {"type": "string"},
                "symbols": {"type": "array", "items": {"type": "string"}},
                "risk_tags": {"type": "array", "items": {"type": "string"}},
                "visual": {
                    "type": "object",
                    "properties": {
                        "palette": {"type": "string"},
                        "icon": {"type": "string"},
                        "card_style": {"type": "string"},
                    },
                    "required": ["palette", "icon", "card_style"],
                    "additionalProperties": False,
                },
            },
            "required": [
                "score", "polarity", "intensity", "omen_type", "headline", "subline",
                "short_reading", "long_reading", "symbols", "risk_tags", "visual",
            ],
            "additionalProperties": False,
        }
        last_error: Exception | None = None
        for _ in range(max(1, self.params.max_retries + 1)):
            tmp_dir = Path(tempfile.mkdtemp(prefix="augar-codex-"))
            schema_path = tmp_dir / "schema.json"
            output_path = tmp_dir / "output.json"
            try:
                schema_path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
                env = os.environ.copy()
                env["CODEX_HOME"] = str(codex_home)
                status = subprocess.run(
                    [codex_path, "login", "status"],
                    env=env,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    capture_output=True,
                    timeout=45,
                )
                if status.returncode != 0:
                    raise RuntimeError(f"Codex ChatGPT OAuth is not logged in for CODEX_HOME={codex_home}: {status.stdout}{status.stderr}")
                cmd = [
                    codex_path,
                    "exec",
                    "-m",
                    self.params.model,
                    "-c",
                    f'model_reasoning_effort="{self.params.reasoning_effort or "low"}"',
                    "--ephemeral",
                    "--skip-git-repo-check",
                    "-s",
                    "read-only",
                    "--output-schema",
                    str(schema_path),
                    "-o",
                    str(output_path),
                    prompt,
                ]
                result = subprocess.run(
                    cmd,
                    env=env,
                    cwd=str(Path(__file__).resolve().parents[1]),
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    capture_output=True,
                    timeout=self.params.timeout,
                )
                if result.returncode != 0:
                    raise RuntimeError(f"Codex exec failed. stdout={result.stdout[-1200:]} stderr={result.stderr[-1200:]}")
                if not output_path.exists():
                    raise RuntimeError("Codex exec did not produce output JSON")
                return json.loads(output_path.read_text(encoding="utf-8").strip())
            except Exception as exc:
                last_error = exc
            finally:
                shutil.rmtree(tmp_dir, ignore_errors=True)
        raise RuntimeError(f"ChatGPT OAuth LLM provider failed for {engine_id}: {last_error}")

    @staticmethod
    def _find_codex_executable() -> str:
        direct = shutil.which("codex")
        if direct and "WindowsApps" not in direct:
            return direct
        ext_root = Path.home() / ".vscode" / "extensions"
        patterns = [
            "openai.chatgpt-*/bin/windows-x86_64/codex.exe",
            "openai.chatgpt-*/bin/linux-x86_64/codex",
            "openai.chatgpt-*/bin/darwin-arm64/codex",
            "openai.chatgpt-*/bin/darwin-x86_64/codex",
        ]
        for pattern in patterns:
            candidates = sorted(ext_root.glob(pattern), reverse=True)
            for candidate in candidates:
                if candidate.exists():
                    return str(candidate)
        raise FileNotFoundError("Could not locate Codex executable for chatgpt_oauth provider")

    @staticmethod
    def _extract_responses_text(body: Dict[str, Any]) -> str:
        parts: list[str] = []
        for item in body.get("output", []) if isinstance(body.get("output"), list) else []:
            for content in item.get("content", []) if isinstance(item, dict) else []:
                if isinstance(content, dict):
                    if content.get("type") in {"output_text", "text"} and content.get("text"):
                        parts.append(str(content["text"]))
        return "\n".join(parts)

    @staticmethod
    def _provider_error(resp: requests.Response) -> str:
        try:
            payload = resp.json()
            message = payload.get("error", {}).get("message") if isinstance(payload, dict) else None
        except Exception:
            message = None
        if message:
            return f"{resp.status_code} {message}"
        return f"{resp.status_code} {resp.text[:300]}"
