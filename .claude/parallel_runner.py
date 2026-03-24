"""
Parallel Runner
===============
Runs multiple Ollama model calls concurrently using asyncio.
Supports three patterns:

  Fan-out   — same prompt on multiple models simultaneously (comparison/ensemble)
  Pipeline  — decompose task into sub-tasks, each on best model, run in parallel
  Batch     — list of (model, prompt) pairs, all run at once

Usage
-----
    python parallel_runner.py fanout "explain quantum computing briefly" --models gemma3:1b llama3.2:3b
    python parallel_runner.py batch tasks.json
    python parallel_runner.py pipeline "analyze this startup idea: ..."

Library
-------
    from parallel_runner import fanout, batch_run, pipeline_run
    import asyncio

    results = asyncio.run(fanout("explain X", ["gemma3:1b", "llama3.2:3b"]))
    for r in results:
        print(r["model"], r["elapsed"], r["output"][:100])
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path.home() / ".claude"))
from model_router import route, OLLAMA_MODELS

try:
    import ollama
    _async_client = ollama.AsyncClient()
except ImportError:
    print("ollama package not installed. Run: pip install ollama")
    sys.exit(1)

try:
    from langsmith import traceable
    import os
    _LANGSMITH = bool(os.getenv("LANGCHAIN_API_KEY"))
except ImportError:
    _LANGSMITH = False
    def traceable(**_kw):
        def _wrap(fn): return fn
        return _wrap


# ── Core async primitives ──────────────────────────────────────────────────────

async def _run_one(
    model: str,
    prompt: str,
    temperature: float = 0.1,
    num_ctx: int = 4096,
    label: str = "",
) -> dict:
    """Run a single model call async. Returns result dict."""
    t0 = time.perf_counter()
    label = label or model
    try:
        resp = await _async_client.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": temperature, "num_ctx": num_ctx},
        )
        elapsed = time.perf_counter() - t0
        return {
            "label":         label,
            "model":         model,
            "output":        resp["message"]["content"],
            "input_tokens":  resp.get("prompt_eval_count", 0),
            "output_tokens": resp.get("eval_count", 0),
            "elapsed":       round(elapsed, 2),
            "error":         None,
        }
    except Exception as e:
        return {
            "label":   label,
            "model":   model,
            "output":  None,
            "input_tokens": 0,
            "output_tokens": 0,
            "elapsed": round(time.perf_counter() - t0, 2),
            "error":   str(e),
        }


# ── Fan-out: same prompt → multiple models ─────────────────────────────────────

async def fanout(
    prompt: str,
    models: list[str],
    temperature: float = 0.1,
) -> list[dict]:
    """
    Send the same prompt to all models concurrently.
    Returns list of result dicts, sorted by elapsed time (fastest first).
    """
    tasks = [_run_one(m, prompt, temperature=temperature) for m in models]
    results = await asyncio.gather(*tasks)
    return sorted(results, key=lambda r: r["elapsed"])


# ── Batch: list of (model, prompt) pairs ──────────────────────────────────────

async def batch_run(items: list[dict]) -> list[dict]:
    """
    Run a batch of independent tasks in parallel.
    Each item: {"model": str, "prompt": str, "label": str (optional)}
    """
    tasks = [
        _run_one(
            item["model"],
            item["prompt"],
            label=item.get("label", item["model"]),
        )
        for item in items
    ]
    return list(await asyncio.gather(*tasks))


# ── Pipeline: decompose → route each part → run in parallel ───────────────────

def _decompose(task: str) -> list[dict]:
    """
    Naive decomposition: split on newlines or semicolons.
    Each sub-task gets its own model routing decision.
    Returns list of {"label", "model", "prompt"}.
    """
    # Split on newlines, bullets, or semicolons
    import re
    parts = re.split(r"(?:\n+|\s*[;]\s*|\s*[-*]\s+)", task.strip())
    parts = [p.strip() for p in parts if len(p.strip()) > 10]

    if len(parts) <= 1:
        # Can't decompose — treat as single task
        decision = route(task, prefer_local=True)
        return [{"label": "task", "model": decision["model"], "prompt": task}]

    items = []
    for i, part in enumerate(parts):
        decision = route(part, prefer_local=True)
        if decision["backend"] == "ollama":
            items.append({
                "label": f"part_{i+1}",
                "model": decision["model"],
                "prompt": part,
            })
    return items


async def pipeline_run(task: str) -> list[dict]:
    """
    Decompose task into sub-tasks, route each to best local model, run in parallel.
    """
    items = _decompose(task)
    if not items:
        return []
    return await batch_run(items)


# ── Output helpers ─────────────────────────────────────────────────────────────

def _print_fanout(results: list[dict], prompt: str) -> None:
    total_wall = max(r["elapsed"] for r in results) if results else 0
    print(f"\n  Prompt: {prompt[:70]}")
    print(f"  Wall time: {total_wall:.2f}s  (sequential would be ~{sum(r['elapsed'] for r in results):.1f}s)\n")
    for r in results:
        tokens = r["input_tokens"] + r["output_tokens"]
        status = f"ERROR: {r['error']}" if r["error"] else f"{r['elapsed']}s | {tokens} tok"
        print(f"  [{r['model']}]  {status}")
        if r["output"]:
            lines = r["output"].strip().splitlines()
            for line in lines[:5]:
                print(f"    {line}")
            if len(lines) > 5:
                print(f"    ... ({len(lines)-5} more lines)")
        print()


def _print_batch(results: list[dict]) -> None:
    total_wall = max(r["elapsed"] for r in results) if results else 0
    seq_time   = sum(r["elapsed"] for r in results)
    speedup    = seq_time / total_wall if total_wall > 0 else 1
    print(f"\n  Batch complete: {len(results)} tasks")
    print(f"  Wall time: {total_wall:.2f}s  |  Sequential estimate: {seq_time:.1f}s  |  Speedup: {speedup:.1f}x\n")
    print(f"  {'Label':<20} {'Model':<28} {'Elapsed':>8} {'Tokens':>8}  Status")
    print(f"  {'-'*80}")
    for r in results:
        tokens = r["input_tokens"] + r["output_tokens"]
        status = "ERROR" if r["error"] else "OK"
        print(f"  {r['label']:<20} {r['model']:<28} {r['elapsed']:>7.2f}s {tokens:>8}  {status}")
    print()


# ── CLI ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print("Commands: fanout <prompt> [--models m1 m2 ...] | batch <file.json> | pipeline <task>")
        sys.exit(0)

    cmd = args[0]

    if cmd == "fanout":
        if len(args) < 2:
            print("Usage: parallel_runner.py fanout \"prompt\" [--models m1 m2 ...]")
            sys.exit(1)
        prompt = args[1]
        if "--models" in args:
            mi = args.index("--models")
            models = args[mi+1:]
        else:
            # Default: fast comparison set
            models = ["gemma3:1b", "llama3.2:3b", "gemma3:4b"]

        print(f"\n  Running fanout across {len(models)} models: {', '.join(models)}")
        results = asyncio.run(fanout(prompt, models))
        _print_fanout(results, prompt)

    elif cmd == "batch":
        if len(args) < 2:
            print("Usage: parallel_runner.py batch <tasks.json>")
            sys.exit(1)
        items = json.loads(Path(args[1]).read_text())
        print(f"\n  Running batch of {len(items)} tasks in parallel...")
        results = asyncio.run(batch_run(items))
        _print_batch(results)

    elif cmd == "pipeline":
        if len(args) < 2:
            print("Usage: parallel_runner.py pipeline \"task with multiple parts; separated by semicolons\"")
            sys.exit(1)
        task = args[1]
        items = _decompose(task)
        print(f"\n  Decomposed into {len(items)} sub-tasks:")
        for item in items:
            print(f"    [{item['model']}] {item['prompt'][:60]}")
        print(f"\n  Running in parallel...")
        results = asyncio.run(pipeline_run(task))
        _print_batch(results)

    else:
        print(f"Unknown command: {cmd}")
        print("Commands: fanout | batch | pipeline")
        sys.exit(1)
