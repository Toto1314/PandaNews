#!/usr/bin/env python3
"""
push_updates.py — Pushes new patch update notifications via notify.py (Telegram).
Reads state.json and games.json, sends notification for games with push_sent == false,
then marks push_sent = true in state.json.

Usage:
    python push_updates.py               # push all pending games
    python push_updates.py --game valorant  # push one game by id
"""

import os
import sys
import json
import re
import subprocess
import logging
import argparse

# ── Paths ───────────────────────────────────────────────────────────────────

HOME       = os.path.expanduser("~")
SKILL_DIR  = os.path.join(HOME, ".claude", "skills", "gaming-update")
GAMES_FILE = os.path.join(SKILL_DIR, "games.json")
STATE_FILE = os.path.join(SKILL_DIR, "state.json")
NOTIFY_PY  = os.path.join(HOME, ".claude", "notify.py")
LOG_FILE   = os.path.join(SKILL_DIR, "gaming_update.log")

# ── Logging ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger("push_updates")

# ── Helpers ──────────────────────────────────────────────────────────────────

def load_json(path: str) -> object:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str, data: object):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def extract_tldr_from_card(card: str) -> str:
    """Extract the TL;DR section from the update card as a single line."""
    match = re.search(r"###\s*TL;DR\s*\n(.*?)(?=\n###|\Z)", card, re.DOTALL)
    if match:
        # Collapse to one line
        return " ".join(match.group(1).strip().splitlines()).strip()
    return ""


def send_notification(game_name: str, version: str, tldr: str) -> bool:
    """
    Run notify.py to send a Telegram push.
    Returns True on success, False on failure.
    """
    title   = f"{game_name} Patch {version}"
    message = tldr if tldr else f"New patch {version} is live."

    log.info("Sending notification: title=%r message=%r", title, message)

    try:
        result = subprocess.run(
            [sys.executable, NOTIFY_PY, "--title", title, message],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            log.info("Notification sent for %s %s", game_name, version)
            return True
        else:
            log.error(
                "notify.py failed for %s. rc=%d stderr=%s",
                game_name, result.returncode, result.stderr.strip()[:200]
            )
            return False
    except subprocess.TimeoutExpired:
        log.error("notify.py timed out for %s", game_name)
        return False
    except Exception as e:
        log.error("send_notification error for %s: %s", game_name, e)
        return False

# ── Core logic ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Push pending gaming patch notifications via Telegram.")
    parser.add_argument("--game", type=str, default=None,
                        help="Game id to push (e.g. valorant). Omit to push all pending games.")
    args = parser.parse_args()

    games = load_json(GAMES_FILE)
    state = load_json(STATE_FILE)

    # Build a lookup of game metadata keyed by id
    games_by_id = {g["id"]: g for g in games}

    # Filter: only games that are pending a push
    pending = []
    for game_id, entry in state.items():
        if args.game and game_id != args.game.lower().strip():
            continue
        if not entry.get("push_sent", True) and entry.get("last_update_card"):
            game_meta = games_by_id.get(game_id)
            if game_meta and game_meta.get("notify_telegram", False):
                pending.append((game_id, entry, game_meta))

    if not pending:
        log.info("No pending notifications to push.")
        return

    log.info("Pushing %d notification(s).", len(pending))

    for game_id, entry, game_meta in pending:
        game_name = game_meta["name"]
        version   = entry.get("last_version", "UNKNOWN")
        card      = entry.get("last_update_card", "")

        # Use cached tldr if available, else extract from card
        tldr = entry.get("tldr") or extract_tldr_from_card(card)

        success = send_notification(game_name, version, tldr)

        if success:
            state[game_id]["push_sent"] = True
            save_json(STATE_FILE, state)
            print(f"[OK]   {game_name} Patch {version} — notification sent.")
        else:
            print(f"[FAIL] {game_name} Patch {version} — notification failed. Will retry next run.")

    log.info("push_updates.py complete.")


if __name__ == "__main__":
    main()
