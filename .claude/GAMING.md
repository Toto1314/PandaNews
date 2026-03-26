# Gaming Intelligence System
**Version:** 1.0.0 | **Added:** 2026-03-25 | **AI OS Version:** 1.10.0

Your personal gaming brain — patch notes, meta coaching, game research, and Telegram notifications. Works in Claude Code via slash commands and on your phone via Kiriko.

---

## Quick Reference

| What you want | Claude Code | Telegram (Kiriko) |
|---|---|---|
| Latest patch notes for a game | `/patch valorant` | "valorant patch notes" |
| Tier list / best picks | `/coach valorant` | "best agents in valorant right now" |
| How to get better at a game | `/coach "how do I rank up in overwatch"` | "how do I rank up in overwatch" |
| Best loadout / build | `/coach "best loadout helldivers2"` | "best loadout helldivers 2" |
| Game mechanics explained | `/game "how does movement work in valorant"` | "how does sage wall work" |
| Upcoming content / season changes | `/game "upcoming LoL changes"` | "what's coming in the next fortnite season" |
| Esports results | `/game "overwatch 2 esports results"` | "who won the valorant tournament" |
| Run patch check for all games | `/gaming-update` | "run patch check" |
| Deep patch analysis (no cache) | `/patch-meta valorant` | — |

---

## Slash Commands

### `/patch [game]`
Checks the local cache first. If the card is less than 24 hours old, shows it instantly — no API call needed. If stale or missing, runs `fetch_updates.py` and shows fresh results.

```
/patch valorant
/patch overwatch2
/patch helldivers2
/patch fortnite
/patch leagueoflegends
/patch                    ← shows all tracked games
```

**Game ID shortcuts:**
- `val` → valorant
- `ow2` or `overwatch` → overwatch2
- `hd2` or `helldivers` → helldivers2
- `fn` → fortnite
- `lol` or `league` → leagueoflegends
- Any other game (e.g. `arc raiders`) → live web search

**Output format:**
```
## <Game> — Patch <VERSION>
### TL;DR
### What Got Buffed
### What Got Nerfed
### What's OP Right Now
### What's Dead
### Under the Radar
### Meta Verdict
```

---

### `/coach [game or question]`
Patch-anchored meta coaching. Reads state.json for the current patch version, then pulls live tier data from tracker sites. Every recommendation is stamped with the patch it applies to.

```
/coach valorant                              ← full tier list
/coach valorant clove                        ← agent-specific coaching
/coach "how do I rank up in league"          ← improvement plan
/coach "best loadout helldivers2"            ← loadout recommendation
/coach "league of legends jungle"            ← role-specific tier list
/coach arc raiders                           ← works for any game, live search
```

**Output types:**
- **Tier list** — S/A/B/C/Avoid with one-line reasoning per tier
- **Improvement plan** — Biggest leak → Week 1 → Week 2 → best picks to main
- **Loadout** — Primary, Secondary, Playstyle, Counters
- **General Q** — Direct answer under 150 words with one concrete next step

---

### `/game [question or topic]`
Research mode. Mechanics, lore, upcoming content, esports, pro play, new releases. Labels anything unconfirmed.

```
/game "how does movement work in valorant"
/game "upcoming LoL season changes"
/game "helldivers 2 best stratagems"
/game "overwatch 2 esports results"
/game "fortnite lore explained"
/game "arc raiders flashpoint update"
```

**Output types:**
- **Mechanics** — How it works, key interactions, common mistakes, pro application
- **Upcoming content** — Confirmed vs UNCONFIRMED/leaked, expected date, meta implication
- **Esports** — Results, what was notable, meta from pro play, one ranked takeaway

---

### `/gaming-update [game]`
Full pipeline: fetch patch card via Claude → push Telegram notification for new versions. Runs all enabled games if no argument.

```
/gaming-update
/gaming-update valorant
```

---

### `/patch-meta [game or paste patch notes]`
Original patch analyzer — no cache check, always goes live. Good when you want a second opinion or the cache feels stale.

---

