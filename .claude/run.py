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

import anthropic
from model_router import route

# -- Constants ----------------------------------------------------------------

CLAUDE_MODEL_MAP = {
    "haiku":  "claude-haiku-4-5-20251001",
    "sonnet": "claude-sonnet-4-6",
    "opus":   "claude-opus-4-6",
}
DEFAULT_MAX_TOKENS = 4096
AGENTS_DIR = Path.home() / ".claude" / "agents"


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

def _load_agent_prompt(file_path: str) -> str:
    """Read an agent .md file and return its body (after frontmatter) as system prompt."""
    fp = Path(file_path)
    if not fp.exists():
        return ""
    raw = fp.read_text(encoding="utf-8")
    # Strip YAML frontmatter block
    if raw.startswith("---"):
        end = raw.find("---", 3)
        if end != -1:
            return raw[end + 3:].strip()
    return raw.strip()


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

def _run_claude(model_param: str, system: str, task: str) -> str:
    """Stream a Claude response via Anthropic SDK. Returns full output text."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("[run] ERROR: ANTHROPIC_API_KEY not set.")
        return ""

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
    try:
        with client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                print(text, end="", flush=True)
                full += text
    except anthropic.AuthenticationError:
        print("[run] Authentication failed. Check ANTHROPIC_API_KEY.")
    except anthropic.RateLimitError:
        print("[run] Rate limit hit. Try again in a moment.")
    except Exception as e:
        print(f"\n[run] Claude error: {e}")
    print()
    return full


# -- Main routing function -----------------------------------------------------

def run(task: str, force_agent: str | None = None, dry_run: bool = False) -> str:
    """
    Route a task through the AI OS:
    1. Find best agent via vector search
    2. Classify complexity tier
    3. Route to Ollama or Claude with agent system prompt
    Returns the output text.
    """
    t0 = time.time()

    # Step 1: Find best agent
    agent_info = _find_agent(task, force_agent=force_agent)
    agent_name = agent_info["agent"] if agent_info else "Lead Orchestrator"
    dept = agent_info["department"] if agent_info else "system"
    agent_file = agent_info["file_path"] if agent_info else None

    # Step 2: Classify tier + model
    decision = route(task)

    # Step 3: Load system prompt
    system_prompt = ""
    if agent_file:
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

    # Step 4: Execute
    if decision["backend"] == "ollama":
        import ollama as _ollama_module
        from model_router import is_model_available, resolve_local_model
        model = decision["model"]
        if not is_model_available(model):
            resolved, _ = resolve_local_model(model)
            if is_model_available(resolved):
                print(f"  [fallback] {model} → {resolved}\n")
                model = resolved
            else:
                print(f"  [error] Model '{model}' not installed. Run: ollama pull {model}")
                return ""
        output = _run_ollama(model, system_prompt, task)
    else:
        output = _run_claude(decision["agent_param"], system_prompt, task)

    elapsed = time.time() - t0
    print(f"\n{'-'*60}")
    print(f"  Done in {elapsed:.1f}s")
    print(f"{'-'*60}\n")

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

    if not clean_args:
        # No task given — drop into interactive REPL
        repl()
        sys.exit(0)

    task = clean_args[0]
    run(task, force_agent=force_agent, dry_run=dry_run)
