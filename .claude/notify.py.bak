#!/usr/bin/env python3
"""
Telegram notifier — sends a message to your phone via the Kiriko bot.
Usage:
  python ~/.claude/notify.py "your message here"
  python ~/.claude/notify.py --title "Portfolio Update" "PLTR hit $78 — check entry condition"
"""

import sys
import os
import argparse
import urllib.request
import urllib.parse
import json

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    print("[notify] Error: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in environment", file=sys.stderr)
    sys.exit(1)

def send(message: str, title: str = None) -> bool:
    if title:
        text = f"*{title}*\n\n{message}"
    else:
        text = message

    payload = json.dumps({
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }).encode()

    req = urllib.request.Request(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            return result.get("ok", False)
    except Exception as e:
        print(f"[notify] Error: {e}", file=sys.stderr)
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("message", nargs="?", default=None)
    parser.add_argument("--title", default=None)
    args = parser.parse_args()

    msg = args.message or sys.stdin.read().strip()
    if not msg:
        print("Usage: notify.py \"message\" [--title \"Title\"]", file=sys.stderr)
        sys.exit(1)

    ok = send(msg, title=args.title)
    if ok:
        print("[notify] Sent OK")
    else:
        print("[notify] Failed", file=sys.stderr)
        sys.exit(1)
