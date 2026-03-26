#!/usr/bin/env python3
"""
fetch_updates.py — Fetches latest patch notes for enabled games via Claude.
Reads games.json, runs claude --print for each game using update_card_prompt.txt,
extracts version from output, and writes results to state.json.

Usage:
    python fetch_updates.py               # fetch all enabled games
    python fetch_updates.py --game valorant  # fetch one game by id
"""

import os
import sys
import json
import re
import subprocess
import logging
import argparse
from datetime import datetime, timezone

# ── Optional Supabase sync ───────────────────────────────────────────────────
# Set SUPABASE_URL + SUPABASE_SERVICE_KEY to also write cards to Supabase.
# If not set, only state.json is written (local mode — no change to existing behavior).
try:
    from supabase import create_client as _sb_create
    _SUPABASE_URL = os.environ.get("SUPABASE_URL")
    _SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
    _supabase = _sb_create(_SUPABASE_URL, _SUPABASE_KEY) if (_SUPABASE_URL and _SUPABASE_KEY) else None
except ImportError:
    _supabase = None

def _sync_to_supabase(game_id: str, version: str, tldr: str, card: str, ts: str) -> None:
    """Push a patch card to Supabase patch_cards table. No-op if not configured."""
    if not _supabase:
        return
    try:
        import re as _re
        section_map = {
            "tldr":         r"###\s*TL;DR\s*\n(.*?)(?=\n###|\Z)",
            "buffed":       r"###\s*What Got Buffed\s*\n(.*?)(?=\n###|\Z)",
            "nerfed":       r"###\s*What Got Nerfed\s*\n(.*?)(?=\n###|\Z)",
            "op_now":       r"###\s*What's OP Right Now\s*\n(.*?)(?=\n###|\Z)",
            "dead":         r"###\s*What's Dead\s*\n(.*?)(?=\n###|\Z)",
            "under_radar":  r"###\s*Under the Radar\s*\n(.*?)(?=\n###|\Z)",
            "meta_verdict": r"###\s*Meta Verdict\s*\n(.*?)(?=\n###|---|\Z)",
        }
        sections = {}
        for key, pattern in section_map.items():
            m = _re.search(pattern, card, _re.DOTALL | _re.IGNORECASE)
            sections[key] = m.group(1).strip() if m else ""

        _supabase.table("patch_cards").upsert({
            "game_id":       game_id,
            "version":       version,
            "patch_date":    ts,
            "tldr":          tldr,
            "card_markdown": card,
            "sections":      sections,
            "push_sent":     False,
        }, on_conflict="game_id,version").execute()
        log.info("Supabase sync OK: %s Patch %s", game_id, version)
    except Exception as e:
        log.warning("Supabase sync failed for %s: %s — state.json still updated", game_id, e)

# ── Paths ───────────────────────────────────────────────────────────────────

HOME          = os.path.expanduser("~")
SKILL_DIR     = os.path.join(HOME, ".claude", "skills", "gaming-update")
GAMES_FILE    = os.path.join(SKILL_DIR, "games.json")
STATE_FILE    = os.path.join(SKILL_DIR, "state.json")
PROMPT_FILE   = os.path.join(SKILL_DIR, "update_card_prompt.txt")
TMP_PROMPT    = os.path.join(HOME, ".claude", "_kiriko_prompt.txt")
CLAUDE_PATH   = r"C:\Users\atank\AppData\Roaming\npm\claude.ps1"
LOG_FILE      = os.path.join(SKILL_DIR, "gaming_update.log")
CLAUDE_TIMEOUT = 300  # seconds per game (web search + page fetch + card generation)

# ── Logging ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger("fetch_updates")

# ── Helpers ──────────────────────────────────────────────────────────────────

