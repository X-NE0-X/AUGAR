"""Entry point for `pip install augar` → `augar` CLI command.

Self-contained — does NOT depend on AUGAR.py at repo root.
Works in both pip-installed and dev-checkout modes.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import textwrap
from pathlib import Path


def _repo_root() -> Path:
    pkg = Path(__file__).resolve().parent          # augar_engine/
    root = pkg.parent
    if (root / "pyproject.toml").exists():
        return root
    for _ in range(4):
        if (root / "frontend" / "dist").is_dir():
            return root
        root = root.parent
    return pkg.parent


def _frontend_dir() -> Path:       return _repo_root() / "frontend"
def _dist_dir() -> Path:           return _frontend_dir() / "dist"
def _node_modules() -> Path:       return _frontend_dir() / "node_modules"


def _ensure_node_modules() -> None:
    if not _node_modules().is_dir():
        print("[augar] Installing frontend dependencies (npm install)...")
        subprocess.run(["npm", "install"], cwd=str(_frontend_dir()), check=True, shell=(sys.platform == "win32"))


def _ensure_build() -> None:
    _ensure_node_modules()
    if not (_dist_dir() / "index.html").exists():
        print("[augar] Building frontend (npm run build)...")
        subprocess.run(["npm", "run", "build"], cwd=str(_frontend_dir()), check=True, shell=(sys.platform == "win32"))


def _cmd_build() -> None:
    _ensure_node_modules()
    print("[augar] Building frontend...")
    subprocess.run(["npm", "run", "build"], cwd=str(_frontend_dir()), check=True, shell=(sys.platform == "win32"))
    print(f"[augar] Build complete -> {_dist_dir()}")


def _add_static_serve() -> None:
    static_dir = os.environ.get("AUGAR_SERVE_STATIC")
    if not static_dir or not Path(static_dir).is_dir():
        return
    from fastapi.staticfiles import StaticFiles as _SF
    from augar_engine.api.app import app as _app
    _app.mount("/assets", _SF(directory=str(Path(static_dir) / "assets")), name="assets")
    _app.mount("/tarots", _SF(directory=str(Path(static_dir) / "tarots")), name="tarots")
    _index = (Path(static_dir) / "index.html").read_text(encoding="utf-8")
    from fastapi.responses import HTMLResponse as _HR
    @_app.get("/{full_path:path}", response_class=_HR)
    async def _spa(full_path: str):
        # API routes already matched by this point — everything else gets index.html
        return _HR(content=_index)


def _cmd_serve() -> None:
    _ensure_build()
    os.environ.setdefault("AUGAR_SERVE_STATIC", str(_dist_dir()))
    _add_static_serve()
    print("[augar] Starting server...")
    print("[augar] Frontend  -> http://127.0.0.1:8765")
    print("[augar] API docs  -> http://127.0.0.1:8765/docs")
    print("[augar] Press Ctrl+C to stop.")
    import uvicorn
    uvicorn.run("augar_engine.api.app:app", host="127.0.0.1", port=8765, log_level="info")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="augar", description="AUGAR — Ask Universe, Get A Reading.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            examples:
              augar serve
              augar generate --period 2026-04-M --all-indexes --provider mock
              augar check --provider chatgpt_oauth
              augar build
        """),
    )
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("serve", help="Start the full application (backend + frontend)")
    sub.add_parser("build", help="Rebuild the frontend static assets")
    sub.add_parser("check", help="Check LLM provider connectivity")
    sub.add_parser("generate", help="Generate oracle cards")
    args, unknown = parser.parse_known_args(argv)

    # no subcommand → default action
    if args.command is None:
        _cmd_serve()
        return

    if args.command == "serve":
        _cmd_serve()
    elif args.command == "build":
        _cmd_build()
    elif args.command == "check":
        from augar_engine.check_llm_provider import main as _chk; _chk(unknown)
    elif args.command == "generate":
        from augar_engine.cli import main as _gen; _gen(unknown)


if __name__ == "__main__":
    main()
