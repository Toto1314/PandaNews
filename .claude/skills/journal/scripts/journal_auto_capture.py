#!/usr/bin/env python3
"""
journal_auto_capture.py — Passive journal capture via Stop hook.

Fires automatically after every Claude response via settings.json Stop hook.
Reads conversation JSON from stdin, extracts the last CEO message,
decides if it's worth capturing, and writes a tagged entry silently.

No output unless T1 data is detected (which gets flagged) or --debug is passed.
"""

import sys
import json
import re
import os
import datetime
import argparse

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────

JOURNAL_DIR = os.path.expanduser("~/.claude/journal/entries")
AUDIT_LOG   = os.path.expanduser("~/.claude/journal/audit.log")
INDEX_FILE  = os.path.expanduser("~/.claude/journal/index.md")
MIN_LENGTH  = 30   # chars — skip very short messages
MAX_LENGTH  = 4000 # chars — skip gigantic pastes

# ─────────────────────────────────────────────────────────────────────────────
# SKIP SIGNALS — task/command messages that are NOT diary content
# ─────────────────────────────────────────────────────────────────────────────

SKIP_PATTERNS = [
    r"^/",                          # skill invocations (/lean, /journal, /patch...)
    r"^(yes|no|go|ok|confirmed|proceed|do it|cancel|done|sure|yep|nope)\s*$",  # one-word confirmations
    r"```",                         # code blocks
    r"\bimplement\b|\brefactor\b|\bdeploy\b|\bfix the\b|\bdebug\b",  # task verbs
    r"^\s*https?://\S+\s*$",        # URL-only messages
    r"^\s*\$\s",                    # shell commands
    r"^(also do|and do|do the prior|do both|proceed|confirm)",  # execution confirmations
]

# ─────────────────────────────────────────────────────────────────────────────
# CAPTURE SIGNALS — conversational/personal content worth journaling
# ─────────────────────────────────────────────────────────────────────────────

