#!/usr/bin/env python3
"""
run.py — AI OS Routing Loop
============================
Type a task. The system picks the right agent, loads its system prompt,
and runs it through Claude (Anthropic SDK) or Ollama based on complexity tier.

Usage
-----
    python run.py "analyze competitive threats from OpenAI"
    python run.py "format this JSON: {...}"              # Tier 0 → Ollama
    python run.py "research quantum computing trends"   # Tier 2 → Claude + agent
    python run.py "what should I invest in right now"   # → CIO-Investments agent
    python run.py --rebuild                             # rebuild vector index
    python run.py --dry-run "your task"                 # show routing only
    python run.py --agent CISO "review this code"       # force a specific agent

Interactive mode:
    python run.py                                       # REPL loop
"""

from __future__ import annotations

import os
import re
import sys
import time
from pathlib import Path

# Make ~/.claude importable
sys.path.insert(0, str(Path.home() / ".claude"))

# Load .env from ~/.claude/.env if present (contains ANTHROPIC_API_KEY etc.)
_env_file = Path.home() / ".claude" / ".env"
if _env_file.exists():
    for _line in _env_file.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

import anthropic
from model_router import route, CLAUDE_MODELS

try:
    from token_tracker import today_usage, _load_stats, _load_budget
    _HAS_TRACKER = True
except ImportError:
    _HAS_TRACKER = False

try:
    from resource_tracker import record as _rt_record
    _HAS_RESOURCE_TRACKER = True
except ImportError:
    _HAS_RESOURCE_TRACKER = False

# -- Constants ----------------------------------------------------------------

CLAUDE_MODEL_MAP = {
    "haiku":  "claude-haiku-4-5-20251001",
    "sonnet": "claude-sonnet-4-6",
    "opus":   "claude-opus-4-6",
}
DEFAULT_MAX_TOKENS = 4096
AGENTS_DIR = Path.home() / ".claude" / "agents"
RUN_LOG = Path.home() / ".claude" / "run_log.jsonl"


# -- Budget gate --------------------------------------------------------------

def _budget_check(cost_tier: str) -> tuple[str, float]:
    """Returns (status, daily_cost). status: 'ok' | 'warn' | 'blocked'."""
    if not _HAS_TRACKER or cost_tier == "free":
        return "ok", 0.0
    try:
        stats  = _load_stats()
        budget = _load_budget()
        today  = today_usage(stats)
        pct    = today["cost"] / budget["daily_cost_usd"] if budget["daily_cost_usd"] else 0
        if pct >= 1.0:
            return "blocked", today["cost"]
        if pct >= budget["warn_pct"] / 100:
            return "warn", today["cost"]
        return "ok", today["cost"]
    except Exception:
        return "ok", 0.0


def _log_run(entry: dict) -> None:
    """Append a run record to the unified run ledger."""
    import json
    with RUN_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


# -- Vector index -------------------------------------------------------------

def _get_vector_router():
    """Lazy-load vector_router; returns None if index not built."""
    try:
        from vector_router import query_agents, build_index
        return query_agents, build_index
    except ImportError:
        return None, None


def _find_agent(task: str, force_agent: str | None = None) -> dict | None:
    """
    Returns the best agent match dict:
        { agent, department, score, file_path, model, excerpt }
    Returns None if no index or no match.
    """
    if force_agent:
        # Search by name across all agent files
        for fp in AGENTS_DIR.rglob("*.md"):
            if fp.stem.lower() == force_agent.lower():
                dept = fp.parent.name
                return {
                    "agent": fp.stem,
                    "department": dept,
                    "score": 0.0,
                    "file_path": str(fp),
                    "model": "",
                    "excerpt": "",
                }
        print(f"  [run] Agent '{force_agent}' not found. Running without agent context.")
        return None

    query_agents, _ = _get_vector_router()
    if query_agents is None:
        return None

    try:
        hits = query_agents(task, n=1)
        return hits[0] if hits else None
    except RuntimeError:
        # Index not built yet
        return None


# -- Agent file → system prompt ------------------------------------------------

