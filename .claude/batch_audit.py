"""
Batch Audit Runner
==================
CAE-Audit style compliance check across multiple agents in parallel.
Uses parallel_runner.batch_run — all agents audited simultaneously.

After every run, results are automatically recorded to:
  - audit_history.jsonl       machine-readable log (pure Python, every run)
  - AUDIT_FINDINGS.md         human + agent readable findings register (OPEN findings)
  - CHANGELOG.md              company audit trail (every run as a company event)

Recording uses gemma3:1b for prose fields (root cause, remediation language).
All structure is Python templates — no Claude API tokens consumed.

Usage
-----
    python batch_audit.py                         # audit all pipeline agents
    python batch_audit.py --dept engineering      # specific department folder
    python batch_audit.py --dept c-suite --n 5   # first N agents in dept
    python batch_audit.py --files agent1.md agent2.md  # specific files
    python batch_audit.py --check nc              # specific check type
    python batch_audit.py --no-record             # skip writing to audit files
    python batch_audit.py --list-checks           # show available checks

Check Types
-----------
    nc          Negative Constraints present and specific?
    invoke      Invoke-when section clear and non-vague?
    escalation  Escalation paths defined?
    tools       Tool list appropriate for the role?
    chain       Reports-to / Manages chain populated?
    full        All of the above (default)
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

AGENTS_DIR   = Path.home() / ".claude" / "agents"
CLAUDE_DIR   = Path.home() / ".claude"
AUDIT_FILE   = CLAUDE_DIR / "AUDIT_FINDINGS.md"
CHANGELOG    = CLAUDE_DIR / "CHANGELOG.md"
HISTORY_FILE = CLAUDE_DIR / "audit_history.jsonl"

sys.path.insert(0, str(CLAUDE_DIR))
from parallel_runner import batch_run

# ── COSO mapping per check type ───────────────────────────────────────────────

COSO_MAP = {
    "nc":         ("COSO (Control Activities)",           "Behavioral constraints missing or incomplete"),
    "invoke":     ("COSO (Information & Communication)",  "Routing guidance unclear — agents may be invoked incorrectly"),
    "escalation": ("COSO (Control Activities)",           "Escalation path undefined — risk events may not surface"),
    "tools":      ("COSO (Control Activities) · CIS",     "Tool access misaligned with stated role"),
    "chain":      ("COSO (Control Environment)",          "Accountability structure incomplete"),
    "full":       ("COSO (Monitoring Activities)",        "Multi-point compliance gap"),
}

SEVERITY_MAP = {
    # For full check: count of failing dimensions
    5: "CRITICAL",
    4: "HIGH",
    3: "HIGH",
    2: "MEDIUM",
    1: "LOW",
    0: "LOW",
}

# ── Audit check definitions ───────────────────────────────────────────────────

CHECKS = {
    "nc": (
        "You are CAE-Audit. Review this agent file for Negative Constraints.\n\n"
        "PASS if: There is a '## Negative Constraints' section with at least 2 specific "
        "NEVER rules that include reasoning (not just 'do not X' but 'do not X because Y').\n"
        "FAIL if: Section is missing, has fewer than 2 rules, or rules are vague.\n\n"
        "Reply with exactly: PASS or FAIL, then one sentence explanation.\n\n"
        "AGENT FILE:\n{content}"
    ),
    "invoke": (
        "You are CAE-Audit. Review this agent file's invoke-when guidance.\n\n"
        "PASS if: There is clear, specific guidance on when to invoke this agent "
        "(not just 'use this agent for X' but with enough specificity to distinguish "
        "from similar agents).\n"
        "FAIL if: No invoke guidance, or guidance is generic/vague.\n\n"
        "Reply with exactly: PASS or FAIL, then one sentence explanation.\n\n"
        "AGENT FILE:\n{content}"
    ),
    "escalation": (
        "You are CAE-Audit. Review this agent file for escalation rules.\n\n"
        "PASS if: There is an '## Escalation Rules' section with at least one specific "
        "trigger condition and a named escalation target.\n"
        "FAIL if: Section missing, or rules don't specify who to escalate to.\n\n"
        "Reply with exactly: PASS or FAIL, then one sentence explanation.\n\n"
        "AGENT FILE:\n{content}"
    ),
    "tools": (
        "You are CAE-Audit. Review this agent file's tool list.\n\n"
        "PASS if: The frontmatter has a 'tools:' list that is appropriate for the role "
        "(e.g., a read-only scout should NOT have Write/Edit; a builder SHOULD have Edit/Write).\n"
        "FAIL if: No tools listed, or tools are clearly mismatched to the stated role.\n\n"
        "Reply with exactly: PASS or FAIL, then one sentence explanation.\n\n"
        "AGENT FILE:\n{content}"
    ),
    "chain": (
        "You are CAE-Audit. Review this agent file's reporting chain.\n\n"
        "PASS if: There is a 'Reports to:' or 'Manages:' line that names specific agents "
        "(not just 'the team' or 'leadership').\n"
        "FAIL if: No chain defined, or chain references non-existent roles.\n\n"
        "Reply with exactly: PASS or FAIL, then one sentence explanation.\n\n"
        "AGENT FILE:\n{content}"
    ),
}

FULL_CHECK = (
    "You are CAE-Audit. Run a 5-point compliance check on this agent file.\n\n"
    "Score each item PASS or FAIL:\n"
    "1. NC: Negative Constraints section with 2+ specific NEVER rules with reasoning\n"
    "2. INVOKE: Clear, specific invoke-when guidance\n"
    "3. ESCALATION: Escalation rules with named targets\n"
    "4. TOOLS: Tool list appropriate for the stated role\n"
    "5. CHAIN: Reports-to or Manages chain with specific agent names\n\n"
    "Format your reply as:\n"
    "NC: PASS/FAIL\n"
    "INVOKE: PASS/FAIL\n"
    "ESCALATION: PASS/FAIL\n"
    "TOOLS: PASS/FAIL\n"
    "CHAIN: PASS/FAIL\n"
    "VERDICT: PASS (all 5) / CONDITIONAL (3-4) / FAIL (<=2)\n\n"
    "AGENT FILE:\n{content}"
)


# ── File loading ──────────────────────────────────────────────────────────────

def _load_agents(dept: str | None, files: list[str] | None, n: int | None) -> list[tuple[str, str]]:
    if files:
        paths = [Path(f) for f in files]
    elif dept:
        dept_dir = AGENTS_DIR / dept
        if not dept_dir.exists():
            matches = [d for d in AGENTS_DIR.iterdir() if d.is_dir() and dept.lower() in d.name.lower()]
            if not matches:
                print(f"[batch_audit] Department '{dept}' not found under {AGENTS_DIR}")
                sys.exit(1)
            dept_dir = matches[0]
            print(f"[batch_audit] Using: {dept_dir.name}")
        paths = sorted(dept_dir.glob("*.md"))
    else:
        paths = sorted((AGENTS_DIR / "pipeline").glob("*.md"))

    if n:
        paths = paths[:n]

    result = []
    for p in paths:
        try:
            content = p.read_text(encoding="utf-8")
            result.append((p.stem, content[:3000]))
        except Exception as e:
            print(f"[batch_audit] Could not read {p.name}: {e}")

    return result


def _build_batch(agents: list[tuple[str, str]], check: str) -> list[dict]:
    template = CHECKS.get(check, FULL_CHECK)
    return [
        {"model": "llama3.2:3b", "prompt": template.format(content=c), "label": n}
        for n, c in agents
    ]


# ── Verdict parsing ───────────────────────────────────────────────────────────

def _parse_verdict(output: str | None, check: str) -> str:
    if not output:
        return "ERROR"
    out = output.upper()
    if check == "full":
        if "VERDICT: PASS" in out:   return "PASS"
        if "CONDITIONAL" in out:     return "CONDITIONAL"
        if "VERDICT: FAIL" in out:   return "FAIL"
    else:
        first = out.strip().splitlines()[0] if output.strip() else ""
        if first.startswith("PASS"): return "PASS"
        if first.startswith("FAIL"): return "FAIL"
    if "PASS" in out[:50]: return "PASS"
    if "FAIL" in out[:50]: return "FAIL"
    return "UNKNOWN"


def _parse_failing_checks(output: str | None) -> list[str]:
    """For full check: return list of dimension names that failed."""
    if not output:
        return []
    dims = ["NC", "INVOKE", "ESCALATION", "TOOLS", "CHAIN"]
    failed = []
    for line in output.upper().splitlines():
        for dim in dims:
            if line.startswith(f"{dim}:") and "FAIL" in line:
                failed.append(dim)
    return failed


def _severity_for_result(verdict: str, failing_checks: list[str]) -> str:
    if verdict == "PASS":
        return "INFO"
    if verdict == "FAIL":
        return SEVERITY_MAP.get(len(failing_checks), "HIGH")
    # CONDITIONAL
    count = len(failing_checks)
    return SEVERITY_MAP.get(count, "MEDIUM")


# ── Recording layer ───────────────────────────────────────────────────────────

async def _generate_prose(prompt: str) -> str:
    """Use gemma3:1b to generate short prose. Falls back to empty string."""
    try:
        import ollama
        client = ollama.AsyncClient()
        resp = await asyncio.wait_for(
            client.chat(
                model="gemma3:1b",
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.1, "num_predict": 80},
            ),
            timeout=45,
        )
        return resp["message"]["content"].strip()
    except Exception:
        return ""


async def _record_results(
    results:  list[dict],
    verdicts: list[str],
    check:    str,
    dept:     str | None,
    wall:     float,
) -> None:
    """
    Write audit run to:
      1. audit_history.jsonl   — machine-readable, every run, pure Python
      2. AUDIT_FINDINGS.md     — findings register, OPEN entries for failures
      3. CHANGELOG.md          — company audit trail entry
    """
    now        = datetime.now(timezone.utc)
    date_str   = now.strftime("%Y-%m-%d")
    ts_str     = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    scope_label = dept or "pipeline"

    pass_c  = verdicts.count("PASS")
    fail_c  = verdicts.count("FAIL")
    cond_c  = verdicts.count("CONDITIONAL")
    total   = len(results)

    # ── 1. audit_history.jsonl (pure Python, no LLM) ─────────────────────────
    history_entry = {
        "ts":           ts_str,
        "date":         date_str,
        "scope":        scope_label,
        "check":        check,
        "total_agents": total,
        "pass":         pass_c,
        "conditional":  cond_c,
        "fail":         fail_c,
        "wall_s":       round(wall, 1),
        "trigger":      "manual",
        "model":        "llama3.2:3b",
        "agents": [
            {
                "name":          r["label"],
                "verdict":       v,
                "elapsed_s":     r["elapsed"],
                "failing_checks": _parse_failing_checks(r["output"]) if check == "full" else [],
                "finding":       (r["output"] or "")[:400],
            }
            for r, v in zip(results, verdicts)
        ],
    }

    with HISTORY_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(history_entry) + "\n")

    print(f"  [record] audit_history.jsonl -> appended run {ts_str}")

    # ── 2. AUDIT_FINDINGS.md — one entry per non-PASS agent ──────────────────
    failures = [
        (r, v, _parse_failing_checks(r["output"]))
        for r, v in zip(results, verdicts)
        if v not in ("PASS", "INFO")
    ]

    if failures:
        finding_blocks = []

        # Generate root cause + remediation prose in parallel via gemma3:1b
        prose_tasks = []
        for r, v, failing in failures:
            dim_list = ", ".join(failing) if failing else check.upper()
            agent    = r["label"]
            prose_tasks.append(
                _generate_prose(
                    f"In one sentence, state the likely root cause for an AI agent named '{agent}' "
                    f"failing a compliance audit on: {dim_list}. Be specific and brief."
                )
            )
            prose_tasks.append(
                _generate_prose(
                    f"In one sentence, state the remediation action needed for an AI agent named '{agent}' "
                    f"that failed compliance on: {dim_list}. Start with a verb (Add, Define, Expand, etc.)."
                )
            )

        prose_results = await asyncio.gather(*prose_tasks)

        for idx, (r, v, failing) in enumerate(failures):
            root_cause   = prose_results[idx * 2]     or f"Agent '{r['label']}' missing or incomplete {', '.join(failing) if failing else check.upper()} section."
            remediation  = prose_results[idx * 2 + 1] or f"Add {', '.join(failing) if failing else check.upper()} section with specific, named targets."
            severity     = _severity_for_result(v, failing)
            coso, _      = COSO_MAP.get(check, COSO_MAP["full"])
            dim_list     = ", ".join(failing) if failing else check.upper()

            # Truncate model finding to first 3 meaningful lines
            finding_lines = [
                l.strip() for l in (r["output"] or "").splitlines()
                if l.strip() and l.strip().upper() not in ("PASS", "FAIL", "CONDITIONAL")
            ]
            finding_excerpt = "  \n  ".join(finding_lines[:3])

            finding_blocks.append(
                f"\n### [{date_str}] | {severity} | {r['label']} — {dim_list} failure ({scope_label})\n"
                f"**Status:** OPEN  \n"
                f"**Audit Run:** {ts_str} | scope={scope_label} | check={check} | model=llama3.2:3b  \n"
                f"**Framework:** {coso}  \n"
                f"**Verdict:** {v} — failing dimensions: {dim_list}  \n"
                f"**Finding:**  \n"
                f"  {finding_excerpt}  \n"
                f"**Root Cause:** {root_cause}  \n"
                f"**Remediation:** {remediation}  \n"
                f"**Resolution Entry:** PENDING  \n"
            )

        # Insert under ## OPEN FINDINGS, before the first --- after it
        content = AUDIT_FILE.read_text(encoding="utf-8")
        insert_marker = "## OPEN FINDINGS"
        if insert_marker in content:
            idx = content.index(insert_marker) + len(insert_marker)
            # Skip past the existing *(none...)* line if present
            content = (
                content[:idx]
                + "\n"
                + "".join(finding_blocks)
                + "\n---\n"
                + content[idx:].lstrip().lstrip("*").lstrip()
            )
        else:
            content += "\n## OPEN FINDINGS\n" + "".join(finding_blocks)

        AUDIT_FILE.write_text(content, encoding="utf-8")
        print(f"  [record] AUDIT_FINDINGS.md -> {len(failures)} finding(s) added as OPEN")
    else:
        print(f"  [record] AUDIT_FINDINGS.md -> no findings (all PASS)")

    # ── 3. CHANGELOG.md — one entry for the entire audit run ─────────────────
    overall = "PASS" if fail_c == 0 and cond_c == 0 else ("CONDITIONAL" if fail_c == 0 else "FAIL")
    failing_agents = [r["label"] for r, v in zip(results, verdicts) if v != "PASS"]

    changelog_entry = (
        f"\n## {date_str} | AUDIT | batch_audit run — {scope_label} dept, check={check}\n\n"
        f"**Changed By:** batch_audit.py (automated — llama3.2:3b)  \n"
        f"**Approved By:** N/A (automated monitoring activity)  \n"
        f"**Risk Tier:** 1  \n"
        f"**COSO Component:** Monitoring Activities · Control Activities  \n\n"
        f"**Scope:** {scope_label} department | {total} agents | check={check}  \n"
        f"**Result:** {overall} — PASS: {pass_c} | CONDITIONAL: {cond_c} | FAIL: {fail_c}  \n"
        f"**Wall time:** {wall:.1f}s (parallel, model: llama3.2:3b)  \n"
    )

    if failing_agents:
        changelog_entry += f"**Findings opened:** {', '.join(failing_agents)}  \n"
        changelog_entry += f"**Action required:** Remediate OPEN findings in AUDIT_FINDINGS.md  \n"
    else:
        changelog_entry += f"**Findings:** None — all agents compliant  \n"

    changelog_entry += "\n---\n"

    # Prepend after the header block (after first ---)
    cl_content = CHANGELOG.read_text(encoding="utf-8")
    first_sep  = cl_content.find("\n---\n")
    if first_sep != -1:
        cl_content = cl_content[:first_sep + 5] + changelog_entry + cl_content[first_sep + 5:]
    else:
        cl_content = cl_content + changelog_entry

    CHANGELOG.write_text(cl_content, encoding="utf-8")
    print(f"  [record] CHANGELOG.md -> audit run entry added ({date_str})")


# ── Console output ────────────────────────────────────────────────────────────

def _print_results(results: list[dict], verdicts: list[str], check: str, wall: float) -> None:
    pass_c = verdicts.count("PASS")
    fail_c = verdicts.count("FAIL")
    cond_c = verdicts.count("CONDITIONAL")
    err_c  = verdicts.count("ERROR") + verdicts.count("UNKNOWN")

    print(f"\n{'='*70}")
    print(f"  CAE-Audit Batch Results  |  check={check}  |  {len(results)} agents  |  {wall:.1f}s wall")
    print(f"  PASS: {pass_c}  FAIL: {fail_c}  CONDITIONAL: {cond_c}  ERR: {err_c}")
    print(f"{'='*70}\n")

    print(f"  {'Agent':<30} {'Verdict':<14} {'Time':>6}  Notes")
    print(f"  {'-'*65}")

    for r, verdict in zip(results, verdicts):
        icon = "OK" if verdict == "PASS" else ("~~" if verdict == "CONDITIONAL" else "!!")
        note = ""
        if r["output"]:
            for line in r["output"].strip().splitlines():
                if line.strip() and line.strip().upper() not in ("PASS", "FAIL", "CONDITIONAL"):
                    note = line.strip()[:50]
                    break
        err = f"  ERROR: {r['error'][:40]}" if r.get("error") else ""
        print(f"  [{icon}] {r['label']:<28} {verdict:<14} {r['elapsed']:>5.1f}s  {note}{err}")

    print()

    failures = [(r, v) for r, v in zip(results, verdicts) if v in ("FAIL", "CONDITIONAL", "UNKNOWN")]
    if failures:
        print(f"  --- Findings ---\n")
        for r, v in failures:
            print(f"  [{r['label']}] {v}")
            if r["output"]:
                for line in r["output"].strip().splitlines():
                    print(f"    {line}")
            print()


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    args = sys.argv[1:]

    if "--list-checks" in args:
        print("\nAvailable checks:")
        for k in list(CHECKS.keys()) + ["full"]:
            print(f"  {k}")
        print()
        sys.exit(0)

    dept      = None
    files     = None
    check     = "full"
    n         = None
    no_record = "--no-record" in args

    i = 0
    while i < len(args):
        if args[i] == "--dept" and i + 1 < len(args):
            dept = args[i + 1]; i += 2
        elif args[i] == "--check" and i + 1 < len(args):
            check = args[i + 1]; i += 2
        elif args[i] == "--n" and i + 1 < len(args):
            n = int(args[i + 1]); i += 2
        elif args[i] == "--files":
            files = args[i + 1:]; break
        else:
            i += 1

    agents = _load_agents(dept, files, n)
    if not agents:
        print("[batch_audit] No agent files found.")
        sys.exit(1)

    print(f"\n  [batch_audit] Auditing {len(agents)} agents in parallel")
    print(f"  Check : {check}")
    print(f"  Model : llama3.2:3b (audit)  +  gemma3:1b (prose recording)")
    print(f"  Record: {'disabled (--no-record)' if no_record else 'audit_history.jsonl | AUDIT_FINDINGS.md | CHANGELOG.md'}\n")

    items = _build_batch(agents, check)

    t0      = time.perf_counter()
    results = asyncio.run(batch_run(items))
    wall    = time.perf_counter() - t0

    verdicts = [_parse_verdict(r["output"], check) for r in results]
    _print_results(results, verdicts, check, wall)

    if not no_record:
        print(f"  Recording results...\n")
        asyncio.run(_record_results(results, verdicts, check, dept, wall))
        print()
