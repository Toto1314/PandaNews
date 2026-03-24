"""
Model Router
============
Classifies task complexity and routes to the right model.

Tier 0 (Trivial)  → Ollama local by default (free)
Tier 1 (Simple)   → Claude Haiku (cheap) or local
Tier 2 (Standard) → Claude Sonnet or local
Tier 3 (Complex)  → Claude Sonnet (local only for code)
Tier 4 (Critical) → Claude Opus only

Usage
-----
    from model_router import route, verify_local_models

    decision = route("summarize this doc")
    decision = route("design a zero-trust architecture")
    verify_local_models()   # check which Ollama models are installed

CLI
---
    python model_router.py "your task"
    python model_router.py "format this" --no-tools
    python model_router.py "refactor auth" --prefer-local
    python model_router.py table
    python model_router.py verify
"""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from typing import Optional


# ── Model registry ─────────────────────────────────────────────────────────────

@dataclass
class ModelConfig:
    backend: str
    model: str
    agent_param: str        # for Claude Agent tool model= param
    supports_tools: bool
    context_k: int
    cost_tier: str          # "free" | "low" | "medium" | "high"
    notes: str


OLLAMA_MODELS: dict[str, ModelConfig] = {
    "gemma3:1b": ModelConfig(
        backend="ollama", model="gemma3:1b", agent_param="",
        supports_tools=False, context_k=8, cost_tier="free",
        notes="Fastest local. No tools. Format/translate/classify only.",
    ),
    "gemma2:2b-instruct-q4_K_M": ModelConfig(
        backend="ollama", model="gemma2:2b-instruct-q4_K_M", agent_param="",
        supports_tools=False, context_k=8, cost_tier="free",
        notes="Tiny. Very short simple tasks only.",
    ),
    "gemma3:4b": ModelConfig(
        backend="ollama", model="gemma3:4b", agent_param="",
        supports_tools=False, context_k=128, cost_tier="free",
        notes="Good local general use. No tools.",
    ),
    "gemma3:latest": ModelConfig(
        backend="ollama", model="gemma3:latest", agent_param="",
        supports_tools=False, context_k=128, cost_tier="free",
        notes="Alias for gemma3:4b.",
    ),
    "gemma:latest": ModelConfig(
        backend="ollama", model="gemma:latest", agent_param="",
        supports_tools=False, context_k=8, cost_tier="free",
        notes="9B legacy gemma. Prefer gemma3 variants.",
    ),
    "llama3.2:3b": ModelConfig(
        backend="ollama", model="llama3.2:3b", agent_param="",
        supports_tools=True, context_k=128, cost_tier="free",
        notes="Small, fast, tool-capable. Tier 0-1 agentic tasks.",
    ),
    "llama3.1:latest": ModelConfig(
        backend="ollama", model="llama3.1:latest", agent_param="",
        supports_tools=True, context_k=128, cost_tier="free",
        notes="8B, solid tool use. Tier 2 substitute on budget.",
    ),
    "mistral:7b-instruct": ModelConfig(
        backend="ollama", model="mistral:7b-instruct", agent_param="",
        supports_tools=False, context_k=32, cost_tier="free",
        notes="Good instruction following. Unreliable tool calling.",
    ),
    "qwen2.5-coder:7b": ModelConfig(
        backend="ollama", model="qwen2.5-coder:7b", agent_param="",
        supports_tools=True, context_k=128, cost_tier="free",
        notes="Best local coding model. Tool calling works.",
    ),
    "deepseek-coder-v2:16b": ModelConfig(
        backend="ollama", model="deepseek-coder-v2:16b", agent_param="",
        supports_tools=True, context_k=128, cost_tier="free",
        notes="16B coding specialist. Best local for complex code.",
    ),
    "deepseek-r1:latest": ModelConfig(
        backend="ollama", model="deepseek-r1:latest", agent_param="",
        supports_tools=False, context_k=128, cost_tier="free",
        notes="Reasoning/chain-of-thought. No tools. Math/logic.",
    ),
    "phi3:medium": ModelConfig(
        backend="ollama", model="phi3:medium", agent_param="",
        supports_tools=False, context_k=128, cost_tier="free",
        notes="14B, good reasoning. No reliable tool calling.",
    ),
    "llava:7b": ModelConfig(
        backend="ollama", model="llava:7b", agent_param="",
        supports_tools=False, context_k=4, cost_tier="free",
        notes="Vision model. Use for image inputs.",
    ),
}