try:
    from prompt_cache import get_prompt as _cached_prompt, get_cached_system_param as _cached_system_param
    _HAS_PROMPT_CACHE = True
except ImportError:
    _HAS_PROMPT_CACHE = False


def _load_agent_prompt(file_path: str) -> str:
    """
    Return processed system prompt for an agent file.
    Uses prompt_cache (hash-based local cache) when available.
    Falls back to direct file read if prompt_cache not installed.
    """
    if _HAS_PROMPT_CACHE:
        return _cached_prompt(file_path)
    # Fallback: direct read + frontmatter strip
    fp = Path(file_path)
    if not fp.exists():
        return ""
    raw = fp.read_text(encoding="utf-8")
    if raw.startswith("---"):
        end = raw.find("---", 3)
        if end != -1:
            return raw[end + 3:].strip()
    return raw.strip()


def _get_system_param(file_path: str):
    """
    Return system prompt in the correct format for the Anthropic SDK.
    With prompt_cache: returns list[dict] with cache_control breakpoint
    (Anthropic API caches tokenization server-side — ~10x cheaper reads).
    Without prompt_cache: returns plain string.
    """
    if _HAS_PROMPT_CACHE:
        return _cached_system_param(file_path)
    return _load_agent_prompt(file_path)


# -- Ollama execution ----------------------------------------------------------

def _run_ollama(model: str, system: str, task: str) -> str:
    """Stream an Ollama response. Returns full output text."""
    import ollama
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": task})

    full = ""
    try:
        for chunk in ollama.chat(model=model, messages=messages, stream=True,
                                  options={"temperature": 0.3, "num_ctx": 4096}):
            tok = chunk["message"]["content"]
            print(tok, end="", flush=True)
            full += tok
    except Exception as e:
        print(f"\n[run] Ollama error: {e}")
    print()
    return full


# -- Claude execution ----------------------------------------------------------