## Tracked Games

Managed in `~/.claude/skills/gaming-update/games.json`

| Game | ID | Patch URL | Telegram Notify |
|---|---|---|---|
| Valorant | `valorant` | playvalorant.com/en-us/news/game-updates/ | ✅ |
| Overwatch 2 | `overwatch2` | overwatch.blizzard.com/en-us/news/patch-notes/ | ✅ |
| Helldivers 2 | `helldivers2` | store.steampowered.com/news/app/553850 | ✅ |
| Fortnite | `fortnite` | fortnite.com/news | ✅ |
| League of Legends | `leagueoflegends` | leagueoflegends.com/en-us/news/tags/patch-notes/ | ✅ |

**To add a new game:** Tell Claude "add [game] to my gaming tracker" — Dir-Gaming will validate a working patch URL and update games.json.

**To disable Telegram push for a game:** Set `"notify_telegram": false` in games.json.

---

## Telegram (Kiriko) — Gaming Intents

Kiriko runs 24/7 and handles three gaming intents. Just text it naturally — no commands needed.

### `gaming_update` intent
Triggered by: patch mentions, "what got nerfed", "what's OP", "patch notes for X"
- Runs fetch_updates.py → push_updates.py
- Replies with TL;DR + patch version for each game

### `gaming_coaching` intent
Triggered by: "how do I get better", "best agents", "tier list", "loadout", "how do I rank up"
- Routes to Meta-Coach via Claude
- Patch-anchored answer, max 200 words, plain text

### `gaming_research` intent
Triggered by: "how does X work", "what's coming in", "esports results", "lore", "upcoming season"
- Routes to Game-Researcher via Claude
- Labels UNCONFIRMED content clearly, max 200 words

**Example Telegram messages:**
```
valorant patch notes
best agents to play in valorant right now
how do I get better at Overwatch
what's coming in the next LoL patch
helldivers 2 meta loadout
how does sage wall work
who won the valorant championship
```

---

## Daily Automation

Patch check runs daily at 9am via Windows Task Scheduler:
```
schtasks /create /tn "GamingUpdateDaily" /tr "python C:\Users\atank\.claude\skills\gaming-update\run_daily.py" /sc daily /st 09:00 /f
```

Logs: `~/.claude/skills/gaming-update/gaming_update.log`
State: `~/.claude/skills/gaming-update/state.json`

---

## Agent Chain

```
Lead Orchestrator
└── Dir-Gaming          (entry point for all gaming queries)
    ├── Patch-Analyst   (patch notes → structured update cards, haiku-class)
    ├── Meta-Coach      (tier lists, coaching, loadouts, improvement plans, sonnet-class)
    └── Game-Researcher (mechanics, esports, lore, upcoming content, haiku-class)
```

Agent files: `~/.claude/agents/gaming/`

---

## File Map

| File | Purpose |
|---|---|
| `~/.claude/agents/gaming/Dir-Gaming.md` | Department head agent |
| `~/.claude/agents/gaming/Patch-Analyst.md` | Patch notes agent |
| `~/.claude/agents/gaming/Meta-Coach.md` | Coaching agent |
| `~/.claude/agents/gaming/Game-Researcher.md` | Research agent |
| `~/.claude/skills/patch/SKILL.md` | `/patch` slash command |
| `~/.claude/skills/coach/SKILL.md` | `/coach` slash command |
| `~/.claude/skills/game/SKILL.md` | `/game` slash command |
| `~/.claude/skills/gaming-update/SKILL.md` | `/gaming-update` slash command |
| `~/.claude/skills/gaming-update/games.json` | Tracked games config |
| `~/.claude/skills/gaming-update/state.json` | Cached patch cards |
| `~/.claude/skills/gaming-update/fetch_updates.py` | Patch fetcher |
| `~/.claude/skills/gaming-update/push_updates.py` | Telegram push |
| `~/.claude/skills/gaming-update/run_daily.py` | Daily scheduler |
| `~/.claude/kiriko_bot.py` | Telegram bot (2-way) |
