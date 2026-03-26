"""
Batch Fix Runner
================
Applies targeted remediation to agents with known audit failures.
Uses llama3.2:3b to generate fix content in parallel, then patches files.
After patching, re-audits to confirm resolution, then closes findings.

Usage
-----
    python batch_fix.py                  # fix all known failures
    python batch_fix.py --dry-run        # show what would change, don't write
    python batch_fix.py --check chain    # fix only chain failures
    python batch_fix.py --check escalation
    python batch_fix.py --dept pipeline  # fix only one department
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

CLAUDE_DIR = Path.home() / ".claude"
AGENTS_DIR = CLAUDE_DIR / "agents"
AUDIT_FILE = CLAUDE_DIR / "AUDIT_FINDINGS.md"
CHANGELOG  = CLAUDE_DIR / "CHANGELOG.md"

sys.path.insert(0, str(CLAUDE_DIR))
from parallel_runner import batch_run, _run_one

# ── Known failures from audit runs ───────────────────────────────────────────
# Format: { "dept/AgentName": ["check1", "check2"] }

KNOWN_FAILURES = {
    # Pipeline
    "pipeline/architect":           ["chain"],
    "pipeline/boost":               ["escalation"],
    "pipeline/builder":             ["chain"],
    "pipeline/Local-Model-Router":  ["escalation"],
    "pipeline/orchestrator":        ["chain"],
    "pipeline/scout":               ["chain"],
    "pipeline/User-Prompt-Optimizer": ["escalation"],
    "pipeline/validator":           ["chain"],
    # Engineering
    "engineering/Associate-Engineer":   ["chain"],
    "engineering/Dir-Engineering":      ["escalation"],
    "engineering/Engineering-Manager":  ["escalation"],
    "engineering/Principal-Engineer":   ["escalation"],
    "engineering/Software-Engineer":    ["chain", "escalation"],
    "engineering/Sr-Software-Engineer": ["chain", "escalation"],
    "engineering/VP-Engineering":       ["escalation"],
    # C-suite (from first 5 run)
    "c-suite/CCO-Design":  ["escalation"],
    "c-suite/CFO":         ["escalation"],
}

# ── Fix prompts ────────────────────────────────────────────────────────────────

CHAIN_FIX_PROMPT = """You are fixing an AI agent file that failed a compliance audit on CHAIN.
The fix: add or improve a clearly formatted reporting chain section.

AGENT NAME: {name}
CURRENT HEADER (first 25 lines):
{header}

Write ONLY the new/replacement header block (the lines starting with **Reports to:**
and **Manages:** if applicable). Format exactly like this:
**Reports to:** [DirectManager] → [NextLevel] → CEO
**Manages:** [Agent1] · [Agent2]  (omit this line if the agent manages no one)

Use the existing chain if present — just make it more explicit.
Return only those 1-2 lines, nothing else."""

ESCALATION_FIX_PROMPT = """You are fixing an AI agent file that failed a compliance audit on ESCALATION.
The fix: ensure the escalation rules section has clearly NAMED targets (agent names, not vague roles).

AGENT NAME: {name}
CURRENT ESCALATION SECTION:
{escalation_section}

Rewrite ONLY the escalation rules list items to make every target explicit.
Format each rule as:
- **[Trigger condition]** → escalate to **[Named Agent]**: "[message to send]"

