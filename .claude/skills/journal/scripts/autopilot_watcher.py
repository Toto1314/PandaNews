#!/usr/bin/env python3
"""
autopilot_watcher.py — AutoPilot idea queue writer via Stop hook.

Fires automatically after every Claude response (alongside journal_auto_capture.py).
Reads conversation JSON from stdin, detects #idea and #company signals in the last
CEO message, and writes actionable items to ~/.claude/journal/autopilot/queue.jsonl.

The Lead Orchestrator checks this queue at the start of each response and surfaces
a one-line gate: "⚡ AutoPilot: [idea] — build a plan? yes / no"

Silent by default. --debug flag for troubleshooting.
"""

import sys
import json
import re
import os
import datetime
import argparse
import hashlib

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────

QUEUE_DIR  = os.path.expanduser("~/.claude/journal/autopilot")
QUEUE_FILE = os.path.join(QUEUE_DIR, "queue.jsonl")

MIN_LENGTH = 30
MAX_LENGTH = 4000

# Max age before auto-expiry (days)
EXPIRY_DAYS = 7

# Max pending items to keep in queue (LIFO — newest 3 are shown)
MAX_QUEUE_SIZE = 10

# ─────────────────────────────────────────────────────────────────────────────
# SKIP SIGNALS — same as journal_auto_capture.py
# ─────────────────────────────────────────────────────────────────────────────

SKIP_PATTERNS = [
    r"^/",                          # skill invocations
    r"^(yes|no|go|ok|confirmed|proceed|do it|cancel|done|sure|yep|nope)\s*$",
    r"```",                         # code blocks
    r"\bimplement\b|\brefactor\b|\bdeploy\b|\bfix the\b|\bdebug\b",
    r"^\s*https?://\S+\s*$",        # URL-only messages
    r"^\s*\$\s",                    # shell commands
    r"^(also do|and do|do the prior|do both|proceed|confirm)",
]

# ─────────────────────────────────────────────────────────────────────────────
# AUTOPILOT SIGNALS — specifically actionable/buildable ideas
# ─────────────────────────────────────────────────────────────────────────────

IDEA_SIGNALS = [
    r"\bI want to build\b",
    r"\bwe should (make|build|create)\b",
    r"\bwhat if (we|I) (built|made|created)\b",
    r"\bcould be a (startup|product|tool|app|service|feature)\b",
    r"\bstartup idea\b",
    r"\bproduct idea\b",
    r"\bimagine if\b",
    r"\bI've been thinking about building\b",
    r"\bI want to (make|create) (a|an)\b",
    r"\bwould be cool (to build|as a product|if)\b",
    r"\bI (have|had) an idea\b",
    r"\bwhat if there was\b",
    r"\bbuild (a|an) (system|tool|app|platform|api|bot|service)\b",
]

COMPANY_RESEARCH_SIGNALS = [
    r"\bresearch\s+[A-Z][a-zA-Z]+\b",
    r"\blook into\s+[A-Z][a-zA-Z]+\b",
    r"\bgive me a brief on\b",
    r"\bwhat do (we|you) know about\s+[A-Z][a-zA-Z]+\b",
    r"\bdig into\s+[A-Z][a-zA-Z]+\b",
    r"\banalyz[e|ing]\s+[A-Z][a-zA-Z]+\b",
    r"\bcompetitor analysis\b",
    r"\bwho is\s+[A-Z][a-zA-Z]+\s+(and what|competing|doing)\b",
]


def extract_last_user_message(data: dict) -> str | None:
    """Extract the last user message from Claude Code conversation JSON."""
    for key in ("messages", "transcript", "conversation"):
        msgs = data.get(key, [])
        if msgs:
            for msg in reversed(msgs):
                role = msg.get("role", "")
                if role in ("user", "human"):
                    content = msg.get("content", "")
                    if isinstance(content, list):
                        parts = []
                        for block in content:
                            if isinstance(block, dict):
                                if block.get("type") == "text":
                                    parts.append(block.get("text", ""))
                            elif isinstance(block, str):
                                parts.append(block)
                        content = " ".join(parts)
                    return str(content).strip()
    return None