CLAUDE_MODELS: dict[str, ModelConfig] = {
    "haiku": ModelConfig(
        backend="claude", model="claude-haiku-4-5-20251001", agent_param="haiku",
        supports_tools=True, context_k=200, cost_tier="low",
        notes="$0.80/$4 per MTok. Fast. Tier 1-2.",
    ),
    "sonnet": ModelConfig(
        backend="claude", model="claude-sonnet-4-6", agent_param="sonnet",
        supports_tools=True, context_k=200, cost_tier="medium",
        notes="$3/$15 per MTok. Default workhorse.",
    ),
    "opus": ModelConfig(
        backend="claude", model="claude-opus-4-6", agent_param="opus",
        supports_tools=True, context_k=200, cost_tier="high",
        notes="$15/$75 per MTok. Tier 4 critical only.",
    ),
}

# Fallback chain: if preferred model is unavailable, try these in order
FALLBACK_CHAIN: dict[str, list[str]] = {
    "gemma3:1b":             ["gemma2:2b-instruct-q4_K_M", "gemma3:4b"],
    "llama3.2:3b":           ["llama3.1:latest", "qwen2.5-coder:7b"],
    "gemma3:4b":             ["gemma3:latest", "llama3.2:3b"],
    "qwen2.5-coder:7b":      ["deepseek-coder-v2:16b", "llama3.1:latest"],
    "deepseek-coder-v2:16b": ["qwen2.5-coder:7b", "llama3.1:latest"],
    "deepseek-r1:latest":    ["phi3:medium", "llama3.1:latest"],
    "llama3.1:latest":       ["qwen2.5-coder:7b", "llama3.2:3b"],
}


# ── Ollama availability ────────────────────────────────────────────────────────

_installed_cache: set[str] | None = None


def _get_installed_models() -> set[str]:
    global _installed_cache
    if _installed_cache is not None:
        return _installed_cache
    try:
        out = subprocess.check_output(
            ["ollama", "list"], text=True, timeout=5,
            stderr=subprocess.DEVNULL
        )
        installed = set()
        for line in out.splitlines()[1:]:  # skip header
            parts = line.split()
            if parts:
                installed.add(parts[0])
        _installed_cache = installed
        return installed
    except Exception:
        _installed_cache = set()
        return set()


def is_model_available(model_name: str) -> bool:
    installed = _get_installed_models()
    # Exact match or prefix match (e.g. "gemma3:1b" in "gemma3:1b-instruct-q4")
    return any(
        model_name == m or m.startswith(model_name.split(":")[0] + ":")
        for m in installed
    )


def resolve_local_model(preferred: str) -> tuple[str, bool]:
    """
    Returns (model_name, is_fallback).
    Tries preferred first, then walks FALLBACK_CHAIN.
    Returns (preferred, False) if available, (fallback, True) if not.
    """
    if is_model_available(preferred):
        return preferred, False
    for fallback in FALLBACK_CHAIN.get(preferred, []):
        if is_model_available(fallback):
            return fallback, True
    return preferred, False  # let caller handle unavailability


def verify_local_models() -> dict[str, bool]:
    """Check which registered Ollama models are installed."""
    return {name: is_model_available(name) for name in OLLAMA_MODELS}


# ── Complexity classifier ──────────────────────────────────────────────────────

TIER_SIGNALS: list[tuple[int, list[str]]] = [
    (0, [
        "format", "translate", "reformat", "convert", "count", "spell check",
        "grammar", "fix typos", "summarize this", "tldr", "tl;dr",
        "what is ", "define ", "list all", "simple question",
    ]),
    (1, [
        "summarize", "explain", "describe", "draft", "write a", "extract",
        "find all", "what are", "how do i", "quick", "simple", "short",
        "brief", "lookup", "what does",
    ]),
    (2, [
        "analyze", "implement", "build", "create", "refactor", "debug",
        "research", "compare", "evaluate", "review", "optimize", "fix bug",
        "generate", "add feature", "write function", "write script",
        "data pipeline", "dashboard", "write test",
    ]),
    (3, [
        "architect", "design system", "multi-file", "security review",
        "threat model", "audit", "complex", "enterprise", "scalable",
        "distributed", "microservice", "infrastructure", "compliance",
        "penetration", "vulnerability", "database schema", "api design",
        "system design",
    ]),
    (4, [
        "governance", "critical incident", "breach", "existential",
        "legal", "regulatory", "ciso", "sox", "gdpr", "hipaa",
        "financial report", "board", "acquisition", "merger",
        "strategic decision", "catastrophic",
    ]),
]