CAPTURE_SIGNALS = {
    "#personal":  [
        r"\bI feel\b", r"\bI felt\b", r"\bI think\b", r"\bI believe\b",
        r"\bI realized\b", r"\bI noticed\b", r"\bI've been\b", r"\bI am\b",
        r"\bmy life\b", r"\bmy day\b", r"\btoday\b", r"\brecently\b",
        r"\bI'm (worried|excited|frustrated|inspired|confused|happy|sad)\b",
    ],
    "#worldview": [
        r"\bthe way I see\b", r"\bthe world\b", r"\bpeople are\b",
        r"\bsociety\b", r"\bhuman nature\b", r"\bthe system\b",
        r"\bI've come to\b", r"\bmy philosophy\b", r"\bthe truth is\b",
        r"\bwhat I've learned\b",
    ],
    "#learn": [
        r"\bI should learn\b", r"\bI want to understand\b", r"\bI need to study\b",
        r"\binteresting concept\b", r"\bfascinating\b", r"\bnote to self\b",
        r"\bremember this\b", r"\bkeep in mind\b", r"\bworth exploring\b",
    ],
    "#idea": [
        r"\bwhat if\b", r"\bI want to build\b", r"\bwe should make\b",
        r"\bcould be a\b", r"\bstartup idea\b", r"\bproduct idea\b",
        r"\bimagine if\b", r"\bwould be cool\b", r"\bI've been thinking about building\b",
    ],
    "#company": [
        r"\b[A-Z][a-z]+\s+(Inc|Corp|Ltd|AI|Labs|Technologies|Systems|Platform)\b",
        r"\bcompany called\b", r"\bstartup called\b", r"\bI heard about\b",
    ],
    "#action": [
        r"\bI need to\b", r"\bI should\b", r"\bfollow up\b", r"\bremember to\b",
        r"\btodo\b", r"\bto-do\b", r"\baction item\b", r"\bdon't forget\b",
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
# T1 PATTERNS — redact before writing
# ─────────────────────────────────────────────────────────────────────────────

T1_PATTERNS = [
    (r"\bsk-[A-Za-z0-9]{20,}\b", "api_key"),
    (r"\bghp_[A-Za-z0-9]{36}\b", "github_pat"),
    (r"\bBearer\s+[A-Za-z0-9\-._~+/]{20,}={0,2}\b", "bearer_token"),
    (r"\b[0-9]{3}-[0-9]{2}-[0-9]{4}\b", "ssn"),
    (r"\b(?:password|pwd|passwd)\s*[=:]\s*\S+", "password"),
    (r"\b[0-9]{16}\b", "card_number"),
    (r"[A-Za-z0-9+/]{40,}={0,2}", "possible_secret"),  # base64 blob
]


def extract_last_user_message(data: dict) -> str | None:
    """Extract the last user message from the Claude Code conversation JSON."""
    # Claude Code Stop hook passes: {"session_id": ..., "transcript": [...], "messages": [...]}
    # Try multiple possible formats
    for key in ("messages", "transcript", "conversation"):
        msgs = data.get(key, [])
        if msgs:
            for msg in reversed(msgs):
                role = msg.get("role", "")
                if role in ("user", "human"):
                    content = msg.get("content", "")
                    if isinstance(content, list):
                        # Extract text from content blocks
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
    """Return True if this message is a task/command, not diary content."""
    if len(text) < MIN_LENGTH or len(text) > MAX_LENGTH:
        return True
    for pattern in SKIP_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def classify_tags(text: str) -> list[str]:
    """Return list of matching tags from CAPTURE_SIGNALS."""
    tags = []
    for tag, patterns in CAPTURE_SIGNALS.items():
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                tags.append(tag)
                break
    return tags


def scan_t1(text: str) -> tuple[str, list[str]]:
    """
    Scan for T1 data. Returns (redacted_text, list_of_detected_types).
    """
    detected = []
    result = text
    for pattern, label in T1_PATTERNS:
        new = re.sub(pattern, f"[REDACTED:{label}]", result)
        if new != result:
            detected.append(label)
            result = new
    return result, detected


def write_entry(text: str, tags: list[str], session_id: str, t1_types: list[str]) -> str:
    """Write a journal entry and return the file path."""
    now = datetime.datetime.now()
    year  = now.strftime("%Y")
    month = now.strftime("%m")
    stamp = now.strftime("%Y%m%d-%H%M%S")

    # Ensure directory exists
    entry_dir = os.path.join(JOURNAL_DIR, year, month)
    os.makedirs(entry_dir, exist_ok=True)

    entry_path = os.path.join(entry_dir, f"{stamp}.md")

    # Build one-line summary (first sentence or first 80 chars)
    summary = re.split(r'[.!?]', text)[0].strip()[:80]

    t1_note = ""
    if t1_types:
        t1_note = f"\nt1_redacted: [{', '.join(t1_types)}]"

    content = f"""---
date: {now.isoformat()}
session_id: {session_id}
tags: {' '.join(tags) if tags else '#personal'}
source: auto-capture (Stop hook){t1_note}
---

{text}

---

[TAGS]: {' '.join(tags) if tags else '#personal'}
"""

    with open(entry_path, "w", encoding="utf-8") as f:
        f.write(content)

    return entry_path


def write_audit(entry_path: str, session_id: str, t1_types: list[str]) -> None:
    now = datetime.datetime.now().isoformat()
    t1_note = f" | T1_REDACTED:{','.join(t1_types)}" if t1_types else ""
    line = f"{now} | Dir-Journal(auto) | WRITE | {entry_path} | session:{session_id}{t1_note}\n"
    with open(AUDIT_LOG, "a", encoding="utf-8") as f:
        f.write(line)


def update_index(entry_path: str, tags: list[str], summary: str) -> None:
    now = datetime.datetime.now().strftime("%Y-%m-%d")
    rel_path = entry_path.replace(os.path.expanduser("~/.claude/journal/"), "")
    line = f"| {now} | {' '.join(tags)} | {summary[:60]} | {rel_path} |\n"
    with open(INDEX_FILE, "a", encoding="utf-8") as f:
        f.write(line)


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
            print(f"[journal_auto_capture] stdin parse error: {e}", file=sys.stderr)
        sys.exit(0)

    session_id = data.get("session_id", "unknown")
    text = extract_last_user_message(data)

    if not text:
        if args.debug:
            print("[journal_auto_capture] No user message found", file=sys.stderr)
        sys.exit(0)

    if should_skip(text):
        if args.debug:
            print(f"[journal_auto_capture] Skipped: {text[:60]}...", file=sys.stderr)
        sys.exit(0)

    tags = classify_tags(text)
    if not tags:
        if args.debug:
            print(f"[journal_auto_capture] No capture signals found: {text[:60]}...", file=sys.stderr)
        sys.exit(0)

    # T1 scan
    clean_text, t1_types = scan_t1(text)

    # Write entry
    entry_path = write_entry(clean_text, tags, session_id, t1_types)
    write_audit(entry_path, session_id, t1_types)

    summary = re.split(r'[.!?]', clean_text)[0].strip()[:60]
    update_index(entry_path, tags, summary)

    if args.debug:
        print(f"[journal_auto_capture] Saved: {entry_path} | tags: {tags}", file=sys.stderr)

    # If T1 detected, write to stderr so Claude Code surfaces it
    if t1_types:
        print(f"⚠️  Journal auto-capture: T1 data redacted from entry ({', '.join(t1_types)}). Entry saved without it.", file=sys.stderr)


if __name__ == "__main__":
    main()