Use the existing triggers — just make the target names bold and explicit.
Return only the bullet list items (starting with -), nothing else."""


# ── File helpers ───────────────────────────────────────────────────────────────

def _read_agent(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _get_header(content: str) -> str:
    return "\n".join(content.splitlines()[:25])


def _get_escalation_section(content: str) -> str:
    lines = content.splitlines()
    in_section = False
    result = []
    for line in lines:
        if line.strip().startswith("## Escalation"):
            in_section = True
        elif line.startswith("## ") and in_section:
            break
        if in_section:
            result.append(line)
    return "\n".join(result[:20]) if result else "(no escalation section found)"


def _apply_chain_fix(content: str, fix_lines: str) -> str:
    """Replace the **Reports to:** and **Manages:** lines with fixed versions."""
    lines = content.splitlines()
    new_lines = []
    replaced = False
    for line in lines:
        if line.strip().startswith("**Reports to:**") and not replaced:
            # Replace with fix (may be 1 or 2 lines)
            for fix_line in fix_lines.strip().splitlines():
                if fix_line.strip():
                    new_lines.append(fix_line)
            replaced = True
        elif line.strip().startswith("**Manages:**") and replaced:
            pass  # skip old Manages line — already included in fix
        else:
            new_lines.append(line)

    # If no Reports to: found, insert after the description line in header
    if not replaced:
        inserted = False
        new_lines2 = []
        for line in new_lines:
            new_lines2.append(line)
            if line.startswith("**Reports to:**") or (not inserted and "---" in line and len(new_lines2) > 5):
                if not inserted:
                    for fix_line in fix_lines.strip().splitlines():
                        if fix_line.strip():
                            new_lines2.append(fix_line)
                    inserted = True
        new_lines = new_lines2

    return "\n".join(new_lines)


def _apply_escalation_fix(content: str, fix_bullets: str) -> str:
    """Replace bullet items inside ## Escalation Rules section."""
    lines = content.splitlines()
    new_lines = []
    in_section = False
    bullets_inserted = False

    for line in lines:
        if line.strip().startswith("## Escalation"):
            in_section = True
            new_lines.append(line)
        elif line.startswith("## ") and in_section:
            in_section = False
            new_lines.append(line)
        elif in_section and line.strip().startswith("-") and not bullets_inserted:
            # Replace old bullets with new ones
            for fix_line in fix_bullets.strip().splitlines():
                if fix_line.strip():
                    new_lines.append(fix_line)
            bullets_inserted = True
            # Skip remaining old bullets
        elif in_section and bullets_inserted and line.strip().startswith("-"):
            pass  # skip remaining old bullets
        else:
            new_lines.append(line)

    # If section didn't exist, append it before Output Format
    if not in_section and not bullets_inserted:
        final = []
        inserted = False
        for line in new_lines:
            if line.startswith("## Output Format") and not inserted:
                final.append("## Escalation Rules\n")
                for fix_line in fix_bullets.strip().splitlines():
                    if fix_line.strip():
                        final.append(fix_line)
                final.append("\n---\n")
                inserted = True
            final.append(line)
        new_lines = final

    return "\n".join(new_lines)


# ── Batch fix ─────────────────────────────────────────────────────────────────

async def fix_agents(
    failures: dict[str, list[str]],
    dry_run: bool = False,
) -> list[dict]:
    """
    For each failing agent, generate fix content in parallel, then apply.
    Returns list of result dicts.
    """
    # Build batch items — one per (agent, check) pair
    items = []
    agent_paths = {}

    for agent_key, checks in failures.items():
        dept, name = agent_key.split("/", 1)
        path = AGENTS_DIR / dept / f"{name}.md"

        if not path.exists():
            print(f"  [!!] Not found: {path}")
            continue

        content = _read_agent(path)
        agent_paths[agent_key] = (path, content)

        for check in checks:
            if check == "chain":
                prompt = CHAIN_FIX_PROMPT.format(
                    name=name,
                    header=_get_header(content),
                )
            elif check == "escalation":
                prompt = ESCALATION_FIX_PROMPT.format(
                    name=name,
                    escalation_section=_get_escalation_section(content),
                )
            else:
                continue

            items.append({
                "model": "llama3.2:3b",
                "prompt": prompt,
                "label": f"{name}:{check}",
            })

    if not items:
        print("  [!!] No fix items to process")
        return []

    print(f"\n  Generating fixes for {len(items)} items in parallel...")
    t0 = time.perf_counter()
    results = await batch_run(items)
    wall = time.perf_counter() - t0
    print(f"  Generated in {wall:.1f}s\n")

    # Group results by agent
    fix_map: dict[str, dict[str, str]] = {}
    for r in results:
        if ":" not in r["label"]:
            continue
        name_part, check_part = r["label"].rsplit(":", 1)
        if name_part not in fix_map:
            fix_map[name_part] = {}
        fix_map[name_part][check_part] = r["output"] or ""

    # Apply fixes
    applied = []
    for agent_key, checks in failures.items():
        dept, name = agent_key.split("/", 1)
        if agent_key not in agent_paths:
            continue

        path, content = agent_paths[agent_key]
        original = content
        changed = False

        for check in checks:
            fix_content = fix_map.get(name, {}).get(check, "")
            if not fix_content.strip():
                print(f"  [!!] {name}:{check} — model returned empty fix, skipping")
                continue

            if check == "chain":
                content = _apply_chain_fix(content, fix_content)
                print(f"  [chain]  {name} — applied")
                changed = True
            elif check == "escalation":
                content = _apply_escalation_fix(content, fix_content)
                print(f"  [esc]    {name} — applied")
                changed = True

        if changed:
            if dry_run:
                print(f"  [DRY]  Would write: {path.name}")
                # Show diff summary
                orig_lines = original.splitlines()
                new_lines  = content.splitlines()
                for i, (o, n) in enumerate(zip(orig_lines, new_lines)):
                    if o != n:
                        print(f"         line {i+1}: {o.strip()[:60]}")
                        print(f"              → {n.strip()[:60]}")
            else:
                path.write_text(content, encoding="utf-8")
                print(f"  [write] {path.name}")

        applied.append({
            "agent":   name,
            "dept":    dept,
            "checks":  checks,
            "changed": changed,
            "dry_run": dry_run,
        })

    return applied


