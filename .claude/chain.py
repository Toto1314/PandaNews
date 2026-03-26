#!/usr/bin/env python3
"""
chain.py — AI OS Multi-Agent Chain Executor
=============================================
Follows the routing logic in CLAUDE.md:
  - Single-dept task  → run() directly with best-match agent
  - Multi-dept task   → COO decomposes → fan out to dept agents → synthesize

Usage
-----
    python chain.py "research OpenAI threats, build a counter-strategy, and identify investment plays"
    python chain.py "we have a security incident on prod"
    python chain.py --dry-run "your task"

How it works
------------
    1. Intake: classify as single or multi-department
    2. If multi → COO produces a JSON work plan
    3. Each subtask routes to its dept agent via vector search
    4. Results collected, then synthesized by Lead Orchestrator
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".claude"))

# Load .env from ~/.claude/.env if present
_env_file = Path.home() / ".claude" / ".env"
if _env_file.exists():
    for _line in _env_file.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

import anthropic
from run import run, _find_agent, _load_agent_prompt, _run_claude, CLAUDE_MODEL_MAP

AGENTS_DIR = Path.home() / ".claude" / "agents"

# Multi-department signal keywords — if 2+ clusters hit, route through COO
MULTI_DEPT_SIGNALS = [
    ["security", "breach", "incident", "vulnerability", "ciso"],
    ["research", "analyze", "competitive", "market", "trends"],
    ["strategy", "plan", "positioning", "gtm", "launch"],
    ["invest", "portfolio", "stock", "equity", "buy", "sell"],
    ["hire", "recruit", "people", "team", "headcount", "hr"],
    ["build", "implement", "code", "deploy", "engineer"],
    ["data", "analytics", "dashboard", "metric", "pipeline"],
    ["finance", "budget", "cost", "revenue", "forecast"],
    ["comms", "press", "announce", "messaging", "pr"],
]


def _count_domain_hits(task: str) -> int:
    """Count how many domain clusters have at least one keyword hit."""
    task_lower = task.lower()
    return sum(
        1 for cluster in MULTI_DEPT_SIGNALS
        if any(kw in task_lower for kw in cluster)
    )


def is_multi_dept(task: str) -> bool:
    """True if task spans 2+ department domains."""
    return _count_domain_hits(task) >= 2


# ── COO decomposition ─────────────────────────────────────────────────────────

COO_DECOMPOSE_PROMPT = """\
You are the COO of an AI operating system. A task has come in that spans multiple departments.
Your job: decompose it into a clean work plan.

TASK: {task}

Output ONLY a JSON array. Each item has:
  - "dept": department name (security, engineering, strategy, research, investments, hr, finance, data, gtm, comms, pmo, design, ai-ml, devops, legal, audit, product, prompt-eng)
  - "agent": specific agent name to handle it (e.g. "CISO", "CSO-Strategy", "CIO-Investments")
  - "task": the scoped subtask for that agent — specific, not vague
  - "depends_on": list of dept names this step must wait for (empty list if none)
  - "priority": 1 (do first) to 5 (do last)

Rules:
- Maximum 4 subtasks. Focus on what matters most.
- Each subtask must be independently executable by one agent.
- Security tasks always get priority 1.
- If synthesis is needed, add a final subtask with agent "Lead-Orchestrator".

Output JSON only. No explanation. No markdown fences.
"""


def decompose_with_coo(task: str) -> list[dict]:
    """
    Call COO to decompose a multi-dept task into a structured work plan.
    Returns list of subtask dicts.
    """
    coo_file = AGENTS_DIR / "c-suite" / "COO.md"
    system_prompt = _load_agent_prompt(str(coo_file)) if coo_file.exists() else ""

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("[chain] ANTHROPIC_API_KEY not set — using simple decomposition")
        return _simple_decompose(task)

    client = anthropic.Anthropic(api_key=api_key)
    prompt = COO_DECOMPOSE_PROMPT.format(task=task)

    try:
        resp = client.messages.create(
            model=CLAUDE_MODEL_MAP["sonnet"],
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.content[0].text.strip()

        # Strip markdown fences if model included them anyway
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        plan = json.loads(raw)
        return sorted(plan, key=lambda x: x.get("priority", 3))

    except (json.JSONDecodeError, IndexError) as e:
        print(f"[chain] COO returned unparseable JSON ({e}) — using fallback")
        return _simple_decompose(task)
    except Exception as e:
        print(f"[chain] COO call failed ({e}) — using fallback")
        return _simple_decompose(task)


def _simple_decompose(task: str) -> list[dict]:
    """Fallback: use vector search to find top 3 agents and assign them."""
    try:
        from vector_router import query_agents
        hits = query_agents(task, n=3)
        return [
            {
                "dept": h["department"],
                "agent": h["agent"],
                "task": task,
                "depends_on": [],
                "priority": i + 1,
            }
            for i, h in enumerate(hits)
        ]
    except Exception:
        return []


# ── Chain executor ────────────────────────────────────────────────────────────

SYNTHESIS_PROMPT = """\
You are the Lead Orchestrator of an AI operating system.
Multiple department agents have completed their work on this task:

