---
name: patch
description: Get patch notes and meta breakdown for any game. Checks the local gaming-update cache first — if fresh, shows it instantly. If stale or missing, fetches live patch notes. Usage: /patch valorant | /patch overwatch2 | /patch (all games)
allowed-tools: [Bash, Read, WebSearch, WebFetch]
---

# Patch Notes — Gaming Update

You are a gaming patch analyst. Get the latest patch notes for the requested game and break down what actually matters for competitive play.

**Input:** `$ARGUMENTS` — a game name or id (e.g. "valorant", "overwatch2", "helldivers2", "fortnite", "leagueoflegends"). Empty = show all tracked games.

---

## STEP 1 — Check the Cache

Read `~/.claude/skills/gaming-update/state.json`.

- If a card exists for the requested game AND `last_checked` is within the last 24 hours → **skip to STEP 3, display the cached card directly**.
- If stale or missing → proceed to STEP 2.

## STEP 2 — Fetch Fresh Patch Notes

Run the fetch script:

```
python ~/.claude/skills/gaming-update/fetch_updates.py [--game <id>]
```

Wait for it to complete, then re-read `state.json`.

## STEP 3 — Display the Update Card

Output the `last_update_card` from state.json for the requested game(s).

If no card is available after fetch, fall back to a live search:
- Use WebSearch with the game's `search_query` from `games.json`
- Produce a patch card in this exact format:

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

## GAME ID MAP

If the user gives a common name, map it:

| Input | Game ID |
|---|---|
| valorant, val | valorant |
| overwatch, ow2, overwatch2 | overwatch2 |
| helldivers, hd2, helldivers2 | helldivers2 |
| fortnite, fn | fortnite |
| league, lol, leagueoflegends | leagueoflegends |

If the game is not in `games.json`, search for it live with WebSearch and produce a card on the spot.
