from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional

import requests

from .constants import (
    CODEX_CHECK_TIMEOUT,
    DEFAULT_MAX_OUTPUT_TOKENS,
    DEFAULT_MAX_RETRIES,
    DEFAULT_MODEL,
    DEFAULT_PROVIDER,
    DEFAULT_REASONING_EFFORT,
    DEFAULT_TEMPERATURE,
    DEFAULT_TIMEOUT,
    DEFAULT_TOP_P,
    OPENAI_BASE_URL,
    PROJECT_ROOT,
)


@dataclass
class LLMParams:
    provider: str = DEFAULT_PROVIDER
    model: str = DEFAULT_MODEL
    base_url: Optional[str] = None
    temperature: float = DEFAULT_TEMPERATURE
    top_p: float = DEFAULT_TOP_P
    max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS
    reasoning_effort: Optional[str] = DEFAULT_REASONING_EFFORT
    timeout: int = DEFAULT_TIMEOUT
    max_retries: int = DEFAULT_MAX_RETRIES
    codex_auth_path: Optional[str] = None
    codex_home: Optional[str] = None
    codex_path: Optional[str] = None
    history_run_id: Optional[str] = None
    api_key: Optional[str] = None

    def public_dict(self) -> Dict[str, Any]:
        return asdict(self)


class LLMClient:
    def __init__(self, params: LLMParams) -> None:
        self.params = params

    def interpret(self, engine_id: str, raw_artifact: Dict[str, Any]) -> Dict[str, Any]:
        if self.params.provider in {"history", "replay"}:
            return self._history_interpret(engine_id, raw_artifact, allow_history=True)
        if self.params.provider == "chatgpt_oauth":
            return self._chatgpt_oauth(engine_id, raw_artifact)
        if self.params.provider in {"openai", "openai_compatible", "deepseek", "local", "custom"}:
            return self._openai_compatible(engine_id, raw_artifact)
        raise ValueError(f"Unsupported LLM provider: {self.params.provider}")

    def _history_interpret(
        self,
        engine_id: str,
        raw_artifact: Dict[str, Any],
        *,
        allow_history: bool,
        required: bool = True,
    ) -> Optional[Dict[str, Any]]:
        period_id = str(raw_artifact.get("period", {}).get("id", ""))
        ticker = str(raw_artifact.get("asset", {}).get("ticker", ""))
        candidates = self._history_candidates(period_id, ticker, engine_id, allow_history=allow_history)
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

    def _history_candidates(self, period_id: str, ticker: str, engine_id: str, *, allow_history: bool) -> list[Path]:
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
            if not allow_history and provider in {"history", "replay"}:
                continue
            card_path = manifest_path.parent / "debug" / "cards" / period_id / ticker / f"{engine_id}.json"
            if not card_path.exists():
                continue
            manifests.append((provider in {"history", "replay"}, str(manifest.get("generated_at", "")), card_path))
        manifests.sort(key=lambda item: (item[0], item[1]))
        manifests.reverse()
        manifests.sort(key=lambda item: item[0])
        return [item[2] for item in manifests]

    def _openai_compatible(self, engine_id: str, raw_artifact: Dict[str, Any]) -> Dict[str, Any]:
        if self.params.api_key:
            api_key = self.params.api_key
        elif self.params.provider == "deepseek":
            api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("AUGAR_LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        else:
            api_key = os.getenv("OPENAI_API_KEY") or os.getenv("AUGAR_LLM_API_KEY")

        if self.params.provider == "deepseek":
            default_base = "https://api.deepseek.com"
        else:
            default_base = OPENAI_BASE_URL

        if not api_key:
            raise RuntimeError("OPENAI_API_KEY, DEEPSEEK_API_KEY, or AUGAR_LLM_API_KEY is required for non-mock providers")
        base_url = (self.params.base_url or default_base).rstrip("/")
        url = f"{base_url}/chat/completions"
        prompt = (
            "你是AUGAR神谕解读器。根据原始artifact输出严格JSON，键名英文（score, polarity, intensity, omen_type, headline, subline, short_reading, long_reading, symbols, risk_tags, visual）。"
            "所有文本内容(headline,subline,short_reading,long_reading)必须用中文。不可包含markdown。原始artifact：\n"
            + json.dumps(raw_artifact, ensure_ascii=False, default=str)
        )
        payload: Dict[str, Any] = {
            "model": self.params.model,
            "messages": [
                {"role": "system", "content": "仅输出合法JSON，所有文本用中文。键名英文。"},
                {"role": "user", "content": prompt},
            ],
            "temperature": self.params.temperature,
            "top_p": self.params.top_p,
            "max_tokens": self.params.max_output_tokens,
        }
        if self.params.provider == "deepseek":
            if self.params.reasoning_effort:
                # thinking mode: reasoning eats tokens — double the budget
                payload["reasoning_effort"] = self.params.reasoning_effort
                payload["thinking"] = {"type": "enabled"}
                payload["max_tokens"] = max(payload["max_tokens"], 8000)
            else:
                # explicitly disable thinking to prevent hidden reasoning
                # from consuming the output token budget (DeepSeek V4 default)
                payload["thinking"] = {"type": "disabled"}
        last_error: Exception | None = None
        raw_content: str = ""
        for attempt in range(max(1, self.params.max_retries + 1)):
            try:
                resp = requests.post(url, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, json=payload, timeout=self.params.timeout)
                resp.raise_for_status()
                body = resp.json()
                raw_content = body["choices"][0]["message"]["content"]
                return json.loads(raw_content)
            except json.JSONDecodeError:
                last_error = RuntimeError(f"LLM returned invalid JSON (attempt {attempt+1}). Raw: {raw_content[:500]}")
            except Exception as exc:
                last_error = exc
        raise RuntimeError(f"LLM provider failed for {engine_id}: {last_error}")

    def _chatgpt_oauth(self, engine_id: str, raw_artifact: Dict[str, Any]) -> Dict[str, Any]:
        codex_path = self.params.codex_path or self._find_codex_executable()
        codex_home = Path(self.params.codex_home or os.getenv("CODEX_HOME", Path.home() / ".codex"))
        prompt = (
            "你是AUGAR神谕解读器。根据原始artifact输出严格JSON，键名英文（score, polarity, intensity, omen_type, headline, subline, short_reading, long_reading, symbols, risk_tags, visual）。"
            "visual是对象，symbols和risk_tags是数组。所有文本必须用中文。不可包含markdown。原始artifact：\n"
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
                    timeout=CODEX_CHECK_TIMEOUT,
                )
                if status.returncode != 0:
                    raise RuntimeError(f"Codex ChatGPT OAuth is not logged in for CODEX_HOME={codex_home}: {status.stdout}{status.stderr}")
                cmd = [
                    codex_path,
                    "exec",
                    "-m",
                    self.params.model,
                    "-c",
                    f'model_reasoning_effort="{self.params.reasoning_effort or DEFAULT_REASONING_EFFORT}"',
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