ORIGINAL TASK: {task}

DEPARTMENT OUTPUTS:
{outputs}

Synthesize these into a single, coherent executive response for the CEO.
- Lead with the key insight or decision
- Surface any conflicts or risks between department findings
- End with a clear recommended next action
"""


def synthesize(task: str, results: list[dict]) -> str:
    """Call Lead Orchestrator to synthesize all dept outputs into one response."""
    outputs_text = ""
    for r in results:
        outputs_text += f"\n[{r['agent']} — {r['dept']}]\n{r['output']}\n"

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return "\n\n".join(r["output"] for r in results)

    client = anthropic.Anthropic(api_key=api_key)
    prompt = SYNTHESIS_PROMPT.format(task=task, outputs=outputs_text)

    print("\n  [Synthesizing across departments...]\n")
    full = ""
    try:
        with client.messages.stream(
            model=CLAUDE_MODEL_MAP["sonnet"],
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            for text in stream.text_stream:
                print(text, end="", flush=True)
                full += text
    except Exception as e:
        print(f"[chain] Synthesis error: {e}")
    print()
    return full


def run_chain(task: str, dry_run: bool = False) -> str:
    """
    Main entry point. Routes single or multi-dept tasks appropriately.
    """
    t0 = time.time()
    multi = is_multi_dept(task)
    domain_hits = _count_domain_hits(task)

    print(f"\n{'='*60}")
    print(f"  TASK     : {task[:80]}{'...' if len(task) > 80 else ''}")
    print(f"  ROUTING  : {'MULTI-DEPT (COO)' if multi else 'SINGLE-DEPT'}")
    print(f"  SIGNALS  : {domain_hits} domain cluster(s) detected")
    print(f"{'='*60}")

    # Single-dept: just run directly
    if not multi:
        return run(task, dry_run=dry_run)

    # Multi-dept: COO decompose → fan out → synthesize
    print("\n  [COO] Decomposing task into department work plan...")
    plan = decompose_with_coo(task)

    if not plan:
        print("  [chain] No subtasks generated — falling back to single-agent run")
        return run(task, dry_run=dry_run)

    print(f"\n  WORK PLAN ({len(plan)} subtasks):")
    for step in plan:
        deps = f" (after: {', '.join(step['depends_on'])})" if step.get("depends_on") else ""
        print(f"    {step['priority']}. [{step['dept']}] {step['agent']} — {step['task'][:60]}{deps}")
    print()

    if dry_run:
        print("  [dry-run] Plan shown. No agents were called.")
        return ""

    # Execute each subtask in priority order
    results = []
    completed_depts = set()

    for step in plan:
        agent_name = step.get("agent", "")
        dept = step.get("dept", "")
        subtask = step.get("task", task)
        depends_on = step.get("depends_on", [])

        # Skip synthesis step — handled separately after all depts run
        if agent_name in ("Lead-Orchestrator", "Lead Orchestrator"):
            continue

        # Check dependencies
        if depends_on:
            missing = [d for d in depends_on if d not in completed_depts]
            if missing:
                print(f"  [chain] WARNING: {agent_name} depends on {missing} which haven't completed. Running anyway.")

        print(f"\n  [{dept.upper()}] Running {agent_name}...")
        print(f"  Task: {subtask[:80]}\n")

        # Find the agent file
        agent_info = _find_agent(subtask, force_agent=agent_name)
        if not agent_info:
            # Fallback: vector search on the subtask
            agent_info = _find_agent(subtask)

        system_prompt = ""
        if agent_info and agent_info.get("file_path"):
            system_prompt = _load_agent_prompt(agent_info["file_path"])
            actual_agent = agent_info["agent"]
        else:
            actual_agent = agent_name

        output = _run_claude("sonnet", system_prompt, subtask)
        results.append({
            "agent": actual_agent,
            "dept": dept,
            "task": subtask,
            "output": output,
        })
        completed_depts.add(dept)

    # Synthesize if 2+ results
    final = ""
    if len(results) >= 2:
        print(f"\n{'='*60}")
        print(f"  SYNTHESIS — Lead Orchestrator")
        print(f"{'='*60}")
        final = synthesize(task, results)
    elif results:
        final = results[0]["output"]

    elapsed = time.time() - t0
    print(f"\n{'='*60}")
    print(f"  Chain complete in {elapsed:.1f}s | {len(results)} agents ran")
    print(f"{'='*60}\n")

    return final


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    args = sys.argv[1:]

    if not args:
        print("Usage: python chain.py \"your task\" [--dry-run]")
        print("       Automatically routes single or multi-dept tasks.")
        sys.exit(1)

    dry_run = "--dry-run" in args
    clean = [a for a in args if not a.startswith("--")]
    task = clean[0] if clean else ""

    if not task:
        print("Provide a task as the first argument.")
        sys.exit(1)

    run_chain(task, dry_run=dry_run)