def _run_claude(model_param: str, system, task: str) -> tuple[str, int, int]:
    """
    Stream a Claude response via Anthropic SDK. Returns (text, input_tokens, output_tokens).
    `system` can be a plain string OR a list[dict] with cache_control breakpoints
    (from _get_system_param). Both formats are accepted by the Anthropic SDK.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("[run] ERROR: ANTHROPIC_API_KEY not set.")
        return "", 0, 0

    model_id = CLAUDE_MODEL_MAP.get(model_param, CLAUDE_MODEL_MAP["sonnet"])
    client = anthropic.Anthropic(api_key=api_key)

    kwargs = {
        "model": model_id,
        "max_tokens": DEFAULT_MAX_TOKENS,
        "messages": [{"role": "user", "content": task}],
    }
    if system:
        kwargs["system"] = system

    full = ""
    input_tokens = output_tokens = 0
    try:
        with client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                print(text, end="", flush=True)
                full += text
            final = stream.get_final_message()
            input_tokens  = final.usage.input_tokens
            output_tokens = final.usage.output_tokens
    except anthropic.AuthenticationError:
        print("[run] Authentication failed. Check ANTHROPIC_API_KEY.")
    except anthropic.RateLimitError:
        print("[run] Rate limit hit. Try again in a moment.")
    except Exception as e:
        print(f"\n[run] Claude error: {e}")
    print()
    return full, input_tokens, output_tokens


# -- Main routing function -----------------------------------------------------

def run(task: str, force_agent: str | None = None, dry_run: bool = False) -> str:
    """
    Route a task through the AI OS:
    1. Classify complexity tier + model
    2. Budget gate (pre-execution)
    3. Find best agent via vector search
    4. Execute (Ollama or Claude SDK with agent system prompt)
    5. Log to run_log.jsonl
    Returns the output text.
    """
    import json
    from datetime import datetime, timezone
    t0 = time.time()
    ts = datetime.now(timezone.utc).isoformat()

    # Step 1: Classify tier + model
    decision = route(task)

    # Step 2: Budget gate
    bstatus, daily_cost = _budget_check(decision["cost_tier"])
    if bstatus == "blocked" and decision["backend"] == "claude":
        print(f"  [budget] Daily limit reached (${daily_cost:.4f}). Downgrading to Haiku.")
        decision["agent_param"] = "haiku"
        decision["model"]       = CLAUDE_MODELS["haiku"].model
        decision["cost_tier"]   = "low"
    elif bstatus == "warn":
        print(f"  [budget] Warning: ${daily_cost:.4f} spent today.")

    # Step 3: Find best agent
    agent_info = _find_agent(task, force_agent=force_agent)
    agent_name = agent_info["agent"] if agent_info else "Lead Orchestrator"
    dept       = agent_info["department"] if agent_info else "system"
    agent_file = agent_info["file_path"] if agent_info else None

    # Step 4: Load system prompt (cache_control format for Claude, plain string for Ollama)
    system_prompt = ""
    if agent_file:
        if decision["backend"] == "claude":
            system_prompt = _get_system_param(agent_file)
        else:
            system_prompt = _load_agent_prompt(agent_file)

    # Print routing header
    print(f"\n{'-'*60}")
    print(f"  AGENT  : {agent_name}  [{dept}]")
    print(f"  MODEL  : {decision['model']}  (tier {decision['tier']})")
    print(f"  REASON : {decision['reason']}")
    if agent_info and agent_info.get("score") is not None:
        print(f"  MATCH  : {agent_info['score']:.3f} similarity score")
    print(f"{'-'*60}\n")

    if dry_run:
        print("  [dry-run] Routing decision shown. No model was called.")
        return ""

    # Step 5: Execute
    output = ""
    input_tokens = output_tokens = 0
    error = None

    if decision["backend"] == "ollama":
        from model_router import is_model_available, resolve_local_model
        model = decision["model"]
        if not is_model_available(model):
            resolved, _ = resolve_local_model(model)
            if is_model_available(resolved):
                print(f"  [fallback] {model} → {resolved}\n")
                model = resolved
            else:
                error = f"Model '{model}' not installed. Run: ollama pull {model}"
                print(f"  [error] {error}")
        if not error:
            output = _run_ollama(model, system_prompt, task)
            if _HAS_RESOURCE_TRACKER and output:
                # Ollama doesn't return token counts — estimate from word count
                _est_in  = int(len(task.split()) * 1.3)
                _est_out = int(len(output.split()) * 1.3)
                _rt_record(model, "ollama", _est_in, _est_out, ts, agent_name)
    else:
        output, input_tokens, output_tokens = _run_claude(
            decision["agent_param"], system_prompt, task
        )
        if _HAS_RESOURCE_TRACKER and (input_tokens + output_tokens) > 0:
            _model_id = CLAUDE_MODEL_MAP.get(decision["agent_param"], decision["model"])
            _rt_record(_model_id, "claude", input_tokens, output_tokens, ts, agent_name)

    elapsed = round(time.time() - t0, 2)
    tok_str = f"  {input_tokens + output_tokens} tokens  |  " if input_tokens + output_tokens else ""
    print(f"\n{'-'*60}")
    print(f"  {tok_str}Done in {elapsed}s")
    print(f"{'-'*60}\n")

    # Step 6: Log
    _log_run({
        "ts":           ts,
        "prompt":       task[:120],
        "tier":         decision["tier"],
        "backend":      decision["backend"],
        "model":        decision["model"],
        "agent":        agent_name,
        "department":   dept,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "elapsed":      elapsed,
        "budget_status": bstatus,
        "error":        error,
    })

    # Post-run budget advisory
    if _HAS_TRACKER and decision["backend"] == "claude":
        bstatus2, daily2 = _budget_check(decision["cost_tier"])
        if bstatus2 in ("warn", "blocked"):
            print(f"  [budget] Post-run: ${daily2:.4f} spent today.\n")

    return output


# -- REPL ---------------------------------------------------------------------

def repl():
    """Interactive loop — type tasks, get routed responses."""
    print("\n  AI OS — Routing Loop")
    print("  Type a task to run. Commands: :rebuild :agents :quit\n")

    query_agents, build_index = _get_vector_router()

    while True:
        try:
            task = input("  > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Bye.")
            break

        if not task:
            continue
        if task in (":quit", ":q", "exit", "quit"):
            print("  Bye.")
            break
        if task == ":rebuild":
            if build_index:
                print("  Rebuilding vector index...")
                n = build_index()
                print(f"  {n} agents indexed.")
            else:
                print("  vector_router not available.")
            continue
        if task == ":agents":
            if query_agents:
                hits = query_agents(task, n=5)
                for h in hits:
                    print(f"    {h['agent']:<35} {h['department']}")
            continue

        run(task)


# -- CLI -----------------------------------------------------------------------

def _cmd_status() -> None:
    """Print today's spend + run log summary."""
    if _HAS_TRACKER:
        from token_tracker import cmd_today, _load_stats
        cmd_today(_load_stats())
    else:
        print("  token_tracker not available.")

    if RUN_LOG.exists():
        import json
        from datetime import date
        today_str = date.today().isoformat()
        lines = RUN_LOG.read_text(encoding="utf-8").splitlines()
        today_runs = []
        for l in lines:
            try:
                r = json.loads(l)
                if today_str in r.get("ts", ""):
                    today_runs.append(r)
            except Exception:
                pass
        if today_runs:
            claude_n = sum(1 for r in today_runs if r.get("backend") == "claude")
            ollama_n = sum(1 for r in today_runs if r.get("backend") == "ollama")
            print(f"  run_log   : {len(today_runs)} runs today ({claude_n} Claude, {ollama_n} Ollama)")
            from collections import Counter
            top = Counter(r["agent"] for r in today_runs if r.get("agent")).most_common(3)
            if top:
                print(f"  Top agents: {', '.join(f'{a}({n})' for a, n in top)}")
            print()


