#!/usr/bin/env python3
"""
auto_changelog.py — AI OS Auto-Changelog Generator
Runs as part of the pre-commit hook to auto-write CHANGELOG.md entries
for any staged changes to agents/ directory.

Usage (called by hook):
    python auto_changelog.py

Returns exit code 0 always (non-blocking — changelog failure never stops a commit).
"""

import subprocess
import sys
import re
from datetime import datetime
from pathlib import Path

CHANGELOG_PATH = Path(__file__).parent / "CHANGELOG.md"
AGENTS_DIR = ".claude/agents/"

# Maps change type letter to human label
CHANGE_LABELS = {
    "A": "AGENT-CREATE",
    "M": "AGENT-UPDATE",
    "D": "AGENT-DELETE",
    "R": "AGENT-RENAME",
}

# Maps department folder to display name
DEPT_NAMES = {
    "ai-ml":       "AI & ML",
    "audit":       "Internal Audit",
    "c-suite":     "C-Suite",
    "comms":       "Communications",
    "data":        "Data & Analytics",
    "design":      "CX & Design",
    "devops":      "DevOps / Platform",
    "engineering": "Engineering",
    "finance":     "Finance",
    "gaming":      "Gaming Intelligence",
    "governance":  "Governance",
    "gtm":         "GTM / Revenue",
    "hr":          "HR / People",
    "investments": "Investments",
    "legal":       "Legal / GRC",
    "pipeline":    "Technical Pipeline",
    "pmo":         "PMO",
    "product":     "Product",
    "prompt-eng":  "Prompt Engineering",
    "research":    "Research & Innovation",
    "security":    "Security",
    "strategy":    "Strategy",
}


def get_staged_agent_changes():
    """Return list of (status, filepath) for staged agent .md files."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-status", "--diff-filter=AMDRC"],
        capture_output=True, text=True
    )
    changes = []
    for line in result.stdout.strip().splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        status = parts[0][0]  # First char: A/M/D/R
        filepath = parts[-1]  # Last part is always the current path
        if filepath.startswith(AGENTS_DIR) and filepath.endswith(".md"):
            changes.append((status, filepath))
    return changes


def get_staged_commit_msg():
    """Try to get the commit message from COMMIT_EDITMSG (set during prepare-commit-msg)."""
    try:
        git_dir = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True, text=True
        ).stdout.strip()
        msg_file = Path(git_dir) / "COMMIT_EDITMSG"
        if msg_file.exists():
            msg = msg_file.read_text(encoding="utf-8").strip()
            # Filter out comment lines
            lines = [l for l in msg.splitlines() if not l.startswith("#")]
            return " ".join(lines).strip()[:120]
    except Exception:
        pass
    return None


def classify_changes(changes):
    """Group changes by department and type."""
    by_dept = {}
    for status, filepath in changes:
        parts = Path(filepath).parts  # e.g. ('.claude', 'agents', 'hr', 'VP-People.md')
        # Find 'agents' index to handle any prefix (.claude/agents/ or agents/)
        try:
            idx = list(parts).index("agents")
            dept = parts[idx + 1] if idx + 1 < len(parts) - 1 else "unknown"
            agent = parts[-1].replace(".md", "")
        except ValueError:
            dept = "unknown"
            agent = parts[-1].replace(".md", "")

        label = CHANGE_LABELS.get(status, "AGENT-UPDATE")
        by_dept.setdefault(dept, []).append((label, agent, filepath))
    return by_dept


def determine_entry_type(changes):
    """Pick the top-level changelog entry type from the mix of changes."""
    types = {s for s, _ in changes}
    if "A" in types and "M" not in types and "D" not in types:
        return "AGENT-CREATE"
    if "D" in types and "A" not in types and "M" not in types:
        return "AGENT-DELETE"
    if "A" in types:
        return "AGENT-CREATE + AGENT-UPDATE"
    return "AGENT-UPDATE"


def count_total_agents():
    """Count current total agents in directory."""
    agents_path = Path(__file__).parent / "agents"
    return sum(1 for f in agents_path.rglob("*.md"))


def build_changelog_entry(changes, by_dept):
    """Build a full CHANGELOG.md entry string."""
    today = datetime.now().strftime("%Y-%m-%d")
    entry_type = determine_entry_type(changes)
    total = count_total_agents()

    # Build dept summary for title
    depts = sorted(DEPT_NAMES.get(d, d.title()) for d in by_dept)
    dept_summary = " · ".join(depts) if len(depts) <= 4 else f"{len(depts)} departments"

    commit_msg = get_staged_commit_msg()
    title_suffix = f" — {commit_msg}" if commit_msg else f" — {dept_summary}"

    lines = [
        f"## {today} | {entry_type}{title_suffix}",
        "",
        f"**Changed By:** Lead Orchestrator (auto-logged by pre-commit hook)",
        f"**Risk Tier:** 1",
        f"**Agent Count After:** {total}",
        "",
    ]

    # Per-department breakdown
    for dept, items in sorted(by_dept.items()):
        dept_label = DEPT_NAMES.get(dept, dept.title())
        creates = [a for l, a, _ in items if l == "AGENT-CREATE"]
        updates = [a for l, a, _ in items if l == "AGENT-UPDATE"]
        deletes = [a for l, a, _ in items if l == "AGENT-DELETE"]

        lines.append(f"**{dept_label}:**")
        if creates:
            lines.append(f"- Created: {', '.join(creates)}")
        if updates:
            lines.append(f"- Updated: {', '.join(updates)}")
        if deletes:
            lines.append(f"- Deleted: {', '.join(deletes)}")
        lines.append("")

    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def prepend_to_changelog(entry: str):
    """Insert the new entry right after the header block in CHANGELOG.md."""
    if not CHANGELOG_PATH.exists():
        CHANGELOG_PATH.write_text(entry, encoding="utf-8")
        return

    content = CHANGELOG_PATH.read_text(encoding="utf-8")

    # Find the end of the header (first --- separator)
    sep = "---\n"
    idx = content.find(sep)
    if idx == -1:
        # No separator found — just prepend
        CHANGELOG_PATH.write_text(entry + content, encoding="utf-8")
    else:
        insert_at = idx + len(sep) + 1  # after the --- and blank line
        new_content = content[:insert_at] + entry + content[insert_at:]
        CHANGELOG_PATH.write_text(new_content, encoding="utf-8")


def stage_changelog():
    """Git-add CHANGELOG.md so it's included in the current commit."""
    subprocess.run(["git", "add", str(CHANGELOG_PATH)], check=False)


def main():
    changes = get_staged_agent_changes()
    if not changes:
        # No agent files staged — nothing to do
        sys.exit(0)

    by_dept = classify_changes(changes)
    entry = build_changelog_entry(changes, by_dept)
    prepend_to_changelog(entry)
    stage_changelog()

    # Print summary to terminal
    created = sum(1 for s, _ in changes if s == "A")
    updated = sum(1 for s, _ in changes if s == "M")
    deleted = sum(1 for s, _ in changes if s == "D")
    parts = []
    if created: parts.append(f"{created} created")
    if updated: parts.append(f"{updated} updated")
    if deleted: parts.append(f"{deleted} deleted")
    print(f"[auto-changelog] {', '.join(parts)} — CHANGELOG.md updated")

    sys.exit(0)


if __name__ == "__main__":
    main()