def load_json(path: str) -> object:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str, data: object):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_claude(prompt: str) -> str:
    """Write prompt to temp file and pipe it into claude --print via PowerShell."""
    with open(TMP_PROMPT, "w", encoding="utf-8") as f:
        f.write(prompt)

    try:
        result = subprocess.run(
            [
                "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                "-Command",
                f"Get-Content -Raw -Encoding UTF8 '{TMP_PROMPT}' | & '{CLAUDE_PATH}' --print"
            ],
            capture_output=True,
            text=True,
            timeout=CLAUDE_TIMEOUT,
        )
        output = result.stdout.strip()
        if not output:
            err = result.stderr.strip()
            log.warning(f"No stdout from claude. stderr: {err[:300]}")
            return f"Error: {err[:300]}" if err else "No response from Claude."
        return output
    except subprocess.TimeoutExpired:
        log.error("Claude timed out after %ds", CLAUDE_TIMEOUT)
        return "Error: Claude timed out."
    except Exception as e:
        log.error("run_claude error: %s", e)
        return f"Error: {e}"
    finally:
        try:
            os.remove(TMP_PROMPT)
        except Exception:
            pass


def extract_version(first_line: str) -> str | None:
    """
    Parse version from the first line of the card.
    Expected format: ## <GameName> — Patch <VERSION>
    Returns the VERSION string, or None if not found.
    """
    match = re.search(r"Patch\s+([^\s].+?)$", first_line.strip())
    if match:
        return match.group(1).strip()
    return None


def extract_first_line(text: str) -> str:
    """Return the first non-empty line of text."""
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return ""


def extract_tldr(card: str) -> str:
    """Extract the TL;DR section text from the update card."""
    match = re.search(r"###\s*TL;DR\s*\n(.*?)(?=\n###|\Z)", card, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""

# ── Core logic ───────────────────────────────────────────────────────────────

def fetch_game(game: dict, state: dict, prompt_template: str) -> dict:
    """Fetch update card for a single game. Returns updated state entry."""
    game_id   = game["id"]
    game_name = game["name"]

    log.info("Fetching update for: %s", game_name)

    # Build prompt
    prompt = (
        prompt_template
        .replace("{{GAME_NAME}}", game_name)
        .replace("{{SEARCH_QUERY}}", game["search_query"])
    )

    # Run claude
    card = run_claude(prompt)
    log.info("Received %d chars for %s", len(card), game_name)

    first_line = extract_first_line(card)
    version    = extract_version(first_line)
    ts_now     = now_iso()

    if version is None:
        log.warning("Could not extract version from first line: %r", first_line)
        version = "UNKNOWN"

    existing = state.get(game_id, {})
    prior_version = existing.get("last_version")

    if prior_version is None or prior_version != version:
        # New version detected (or first run) — store full card
        log.info("New version for %s: %s (was: %s)", game_name, version, prior_version)
        tldr = extract_tldr(card)
        state[game_id] = {
            "last_version":     version,
            "last_checked":     ts_now,
            "last_update_card": card,
            "push_sent":        False,
            "tldr":             tldr,
        }
        _sync_to_supabase(game_id, version, tldr, card, ts_now)
    else:
        # Same version — update timestamp only, preserve push_sent
        log.info("Same version for %s: %s — updating last_checked only", game_name, version)
        existing["last_checked"] = ts_now
        state[game_id] = existing

    return state


def main():
    parser = argparse.ArgumentParser(description="Fetch gaming patch update cards via Claude.")
    parser.add_argument("--game", type=str, default=None,
                        help="Game id to fetch (e.g. valorant). Omit to fetch all enabled games.")
    args = parser.parse_args()

    # Load data
    games         = load_json(GAMES_FILE)
    state         = load_json(STATE_FILE)
    prompt_template = open(PROMPT_FILE, "r", encoding="utf-8").read()

    # Filter games
    if args.game:
        target = args.game.lower().strip()
        games  = [g for g in games if g["id"] == target]
        if not games:
            log.error("No game found with id: %s", target)
            sys.exit(1)
    else:
        games = [g for g in games if g.get("enabled", False)]

    log.info("Processing %d game(s).", len(games))

    for game in games:
        try:
            state = fetch_game(game, state, prompt_template)
            save_json(STATE_FILE, state)
            log.info("State saved after: %s", game["name"])
        except Exception as e:
            log.error("Error fetching %s: %s", game["name"], e)

    log.info("fetch_updates.py complete.")


if __name__ == "__main__":
    main()