CODE_KEYWORDS   = ["code", "python", "javascript", "typescript", "function",
                   "class", "bug", "script", "api", "sql", "refactor",
                   "compile", "test", "implement", "debug", "syntax", "import"]
VISION_KEYWORDS = ["image", "screenshot", "photo", "picture", "visual", "diagram"]
REASON_KEYWORDS = ["reason", "logic", "math", "proof", "calculate", "derive", "theorem"]


def _detect_domain(task: str) -> str:
    t = task.lower()
    if any(k in t for k in VISION_KEYWORDS):
        return "vision"
    if any(k in t for k in REASON_KEYWORDS):
        return "reasoning"
    if any(k in t for k in CODE_KEYWORDS):
        return "code"
    return "general"


def classify(task: str) -> tuple[int, list[str]]:
    """
    Returns (tier, matched_keywords) for observability.
    """
    t = task.lower()
    max_tier = 0
    matched: list[str] = []

    for tier, keywords in TIER_SIGNALS:
        hits = [k for k in keywords if k in t]
        if hits:
            if tier > max_tier:
                max_tier = tier
                matched = hits
            elif tier == max_tier:
                matched.extend(hits)

    words = len(task.split())
    length_boost = ""
    if words > 100 and max_tier < 2:
        max_tier = 2
        length_boost = f"(length>{words}w)"
    elif words > 50 and max_tier < 1:
        max_tier = 1
        length_boost = f"(length>{words}w)"

    if length_boost:
        matched.append(length_boost)

    return max_tier, matched


def route(
    task: str,
    prefer_local: bool = False,
    needs_tools: bool = True,
    force_tier: Optional[int] = None,
) -> dict:
    """
    Classify task and return routing decision.

    Key behaviour change from v1:
      - Tier 0 now defaults to Ollama regardless of prefer_local.
        Pass prefer_local=False and you still get local for trivial tasks.
      - prefer_local promotes Tier 1-2 to Ollama as well.
      - Fallback chain applied automatically when preferred model is unavailable.
    """
    tier, matched_keywords = (
        (force_tier, ["forced"]) if force_tier is not None
        else classify(task)
    )
    domain   = _detect_domain(task)
    fallback = False
    cfg      = None

    if tier == 0:
        # Always local for trivial — saves tokens, fast enough
        preferred = "llama3.2:3b" if needs_tools else "gemma3:1b"
        resolved, fallback = resolve_local_model(preferred)
        if is_model_available(resolved):
            cfg = OLLAMA_MODELS.get(resolved, OLLAMA_MODELS[preferred])
            reason = f"Tier 0: always local. {'Tool-capable' if needs_tools else 'No tools'} model."
        else:
            cfg = CLAUDE_MODELS["haiku"]
            reason = f"Tier 0: preferred local ({preferred}) not installed, falling back to Haiku."

    elif tier == 1:
        if prefer_local:
            preferred = "llama3.2:3b" if needs_tools else "gemma3:4b"
            resolved, fallback = resolve_local_model(preferred)
            cfg = OLLAMA_MODELS.get(resolved, CLAUDE_MODELS["haiku"])
            reason = f"Tier 1: local preferred."
        else:
            cfg = CLAUDE_MODELS["haiku"]
            reason = "Tier 1: Haiku is cost-effective and sufficient."

    elif tier == 2:
        if prefer_local:
            preferred = (
                "qwen2.5-coder:7b"  if domain == "code"      else
                "deepseek-r1:latest" if domain == "reasoning" else
                "llama3.1:latest"
            )
            resolved, fallback = resolve_local_model(preferred)
            cfg = OLLAMA_MODELS.get(resolved, CLAUDE_MODELS["sonnet"])
            reason = f"Tier 2: local preferred. Domain: {domain}."
        else:
            cfg = CLAUDE_MODELS["sonnet"]
            reason = "Tier 2: Sonnet default."

    elif tier == 3:
        if prefer_local and domain == "code":
            preferred = "deepseek-coder-v2:16b"
            resolved, fallback = resolve_local_model(preferred)
            cfg = OLLAMA_MODELS.get(resolved, CLAUDE_MODELS["sonnet"])
            reason = f"Tier 3 code: local preferred ({resolved})."
        else:
            cfg = CLAUDE_MODELS["sonnet"]
            reason = "Tier 3: Sonnet. Architecture/multi-file/security tasks."

    else:  # tier 4
        cfg = CLAUDE_MODELS["opus"]
        reason = "Tier 4: Opus only. Critical/governance — no local substitute."

    return {
        "tier":             tier,
        "backend":          cfg.backend,
        "model":            cfg.model,
        "agent_param":      cfg.agent_param,
        "supports_tools":   cfg.supports_tools,
        "cost_tier":        cfg.cost_tier,
        "reason":           reason,
        "domain":           domain,
        "prefer_local":     prefer_local,
        "matched_keywords": matched_keywords,
        "used_fallback":    fallback,
    }