def should_skip(text: str) -> bool:
    """Return True if this message is a task/command, not an idea."""
    if len(text) < MIN_LENGTH or len(text) > MAX_LENGTH:
        return True
    for pattern in SKIP_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def detect_autopilot_signal(text: str) -> tuple[str | None, str]:
    """
    Detect idea or company research signals.
    Returns (tag, summary) or (None, "") if no signal.
    """
    for pattern in IDEA_SIGNALS:
        if re.search(pattern, text, re.IGNORECASE):
            summary = _extract_summary(text)
            return "#idea", summary

    for pattern in COMPANY_RESEARCH_SIGNALS:
        if re.search(pattern, text, re.IGNORECASE):
            summary = _extract_summary(text)
            return "#company", summary

    return None, ""


def _extract_summary(text: str) -> str:
    """Extract a clean one-sentence summary from the idea text."""
    # Take first sentence or first 80 chars, whichever is shorter
    first_sentence = re.split(r'[.!?]', text)[0].strip()
    if len(first_sentence) > 80:
        # Try to find a natural break
        words = first_sentence.split()
        summary = ""
        for word in words:
            if len(summary) + len(word) > 75:
                summary = summary.rstrip() + "…"
                break
            summary += word + " "
        return summary.strip()
    return first_sentence


def _message_hash(text: str, session_id: str) -> str:
    """Short hash for deduplication."""
    key = f"{session_id}:{text[:100]}"
    return hashlib.md5(key.encode()).hexdigest()[:8]


def load_queue() -> list[dict]:
    """Load existing queue entries."""
    if not os.path.exists(QUEUE_FILE):
        return []
    entries = []
    with open(QUEUE_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return entries


def save_queue(entries: list[dict]) -> None:
    """Write all queue entries back to file."""
    os.makedirs(QUEUE_DIR, exist_ok=True)
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")


def expire_old_entries(entries: list[dict]) -> list[dict]:
    """Mark entries older than EXPIRY_DAYS as expired."""
    cutoff = datetime.datetime.now() - datetime.timedelta(days=EXPIRY_DAYS)
    for entry in entries:
        if entry.get("status") == "pending":
            ts_str = entry.get("ts", "")
            try:
                ts = datetime.datetime.fromisoformat(ts_str)
                if ts < cutoff:
                    entry["status"] = "expired"
            except (ValueError, TypeError):
                pass
    return entries


def is_duplicate(entries: list[dict], msg_hash: str) -> bool:
    """Check if this exact message was already queued."""
    for entry in entries:
        if entry.get("hash") == msg_hash and entry.get("status") == "pending":
            return True
    return False


def enqueue(tag: str, summary: str, session_id: str, msg_hash: str) -> None:
    """Add a new pending item to the queue."""
    os.makedirs(QUEUE_DIR, exist_ok=True)

    entries = load_queue()
    entries = expire_old_entries(entries)

    # Deduplicate
    if is_duplicate(entries, msg_hash):
        return

    # Trim to max size (keep newest)
    pending = [e for e in entries if e.get("status") == "pending"]
    if len(pending) >= MAX_QUEUE_SIZE:
        # Don't add more — queue is full
        return

    new_entry = {
        "ts": datetime.datetime.now().isoformat(),
        "summary": summary,
        "tag": tag,
        "session_id": session_id,
        "hash": msg_hash,
        "status": "pending",
    }
    entries.append(new_entry)
    save_queue(entries)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="Print decisions to stderr")
    args = parser.parse_args()

    # Read stdin (Claude Code passes conversation JSON)
    try:
        raw = sys.stdin.read().strip()
        if not raw:
            sys.exit(0)
        data = json.loads(raw)
    except Exception as e:
        if args.debug:
            print(f"[autopilot_watcher] stdin parse error: {e}", file=sys.stderr)
        sys.exit(0)

    session_id = data.get("session_id", "unknown")
    text = extract_last_user_message(data)

    if not text:
        if args.debug:
            print("[autopilot_watcher] No user message found", file=sys.stderr)
        sys.exit(0)

    if should_skip(text):
        if args.debug:
            print(f"[autopilot_watcher] Skipped: {text[:60]}", file=sys.stderr)
        sys.exit(0)

    tag, summary = detect_autopilot_signal(text)
    if not tag:
        if args.debug:
            print(f"[autopilot_watcher] No autopilot signal: {text[:60]}", file=sys.stderr)
        sys.exit(0)

    msg_hash = _message_hash(text, session_id)
    enqueue(tag, summary, session_id, msg_hash)

    if args.debug:
        print(f"[autopilot_watcher] Queued [{tag}]: {summary}", file=sys.stderr)


if __name__ == "__main__":
    main()
