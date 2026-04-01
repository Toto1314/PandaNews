"""
prompt_cache.py — Hash-Based Prompt Cache with Anthropic API Cache Breakpoints
===============================================================================
Two-layer caching:

  Layer 1 (local): Reads agent .md files once, strips frontmatter, stores the
                   processed system prompt in ~/.claude/prompt_cache/.
                   Hash of source file = cache key. Source changes → auto-invalidate.

  Layer 2 (API):   Returns the prompt pre-wrapped in Anthropic's cache_control
                   format. When passed as `system=` to the Anthropic SDK, the
                   API caches tokenization server-side across calls with the
                   same content — charges cache_read rate (~10x cheaper) instead
                   of full input rate.

Usage
-----
    from prompt_cache import get_prompt, get_cached_system_param, invalidate, clear_all

    # Get plain string (for Ollama or non-caching use)
    prompt = get_prompt("/path/to/Agent.md")

    # Get Anthropic SDK-ready system param with cache_control baked in
    system_param = get_cached_system_param("/path/to/Agent.md")
    # → [{"type": "text", "text": "...", "cache_control": {"type": "ephemeral"}}]

    # Invalidate one agent's cache
    invalidate("Investment-Analyst")

    # Nuke everything
    clear_all()

CLI
---
    python prompt_cache.py stats              # show cache state
    python prompt_cache.py warm <agent_dir>   # pre-warm all agents in a dir
    python prompt_cache.py invalidate <name>  # force-invalidate one agent
    python prompt_cache.py clear              # delete all cache files
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ── Paths ─────────────────────────────────────────────────────────────────────

CACHE_DIR   = Path.home() / ".claude" / "prompt_cache"
AGENTS_DIR  = Path.home() / ".claude" / "agents"

CACHE_DIR.mkdir(parents=True, exist_ok=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _strip_frontmatter(raw: str) -> str:
    """Remove YAML frontmatter block (--- ... ---) and return body."""
    if raw.startswith("---"):
        end = raw.find("---", 3)
        if end != -1:
            return raw[end + 3:].strip()
    return raw.strip()


def _cache_path(agent_name: str) -> Path:
    return CACHE_DIR / f"{agent_name}.cache.json"


def _agent_name_from_path(file_path: str) -> str:
    return Path(file_path).stem


# ── Core cache operations ─────────────────────────────────────────────────────

def get_prompt(file_path: str) -> str:
    """
    Return processed system prompt for an agent file.
    Reads from local cache if source is unchanged (hash match).
    Regenerates and writes cache if source changed or cache missing.
    """
    fp = Path(file_path)
    if not fp.exists():
        return ""

    raw = fp.read_text(encoding="utf-8")
    current_hash = _sha256(raw)
    agent_name = _agent_name_from_path(file_path)
    cache_file = _cache_path(agent_name)

    # Cache hit: source unchanged
    if cache_file.exists():
        try:
            cached = json.loads(cache_file.read_text(encoding="utf-8"))
            if cached.get("source_hash") == current_hash:
                return cached["prompt"]
        except (json.JSONDecodeError, KeyError):
            pass  # corrupt cache — regenerate

    # Cache miss or stale: process and store
    processed = _strip_frontmatter(raw)
    entry = {
        "agent":       agent_name,
        "source_path": str(fp),
        "source_hash": current_hash,
        "cached_at":   datetime.now(timezone.utc).isoformat(),
        "prompt":      processed,
    }
    cache_file.write_text(json.dumps(entry, indent=2), encoding="utf-8")
    return processed


def get_cached_system_param(file_path: str) -> list[dict] | str:
    """
    Return the system prompt in Anthropic SDK cache_control format.
    Pass this directly as `system=` to client.messages.create() or
    client.messages.stream().

    Returns a list[dict] with cache_control breakpoint when content is
    non-empty, or a plain string "" when agent file is missing/empty.

    The cache_control type "ephemeral" tells Anthropic to cache this
    content server-side. Subsequent calls with the same content are
    billed at the cache_read rate (~10x cheaper than full input).
    """
    prompt = get_prompt(file_path)
    if not prompt:
        return ""

    return [
        {
            "type": "text",
            "text": prompt,
            "cache_control": {"type": "ephemeral"},
        }
    ]


# ── Invalidation ──────────────────────────────────────────────────────────────

def invalidate(agent_name: str) -> bool:
    """Delete cache file for one agent. Returns True if found and deleted."""
    cache_file = _cache_path(agent_name)
    if cache_file.exists():
        cache_file.unlink()
        return True
    return False


def clear_all() -> int:
    """Delete all cache files. Returns count deleted."""
    files = list(CACHE_DIR.glob("*.cache.json"))
    for f in files:
        f.unlink()
    return len(files)


# ── Stats ─────────────────────────────────────────────────────────────────────

def stats() -> list[dict]:
    """Return list of cache entry metadata (no prompt text)."""
    result = []
    for f in sorted(CACHE_DIR.glob("*.cache.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            source = Path(data.get("source_path", ""))
            # Check if source still matches
            stale = True
            if source.exists():
                current_hash = _sha256(source.read_text(encoding="utf-8"))
                stale = current_hash != data.get("source_hash", "")
            result.append({
                "agent":     data.get("agent", f.stem),
                "cached_at": data.get("cached_at", "")[:19],
                "prompt_len": len(data.get("prompt", "")),
                "stale":     stale,
                "cache_file": str(f),
            })
        except Exception:
            pass
    return result


# ── Warm cache (pre-build all agents) ─────────────────────────────────────────

def warm(agent_dir: Optional[str] = None) -> int:
    """
    Pre-warm cache for all agent .md files in a directory.
    Defaults to ~/.claude/agents/. Returns count of agents cached.
    """
    base = Path(agent_dir) if agent_dir else AGENTS_DIR
    count = 0
    for md in base.rglob("*.md"):
        try:
            result = get_prompt(str(md))
            if result:
                count += 1
        except Exception:
            pass
    return count


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    args = sys.argv[1:]

    if not args or args[0] == "stats":
        entries = stats()
        if not entries:
            print("  Cache is empty. Run: python prompt_cache.py warm")
        else:
            print(f"\n  {'Agent':<40} {'Cached At':<22} {'Chars':>7} {'Status'}")
            print(f"  {'-'*80}")
            for e in entries:
                status = "STALE" if e["stale"] else "OK"
                print(f"  {e['agent']:<40} {e['cached_at']:<22} {e['prompt_len']:>7}  {status}")
            fresh = sum(1 for e in entries if not e["stale"])
            stale = sum(1 for e in entries if e["stale"])
            print(f"\n  {len(entries)} cached  |  {fresh} fresh  |  {stale} stale\n")

    elif args[0] == "warm":
        d = args[1] if len(args) > 1 else None
        print(f"  Warming cache for {'all agents' if not d else d}...")
        n = warm(d)
        print(f"  {n} agents cached.\n")

    elif args[0] == "invalidate" and len(args) > 1:
        name = args[1]
        deleted = invalidate(name)
        print(f"  {'Deleted cache for ' + name if deleted else name + ' not found in cache.'}")

    elif args[0] == "clear":
        n = clear_all()
        print(f"  Deleted {n} cache files.")

    else:
        print("Commands: stats | warm [dir] | invalidate <agent_name> | clear")