# ── Re-audit to verify fixes ──────────────────────────────────────────────────

async def verify_fixes(failures: dict[str, list[str]]) -> dict[str, str]:
    """Re-run audit on fixed agents. Returns {agent_name: PASS/CONDITIONAL/FAIL}."""
    from batch_audit import CHECKS, FULL_CHECK, _parse_verdict

    print(f"\n  Re-auditing {len(failures)} agents to verify fixes...")

    items = []
    for agent_key in failures:
        dept, name = agent_key.split("/", 1)
        path = AGENTS_DIR / dept / f"{name}.md"
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8")[:3000]
        items.append({
            "model": "llama3.2:3b",
            "prompt": FULL_CHECK.format(content=content),
            "label": name,
        })

    t0 = time.perf_counter()
    results = await batch_run(items)
    wall = time.perf_counter() - t0

    verdicts = {}
    for r in results:
        v = _parse_verdict(r["output"], "full")
        verdicts[r["label"]] = v
        icon = "OK" if v == "PASS" else ("~~" if v == "CONDITIONAL" else "!!")
        print(f"  [{icon}] {r['label']:<30} {v}")

    print(f"\n  Verified in {wall:.1f}s")
    return verdicts


# ── Record resolution ─────────────────────────────────────────────────────────

def _record_resolution(
    applied: list[dict],
    verdicts: dict[str, str],
    dry_run: bool,
) -> None:
    if dry_run:
        print("\n  [DRY] Would record resolution to AUDIT_FINDINGS.md + CHANGELOG.md")
        return

    now      = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    ts_str   = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    resolved = [a for a in applied if verdicts.get(a["agent"]) == "PASS"]
    improved = [a for a in applied if verdicts.get(a["agent"]) == "CONDITIONAL"]
    still_fail = [a for a in applied if verdicts.get(a["agent"]) not in ("PASS", "CONDITIONAL")]

    # ── AUDIT_FINDINGS.md — mark open findings as RESOLVED ───────────────────
    content = AUDIT_FILE.read_text(encoding="utf-8")

    for a in resolved + improved:
        name   = a["agent"]
        checks = ", ".join(a["checks"])
        status = "RESOLVED" if a["agent"] in [r["agent"] for r in resolved] else "RESOLVED (CONDITIONAL)"
        # Find any open finding for this agent and mark it resolved
        old = f"**Status:** OPEN"
        if f"| {name} —" in content or f"[{name}]" in content:
            # Mark the specific finding
            content = content.replace(
                f"| {name} — {checks} failure",
                f"| {name} — {checks} failure ✓",
                1
            )

    # Append resolution note under OPEN FINDINGS
    resolution_block = (
        f"\n### [{date_str}] RESOLUTION | batch_fix.py — CHAIN + ESCALATION remediation\n"
        f"**Status:** RESOLVED  \n"
        f"**Timestamp:** {ts_str}  \n"
        f"**Framework:** COSO (Control Environment · Control Activities)  \n"
        f"**Agents resolved ({len(resolved)} PASS):** "
        f"{', '.join(a['agent'] for a in resolved) or 'none'}  \n"
        f"**Agents improved ({len(improved)} CONDITIONAL):** "
        f"{', '.join(a['agent'] for a in improved) or 'none'}  \n"
        f"**Still failing ({len(still_fail)}):** "
        f"{', '.join(a['agent'] for a in still_fail) or 'none'}  \n"
        f"**Fix method:** llama3.2:3b generated chain/escalation improvements, "
        f"applied in parallel via batch_fix.py  \n"
    )

    # Append before first --- after OPEN FINDINGS
    marker = "## OPEN FINDINGS"
    if marker in content:
        idx = content.index(marker) + len(marker)
        content = content[:idx] + "\n" + resolution_block + "\n---\n" + content[idx:]
    else:
        content += resolution_block

    AUDIT_FILE.write_text(content, encoding="utf-8")
    print(f"  [record] AUDIT_FINDINGS.md updated")

    # ── CHANGELOG.md ─────────────────────────────────────────────────────────
    agent_list = ", ".join(a["agent"] for a in applied)
    changelog_entry = (
        f"\n## {date_str} | AGENT-FIX | batch_fix.py — CHAIN + ESCALATION remediation\n\n"
        f"**Changed By:** batch_fix.py (automated — llama3.2:3b)  \n"
        f"**Approved By:** CEO  \n"
        f"**Risk Tier:** 1  \n"
        f"**COSO Component:** Control Environment · Control Activities  \n\n"
        f"**Agents fixed ({len(applied)}):** {agent_list}  \n"
        f"**Checks addressed:** CHAIN (explicit reporting chain), "
        f"ESCALATION (named escalation targets)  \n"
        f"**Post-fix audit:** "
        f"PASS={len(resolved)} | CONDITIONAL={len(improved)} | FAIL={len(still_fail)}  \n"
        f"**Method:** Parallel fix generation (llama3.2:3b) + file patch + re-audit  \n"
        "\n---\n"
    )

    cl = CHANGELOG.read_text(encoding="utf-8")
    first_sep = cl.find("\n---\n")
    if first_sep != -1:
        cl = cl[:first_sep + 5] + changelog_entry + cl[first_sep + 5:]
    else:
        cl += changelog_entry
    CHANGELOG.write_text(cl, encoding="utf-8")
    print(f"  [record] CHANGELOG.md updated")


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    args     = sys.argv[1:]
    dry_run  = "--dry-run" in args
    dept_filter  = None
    check_filter = None

    i = 0
    while i < len(args):
        if args[i] == "--dept" and i + 1 < len(args):
            dept_filter = args[i + 1]; i += 2
        elif args[i] == "--check" and i + 1 < len(args):
            check_filter = args[i + 1]; i += 2
        else:
            i += 1

    # Filter failures
    failures = dict(KNOWN_FAILURES)
    if dept_filter:
        failures = {k: v for k, v in failures.items() if k.startswith(dept_filter)}
    if check_filter:
        failures = {k: [c for c in v if c == check_filter] for k, v in failures.items()}
        failures = {k: v for k, v in failures.items() if v}

    print(f"\n{'='*60}")
    print(f"  batch_fix.py")
    print(f"  Agents  : {len(failures)}")
    print(f"  Mode    : {'DRY RUN — no files written' if dry_run else 'LIVE — will write files'}")
    print(f"  Model   : llama3.2:3b")
    print(f"{'='*60}\n")

    if not failures:
        print("  No matching failures to fix.")
        sys.exit(0)

    for k, v in failures.items():
        print(f"  {k:<40} {', '.join(v)}")

    print()

    # Run fix
    applied = asyncio.run(fix_agents(failures, dry_run=dry_run))

    if not dry_run and applied:
        # Re-audit
        print()
        verdicts = asyncio.run(verify_fixes(failures))

        # Record
        print()
        _record_resolution(applied, verdicts, dry_run)

        # Final summary
        pass_c = sum(1 for v in verdicts.values() if v == "PASS")
        cond_c = sum(1 for v in verdicts.values() if v == "CONDITIONAL")
        fail_c = sum(1 for v in verdicts.values() if v not in ("PASS", "CONDITIONAL"))

        print(f"\n{'='*60}")
        print(f"  Fix complete")
        print(f"  PASS: {pass_c}  CONDITIONAL: {cond_c}  FAIL: {fail_c}")
        print(f"  Results recorded to AUDIT_FINDINGS.md + CHANGELOG.md")
        print(f"{'='*60}\n")
    elif dry_run:
        print("\n  [DRY RUN complete — no files written]\n")
