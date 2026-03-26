"""
Smart Run — Executes tasks through the right model automatically.
=================================================================
Routes by complexity, streams output, traces to LangSmith, checks budget,
falls back gracefully when a model is unavailable.

Usage
-----
    python smart_run.py "format this JSON: {...}"         # Tier 0 → gemma3:1b
    python smart_run.py "explain LangGraph"               # Tier 1 → Haiku
    python smart_run.py "refactor auth module" --local    # Tier 2 → qwen2.5-coder
    python smart_run.py "your task" --dry-run             # show routing only
    python smart_run.py "your task" --tier 0              # force tier
    python smart_run.py "your task" --no-tools            # allow non-tool models
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Make ~/.claude importable
sys.path.insert(0, str(Path.home() / ".claude"))
from model_router import route, resolve_local_model, is_model_available

import ollama as _ollama
try:
    from langsmith import traceable as _traceable
    _LANGSMITH = bool(os.getenv("LANGCHAIN_API_KEY"))
except ImportError:
    _LANGSMITH = False
    def _traceable(**_kw):        # no-op decorator if langsmith not installed
        def _wrap(fn): return fn
        return _wrap

try:
    from vector_router import query_agents as _query_agents
    _VECTOR_ROUTER = True
except ImportError:
    _VECTOR_ROUTER = False

try:
    from parallel_runner import fanout as _fanout
    import asyncio as _asyncio
    _PARALLEL_RUNNER = True
except ImportError:
    _PARALLEL_RUNNER = False

OLLAMA_LOG = Path.home() / ".claude" / "ollama_usage.jsonl"
BUDGET_FILE = Path.home() / ".claude" / "token_budget.json"


# ── Ollama execution ───────────────────────────────────────────────────────────

@_traceable(name="ollama-chat", run_type="llm", metadata={"provider": "ollama"})
def _ollama_call(model: str, prompt: str) -> dict:
    """
    Non-streaming internal call. Used when output is consumed programmatically.
    LangSmith traces this if LANGCHAIN_API_KEY is set.
    """
    resp = _ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0.1, "num_ctx": 4096},
    )
    return {
        "content":      resp["message"]["content"],
        "input_tokens":  resp.get("prompt_eval_count", 0),
        "output_tokens": resp.get("eval_count", 0),
    }


def _ollama_stream(model: str, prompt: str) -> dict:
    """
    Streaming call that prints tokens as they arrive.
    Returns same shape as _ollama_call.
    """
    chunks = _ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        stream=True,
        options={"temperature": 0.1, "num_ctx": 4096},
    )
    full_text = ""
    input_tokens = output_tokens = 0
    for chunk in chunks:
        token = chunk["message"]["content"]
        print(token, end="", flush=True)
        full_text += token
        if chunk.get("done"):
            input_tokens  = chunk.get("prompt_eval_count", 0)
            output_tokens = chunk.get("eval_count", 0)
    print()  # newline after stream ends
    return {
        "content":      full_text,
        "input_tokens":  input_tokens,
        "output_tokens": output_tokens,
    }


def _log_ollama(model: str, prompt: str, tokens_in: int, tokens_out: int, elapsed: float) -> None:
    """Append Ollama run to ollama_usage.jsonl for token_tracker to read."""
    entry = {
        "ts":        datetime.now(timezone.utc).isoformat(),
        "model":     model,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "elapsed":   round(elapsed, 2),
        "prompt_preview": prompt[:80],
    }
    with OLLAMA_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


# ── Budget check ───────────────────────────────────────────────────────────────

def _budget_ok(cost_tier: str) -> tuple[bool, str]:
    """
    Returns (ok, message). Warns if daily cost budget >= warn_pct.
    Only blocks medium/high cost Claude calls — never blocks free Ollama.
    """
    if cost_tier == "free":
        return True, ""
    try:
        from token_tracker import today_usage, _load_stats, _load_budget
        stats  = _load_stats()
        budget = _load_budget()
        today  = today_usage(stats)
        warn   = budget["warn_pct"] / 100
        if today["cost"] >= budget["daily_cost_usd"] * warn:
            msg = (
                f"Daily cost budget {budget['warn_pct']}% reached "
                f"(${today['cost']:.4f} / ${budget['daily_cost_usd']:.2f}). "
                f"Routing to cheaper model."
            )
            return False, msg
    except Exception:
        pass
    return True, ""


# ── Main executor ──────────────────────────────────────────────────────────────

def run_task(
    prompt: str,
    prefer_local: bool = False,
    needs_tools: bool = True,
    force_tier: int | None = None,
    stream: bool = True,
    dry_run: bool = False,
) -> dict:
    """
    Classify, route, and execute a task.
    Returns a result dict with full routing metadata + output.
    """
    decision = route(
        prompt,
        prefer_local=prefer_local,
        needs_tools=needs_tools,
        force_tier=force_tier,
    )

    result = {
        "prompt":           prompt,
        "tier":             decision["tier"],
        "backend":          decision["backend"],
        "model":            decision["model"],
        "reason":           decision["reason"],
        "cost_tier":        decision["cost_tier"],
        "matched_keywords": decision["matched_keywords"],
        "used_fallback":    decision["used_fallback"],
        "output":           None,
        "input_tokens":     0,
        "output_tokens":    0,
        "elapsed":          None,
        "error":            None,
        "dry_run":          dry_run,
    }

    if dry_run:
        result["output"] = "[dry-run] Routing decision only — no model was called."
        return result

    # Budget gate — downgrade if over daily limit
    ok, budget_msg = _budget_ok(decision["cost_tier"])
    if not ok:
        print(f"  [budget] {budget_msg}", flush=True)
        # Downgrade to Haiku if Sonnet/Opus was selected
        if decision["cost_tier"] in ("medium", "high"):
            from model_router import CLAUDE_MODELS
            decision["model"]      = CLAUDE_MODELS["haiku"].model
            decision["agent_param"] = "haiku"
            decision["cost_tier"]  = "low"
            result["model"]        = decision["model"]
            result["reason"]      += " [budget-downgraded to haiku]"

    if decision["backend"] == "ollama":
        model = decision["model"]

        # Verify model is actually installed; walk fallback chain if not
        if not is_model_available(model):
            resolved, was_fallback = resolve_local_model(model)
            if is_model_available(resolved):
                print(f"  [fallback] {model} not found, using {resolved}", flush=True)
                model = resolved
                result["model"]        = resolved
                result["used_fallback"] = True
            else:
                result["error"] = (
                    f"Model '{model}' is not installed. "
                    f"Run: ollama pull {model}"
                )
                return result

        t0 = time.time()
        try:
            if stream:
                resp = _ollama_stream(model, prompt)
            else:
                resp = _ollama_call(model, prompt)

            elapsed = time.time() - t0
            result["output"]        = resp["content"]
            result["input_tokens"]  = resp["input_tokens"]
            result["output_tokens"] = resp["output_tokens"]
            result["elapsed"]       = round(elapsed, 2)
            _log_ollama(model, prompt, resp["input_tokens"], resp["output_tokens"], elapsed)

        except _ollama.ResponseError as e:
            result["error"] = f"Ollama error: {e}. Is Ollama running? Try: ollama serve"
        except ConnectionError:
            result["error"] = "Ollama is not running. Start it with: ollama serve"
        except Exception as e:
            result["error"] = str(e)

    else:
        # Claude backend — semantic agent lookup + routing signal
        agent_hint = ""
        if _VECTOR_ROUTER:
            try:
                hits = _query_agents(prompt, n=3)
                if hits:
                    top = hits[0]
                    agent_hint = (
                        f"\n  Top agent  : {top['agent']} "
                        f"(dept={top['department']}, score={top['score']})"
                    )
                    if len(hits) > 1:
                        others = ", ".join(h["agent"] for h in hits[1:])
                        agent_hint += f"\n  Alternates : {others}"
            except Exception:
                pass  # index not built yet — graceful degradation

        result["output"] = (
            f"[smart_run] Route to Claude.\n"
            f"  model=\"{decision['agent_param']}\"\n"
            f"  Invoke: Agent tool with model=\"{decision['agent_param']}\""
            f"{agent_hint}"
        )

    return result


# ── CLI ────────────────────────────────────────────────────────────────────────

def _print_result(r: dict) -> None:
    tier_names = ["Trivial", "Simple", "Standard", "Complex", "Critical"]
    kw = ", ".join(r.get("matched_keywords", [])) or "(length heuristic)"

    print(f"\n{'='*62}")
    print(f"  ROUTING")
    print(f"{'='*62}")
    print(f"  Tier     : {r['tier']} ({tier_names[r['tier']]})")
    print(f"  Model    : {r['model']}")
    print(f"  Backend  : {r['backend']}")
    print(f"  Cost     : {r['cost_tier']}")
    print(f"  Keywords : {kw}")
    print(f"  Reason   : {r['reason']}")
    if r["used_fallback"]:
        print(f"  Fallback : yes")
    if r["elapsed"]:
        tok_s = ""
        total = r.get("input_tokens", 0) + r.get("output_tokens", 0)
        if total:
            tok_s = f"  |  {total} tokens ({r['input_tokens']} in / {r['output_tokens']} out)"
        print(f"  Elapsed  : {r['elapsed']}s{tok_s}")

    if not r["dry_run"] and r["backend"] == "ollama":
        print(f"\n{'='*62}")
        print(f"  OUTPUT")
        print(f"{'='*62}")

    if r["error"]:
        print(f"\n  ERROR: {r['error']}")
    elif r["dry_run"]:
        print(f"\n  {r['output']}")
    elif r["backend"] == "claude":
        print(f"\n  {r['output']}")
    # (ollama output already streamed above)
    print()


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(
            "Usage: python smart_run.py \"task\" "
            "[--prefer-local] [--no-tools] [--dry-run] [--tier N] [--no-stream] [--fanout]"
        )
        sys.exit(1)

    prompt       = args[0]
    prefer_local = "--prefer-local" in args or "--local" in args
    needs_tools  = "--no-tools" not in args
    dry_run      = "--dry-run" in args
    stream       = "--no-stream" not in args
    fanout_mode  = "--fanout" in args
    force_tier   = None

    for i, a in enumerate(args):
        if a == "--tier" and i + 1 < len(args):
            force_tier = int(args[i + 1])

    # --fanout: run prompt across comparison models in parallel
    if fanout_mode:
        if not _PARALLEL_RUNNER:
            print("parallel_runner not available. Ensure parallel_runner.py is in ~/.claude/")
            sys.exit(1)
        fanout_models = ["gemma3:1b", "llama3.2:3b", "qwen2.5-coder:7b"]
        # Allow custom models: --fanout --models m1 m2 m3
        if "--models" in args:
            mi = args.index("--models")
            fanout_models = [a for a in args[mi+1:] if not a.startswith("--")]
        print(f"\n  [fanout] Running across {len(fanout_models)} models: {', '.join(fanout_models)}")
        results = _asyncio.run(_fanout(prompt, fanout_models))
        wall = max(r["elapsed"] for r in results) if results else 0
        seq  = sum(r["elapsed"] for r in results)
        print(f"  Wall: {wall:.2f}s  |  Sequential estimate: {seq:.1f}s  |  Speedup: {seq/wall:.1f}x\n")
        for r in results:
            tok = r["input_tokens"] + r["output_tokens"]
            status = f"ERROR: {r['error']}" if r["error"] else f"{r['elapsed']}s | {tok} tok"
            print(f"  [{r['model']}]  {status}")
            if r["output"]:
                for line in r["output"].strip().splitlines()[:4]:
                    print(f"    {line}")
            print()
        sys.exit(0)

    result = run_task(
        prompt,
        prefer_local=prefer_local,
        needs_tools=needs_tools,
        force_tier=force_tier,
        stream=stream,
        dry_run=dry_run,
    )
    _print_result(result)