def _cmd_agents(task: str) -> None:
    """Show top 5 agents for a task without executing."""
    query_agents, _ = _get_vector_router()
    if not query_agents:
        print("vector_router not available. Run: python vector_router.py build")
        return
    try:
        hits = query_agents(task, n=5)
        if not hits:
            print("No results. Run: python vector_router.py build")
            return
        print(f"\n  Top agents for: \"{task[:60]}\"")
        print(f"  {'Agent':<35} {'Dept':<20} {'Score':>7}")
        print(f"  {'-'*65}")
        for h in hits:
            print(f"  {h['agent']:<35} {h['department']:<20} {h.get('score', 0):>7.4f}")
        print()
    except Exception as e:
        print(f"  vector_router error: {e}")


if __name__ == "__main__":
    args = sys.argv[1:]

    # Flags
    dry_run = "--dry-run" in args
    rebuild = "--rebuild" in args
    force_agent = None

    for i, a in enumerate(args):
        if a == "--agent" and i + 1 < len(args):
            force_agent = args[i + 1]

    # Strip flag args to find the task
    clean_args = [a for a in args if not a.startswith("--") and a != force_agent]

    if rebuild:
        _, build_index = _get_vector_router()
        if build_index:
            print("Rebuilding vector index...")
            n = build_index()
            print(f"Done. {n} agents indexed.")
        else:
            print("vector_router not available.")
        sys.exit(0)

    if clean_args and clean_args[0] == "status":
        _cmd_status()
        sys.exit(0)

    if clean_args and clean_args[0] == "agents" and len(clean_args) > 1:
        _cmd_agents(clean_args[1])
        sys.exit(0)

    if not clean_args:
        # No task given — drop into interactive REPL
        repl()
        sys.exit(0)

    task = clean_args[0]

    # Tier 0 → fast single-agent path (Ollama, no governance overhead)
    # Tier 1+ → chain.py governance path (COO decompose, C-suite chain, synthesis)
    # --agent flag bypasses chain (explicit agent override = user knows what they want)
    if not force_agent:
        from model_router import route as _route_check
        _tier = _route_check(task)["tier"]
        if _tier >= 1:
            from chain import run_chain
            run_chain(task, dry_run=dry_run)
            sys.exit(0)

    run(task, force_agent=force_agent, dry_run=dry_run)
