"""
Ollama Model Warm-up
====================
Pre-loads models into memory by sending a tiny ping prompt.
Run at session start so first real calls are instant.

Usage
-----
    python warmup.py                    # warm default models
    python warmup.py --models gemma3:1b llama3.2:3b
    python warmup.py --all              # warm every installed model
    python warmup.py --status           # show which models are loaded
    python warmup.py --config           # show/edit warmup config
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".claude"))

try:
    import ollama
    _async_client = ollama.AsyncClient()
except ImportError:
    print("[warmup] ollama package not installed.")
    sys.exit(1)

CONFIG_FILE = Path.home() / ".claude" / "warmup_config.json"

DEFAULT_CONFIG = {
    "models": [
        "llama3.2:3b",      # Tier 0-1 with tools — most used
        "gemma3:1b",        # Tier 0 no-tools — fastest
        "qwen2.5-coder:7b", # Code tasks
    ],
    "ping_prompt": "hi",    # minimal prompt just to load weights
    "timeout": 60,          # seconds per model before giving up
    "silent": False,        # set True to suppress output in hooks
}

PING = "hi"


def _load_config() -> dict:
    if CONFIG_FILE.exists():
        return {**DEFAULT_CONFIG, **json.loads(CONFIG_FILE.read_text(encoding="utf-8"))}
    return DEFAULT_CONFIG.copy()


def _save_config(c: dict) -> None:
    CONFIG_FILE.write_text(json.dumps(c, indent=2), encoding="utf-8")


def _get_installed() -> set[str]:
    try:
        import subprocess
        out = subprocess.check_output(
            ["ollama", "list"], text=True, timeout=5, stderr=subprocess.DEVNULL
        )
        return {line.split()[0] for line in out.splitlines()[1:] if line.strip()}
    except Exception:
        return set()


async def _ping_model(model: str, timeout: int) -> dict:
    t0 = time.perf_counter()
    try:
        await asyncio.wait_for(
            _async_client.chat(
                model=model,
                messages=[{"role": "user", "content": PING}],
                options={"temperature": 0, "num_predict": 1},
            ),
            timeout=timeout,
        )
        elapsed = time.perf_counter() - t0
        return {"model": model, "status": "warm", "elapsed": round(elapsed, 2)}
    except asyncio.TimeoutError:
        return {"model": model, "status": "timeout", "elapsed": timeout}
    except Exception as e:
        return {"model": model, "status": "error", "elapsed": round(time.perf_counter() - t0, 2), "error": str(e)}


async def warm_models(models: list[str], timeout: int = 60, silent: bool = False) -> list[dict]:
    installed = _get_installed()
    to_warm   = [m for m in models if m in installed]
    skipped   = [m for m in models if m not in installed]

    if skipped and not silent:
        print(f"[warmup] Skipping (not installed): {', '.join(skipped)}")

    if not to_warm:
        if not silent:
            print("[warmup] No models to warm.")
        return []

    if not silent:
        print(f"[warmup] Warming {len(to_warm)} models in parallel: {', '.join(to_warm)}")

    t0      = time.perf_counter()
    tasks   = [_ping_model(m, timeout) for m in to_warm]
    results = await asyncio.gather(*tasks)
    wall    = time.perf_counter() - t0

    if not silent:
        for r in results:
            icon = "OK" if r["status"] == "warm" else "!!"
            err  = f"  ({r.get('error', '')})" if r.get("error") else ""
            print(f"  [{icon}] {r['model']:<30} {r['elapsed']:.1f}s{err}")
        print(f"[warmup] Done in {wall:.1f}s\n")

    return list(results)


def cmd_status() -> None:
    installed = _get_installed()
    cfg       = _load_config()
    print(f"\n  Configured warm models: {', '.join(cfg['models'])}")
    print(f"  Installed:              {', '.join(sorted(installed))}\n")
    ready  = [m for m in cfg["models"] if m in installed]
    absent = [m for m in cfg["models"] if m not in installed]
    if ready:
        print(f"  Ready to warm : {', '.join(ready)}")
    if absent:
        print(f"  Not installed : {', '.join(absent)}")
    print()


def cmd_config() -> None:
    cfg = _load_config()
    print(f"\n  Warmup config ({CONFIG_FILE})")
    print(json.dumps(cfg, indent=4))
    print()


if __name__ == "__main__":
    args = sys.argv[1:]

    if "--status" in args:
        cmd_status()
        sys.exit(0)

    if "--config" in args:
        cmd_config()
        sys.exit(0)

    cfg = _load_config()

    if "--all" in args:
        models = list(_get_installed())
    elif "--models" in args:
        mi     = args.index("--models")
        models = [a for a in args[mi+1:] if not a.startswith("--")]
    else:
        models = cfg["models"]

    silent  = "--silent" in args or cfg.get("silent", False)
    timeout = cfg.get("timeout", 60)

    asyncio.run(warm_models(models, timeout=timeout, silent=silent))
