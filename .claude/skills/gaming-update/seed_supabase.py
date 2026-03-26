#!/usr/bin/env python3
"""
seed_supabase.py — One-time seed script for PatchPulse Supabase database.
Reads games.json and state.json, writes to Supabase games + patch_cards tables.

Usage:
    python seed_supabase.py

Requirements:
    pip install supabase

Environment variables (set in your shell or .env):
    SUPABASE_URL         — e.g. https://xxxx.supabase.co
    SUPABASE_SERVICE_KEY — service role key (bypasses RLS, safe for local scripts)
"""

import os
import json
import sys
from datetime import datetime, timezone

# ── Dependency check ──────────────────────────────────────────────────────────

try:
    from supabase import create_client, Client
except ImportError:
    print("ERROR: supabase-py not installed. Run: pip install supabase")
    sys.exit(1)

# ── Config ────────────────────────────────────────────────────────────────────

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: Set SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables.")
    print("  Windows: set SUPABASE_URL=https://xxxx.supabase.co")
    print("           set SUPABASE_SERVICE_KEY=your-service-role-key")
    sys.exit(1)

SKILL_DIR  = os.path.join(os.path.expanduser("~"), ".claude", "skills", "gaming-update")
GAMES_FILE = os.path.join(SKILL_DIR, "games.json")
STATE_FILE = os.path.join(SKILL_DIR, "state.json")

# ── Helpers ───────────────────────────────────────────────────────────────────

def load_json(path: str) -> object:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def parse_sections(card_markdown: str) -> dict:
    """
    Extract the 7 named sections from a patch card into a dict.
    Keys: tldr, buffed, nerfed, op_now, dead, under_radar, meta_verdict
    """
    import re
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
        match = re.search(pattern, card_markdown, re.DOTALL | re.IGNORECASE)
        sections[key] = match.group(1).strip() if match else ""
    return sections

# ── Seed: games table ─────────────────────────────────────────────────────────

def seed_games(supabase: Client, games: list) -> None:
    print(f"\n[games] Seeding {len(games)} games...")
    for game in games:
        row = {
            "id":           game["id"],
            "name":         game["name"],
            "enabled":      game.get("enabled", True),
            "search_query": game.get("search_query"),
            "patch_url":    game.get("patch_url"),
        }
        result = supabase.table("games").upsert(row, on_conflict="id").execute()
        print(f"  [OK] {game['name']} ({game['id']})")

# ── Seed: patch_cards table ───────────────────────────────────────────────────

def seed_patch_cards(supabase: Client, state: dict) -> None:
    print(f"\n[patch_cards] Seeding {len(state)} patch card(s)...")
    for game_id, entry in state.items():
        version = entry.get("last_version")
        card    = entry.get("last_update_card", "")
        tldr    = entry.get("tldr", "")
        ts      = entry.get("last_checked", datetime.now(timezone.utc).isoformat())

        if not version or not card:
            print(f"  [SKIP] {game_id} — no version or card data")
            continue

        sections = parse_sections(card)

        row = {
            "game_id":       game_id,
            "version":       version,
            "patch_date":    ts,
            "tldr":          tldr,
            "card_markdown": card,
            "sections":      sections,
            "push_sent":     entry.get("push_sent", False),
        }

        result = supabase.table("patch_cards").upsert(
            row, on_conflict="game_id,version"
        ).execute()
        print(f"  [OK] {game_id} — Patch {version}")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("PatchPulse — Supabase Seed")
    print(f"URL: {SUPABASE_URL}")
    print(f"Games file:  {GAMES_FILE}")
    print(f"State file:  {STATE_FILE}")

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    games = load_json(GAMES_FILE)
    state = load_json(STATE_FILE)

    seed_games(supabase, games)
    seed_patch_cards(supabase, state)

    print("\n[DONE] Seed complete. Open Loveable and connect to your Supabase project.")
    print("       Your /feed page will show real patch cards on first load.")

if __name__ == "__main__":
    main()
