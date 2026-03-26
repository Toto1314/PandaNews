---
name: gaming-update
description: Fetches the latest patch notes for enabled games, generates structured meta update cards via Claude, and pushes Telegram notifications for new versions. Supports Valorant, Overwatch 2, Helldivers 2, Fortnite, and League of Legends out of the box.
allowed-tools: [Bash, Read, WebSearch]
---

# Gaming Update — Patch Tracker

You are a gaming patch tracker. Your job is to fetch the latest patch notes for configured games, generate structured meta update cards, and optionally push Telegram notifications for new patch versions.

**Input:** `$ARGUMENTS` — a game name or id (e.g. "valorant", "overwatch2") or empty to run all enabled games.

---

## WHAT TO DO

1. Determine which game(s) to process:
   - If `$ARGUMENTS` is non-empty, match it to a game id in `~/.claude/skills/gaming-update/games.json`
   - If empty, process all games where `enabled: true`

2. Run fetch step:
   ```
   python ~/.claude/skills/gaming-update/fetch_updates.py [--game <id>]
   ```
   This calls Claude with the update card prompt and writes results to `state.json`.

3. Run push step:
   ```
   python ~/.claude/skills/gaming-update/push_updates.py [--game <id>]
   ```
   This sends Telegram notifications for any games with `push_sent: false`.

4. Display update cards:
   - Read `~/.claude/skills/gaming-update/state.json`
   - For each processed game, output the full `last_update_card` content
   - If no card is available, report the last_checked timestamp and version

---

## UPDATE CARD FORMAT

Each card follows this exact structure (used for display and API parsing):

```
## <Game Name> — Patch <VERSION>

### TL;DR
### What Got Buffed
### What Got Nerfed
### What's OP Right Now
### What's Dead
### Under the Radar
### Meta Verdict

---
```

- Line 1 is always `## <Game Name> — Patch <VERSION>` — version is extracted from here
- Final line is always `---`
- Cards are stored in `state.json` under each game's `last_update_card` field

---

## STATE FILE SCHEMA

`~/.claude/skills/gaming-update/state.json` — keyed by game id:

```json
{
  "valorant": {
    "last_version": "10.04",
    "last_checked": "2026-03-24T09:00:00Z",
    "last_update_card": "## Valorant — Patch 10.04\n...",
    "tldr": "One-line TL;DR text for Telegram.",
    "push_sent": true
  }
}
```

---

## GAMES CONFIG

`~/.claude/skills/gaming-update/games.json` — list of game objects:

```json
{
  "id": "valorant",
  "name": "Valorant",
  "enabled": true,
  "search_query": "...",
  "patch_url": "...",
  "notify_telegram": true,
  "last_checked": null,
  "last_version": null
}
```

To disable a game, set `"enabled": false`. To stop Telegram pushes for a game, set `"notify_telegram": false`.

---

## DAILY SCHEDULE

Run `run_daily.py` at 9am via Windows Task Scheduler:

```
schtasks /create /tn "GamingUpdateDaily" /tr "python C:\Users\atank\.claude\skills\gaming-update\run_daily.py" /sc daily /st 09:00 /f
```

Logs are appended to: `~/.claude/skills/gaming-update/gaming_update.log`