# ── CLI ────────────────────────────────────────────────────────────────────────

def _print_table() -> None:
    print("\n  Model Routing Table")
    print(f"  {'Tier':<6} {'Condition':<35} {'Default':<32} {'Local --prefer-local':<30} Cost")
    print("  " + "-" * 115)
    rows = [
        (0, "Trivial, no tools",        "gemma3:1b (ollama)",          "gemma3:1b",              "free"),
        (0, "Trivial, needs tools",      "llama3.2:3b (ollama)",        "llama3.2:3b",            "free"),
        (1, "Simple Q&A / extraction",   "claude-haiku-4-5",            "gemma3:4b / llama3.2:3b","low"),
        (2, "Standard code",             "claude-sonnet-4-6",           "qwen2.5-coder:7b",       "free/med"),
        (2, "Standard general",          "claude-sonnet-4-6",           "llama3.1:latest",        "free/med"),
        (2, "Reasoning / math",          "claude-sonnet-4-6",           "deepseek-r1:latest",     "free/med"),
        (3, "Complex code/arch",         "claude-sonnet-4-6",           "deepseek-coder-v2:16b",  "free/med"),
        (3, "Security / compliance",     "claude-sonnet-4-6",           "(none)",                 "med"),
        (4, "Governance / legal / crit", "claude-opus-4-6",             "(none)",                 "high"),
    ]
    for tier, cond, default, local, cost in rows:
        print(f"  {tier:<6} {cond:<35} {default:<32} {local:<30} {cost}")
    print("\n  Tier 0 ALWAYS routes to Ollama by default (no prefer_local flag needed).")
    print("  Tiers 1-3 require --prefer-local to use Ollama.\n")


def _print_verify() -> None:
    status = verify_local_models()
    installed = _get_installed_models()
    print(f"\n  Installed Ollama models: {', '.join(sorted(installed)) or '(none)'}\n")
    print(f"  {'Model':<35} {'Available':<12} Notes")
    print(f"  {'-'*80}")
    for name, avail in sorted(status.items()):
        cfg = OLLAMA_MODELS[name]
        mark = "YES" if avail else "NO "
        print(f"  {name:<35} {mark:<12} {cfg.notes[:45]}")
    print()


if __name__ == "__main__":
    args = sys.argv[1:]

    if not args or args[0] == "table":
        _print_table()
        sys.exit(0)

    if args[0] == "verify":
        _print_verify()
        sys.exit(0)

    task         = args[0]
    prefer_local = "--prefer-local" in args or "--local" in args
    needs_tools  = "--no-tools" not in args
    force_tier   = None

    for i, a in enumerate(args):
        if a == "--tier" and i + 1 < len(args):
            force_tier = int(args[i + 1])

    d = route(task, prefer_local=prefer_local, needs_tools=needs_tools, force_tier=force_tier)
    tier_names = ["Trivial", "Simple", "Standard", "Complex", "Critical"]

    print(f"\n  Task     : {task[:80]}")
    print(f"  Tier     : {d['tier']}  ({tier_names[d['tier']]})")
    print(f"  Domain   : {d['domain']}")
    print(f"  Keywords : {', '.join(d['matched_keywords']) or '(none — length heuristic)'}")
    print(f"  Backend  : {d['backend']}")
    print(f"  Model    : {d['model']}")
    print(f"  Fallback : {'yes' if d['used_fallback'] else 'no'}")
    print(f"  Cost     : {d['cost_tier']}")
    print(f"  Reason   : {d['reason']}")
    if d["backend"] == "claude":
        print(f"  Agent param: model=\"{d['agent_param']}\"")
    print()
