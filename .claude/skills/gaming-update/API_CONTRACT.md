# Gaming Update — REST API Contract

**Version:** 1.0.0
**Status:** Design spec for future Next.js web app
**Starting point:** `~/next-template/` (existing Next.js template in home directory)
**Data source:** `~/.claude/skills/gaming-update/` (games.json, state.json)

---

## Overview

The web app exposes a thin REST API over the gaming-update skill's JSON files. The frontend displays update cards, allows toggling games on/off, and shows push history. All routes live under `/api/`.

Base URL (local dev): `http://localhost:3000/api`

---

## Endpoints

### GET /api/games

Returns the full list of configured games with their current state merged in.

**Response 200:**
```json
[
  {
    "id": "valorant",
    "name": "Valorant",
    "enabled": true,
    "search_query": "...",
    "patch_url": "https://playvalorant.com/en-us/news/game-updates/",
    "notify_telegram": true,
    "last_checked": "2026-03-24T09:00:00Z",
    "last_version": "10.04",
    "push_sent": true,
    "tldr": "Jett nerfs land hard. Clove is the new op."
  }
]
```

**Notes:**
- `last_checked`, `last_version`, `push_sent`, `tldr` are pulled from state.json and merged
- Games with no state yet will have those fields as `null`

---

### GET /api/updates

Returns all update cards from state.json, newest version first per game.

**Query params:**
- `game` (optional) — filter by game id, e.g. `?game=valorant`

**Response 200:**
```json
[
  {
    "id": "valorant",
    "name": "Valorant",
    "version": "10.04",
    "last_checked": "2026-03-24T09:00:00Z",
    "push_sent": true,
    "tldr": "Jett nerfs land hard. Clove is the new op.",
    "card": "## Valorant — Patch 10.04\n\n### TL;DR\n..."
  }
]
```

**Update card field (`card`) structure:**
The `card` field is a raw markdown string. Parse it by splitting on `\n###` to extract sections. Section order is always:
1. `TL;DR`
2. `What Got Buffed`
3. `What Got Nerfed`
4. `What's OP Right Now`
5. `What's Dead`
6. `Under the Radar`
7. `Meta Verdict`

First line format (for version extraction):
```
## <Game Name> — Patch <VERSION>
```
Regex: `/## .+ — Patch (.+)/`

Final line is always: `---`

---

### POST /api/games

Add a new game to games.json or update an existing game's config.

**Request body:**
```json
{
  "id": "apex",
  "name": "Apex Legends",
  "enabled": true,
  "search_query": "Apex Legends latest patch notes site:ea.com",
  "patch_url": "https://www.ea.com/games/apex-legends/news",
  "notify_telegram": true
}
```

**Required fields:** `id`, `name`
**Optional fields:** `enabled` (default `true`), `search_query`, `patch_url`, `notify_telegram` (default `true`)

**Response 201** (new game):
```json
{ "ok": true, "action": "created", "id": "apex" }
```

**Response 200** (updated existing):
```json
{ "ok": true, "action": "updated", "id": "apex" }
```

**Response 400** (missing required fields):
```json
{ "ok": false, "error": "id and name are required" }
```

**Notes:**
- `id` must be lowercase alphanumeric (no spaces, no special chars except hyphens)
- If `id` already exists in games.json, the record is updated (not duplicated)
- `last_checked` and `last_version` are set to `null` for new games

---

### DELETE /api/games/:id

Remove a game from games.json and clear its entry from state.json.

**Path param:** `id` — the game id (e.g. `valorant`)

**Response 200:**
```json
{ "ok": true, "deleted": "apex" }
```

**Response 404:**
```json
{ "ok": false, "error": "Game not found: apex" }
```

**Notes:**
- This is a hard delete — the game's state history is also cleared from state.json
- To disable without deleting, use `POST /api/games` with `"enabled": false`

---

## Update Card Parsing Reference

When rendering update cards in the Next.js frontend, parse the markdown card string with this approach:

```typescript
function parseUpdateCard(card: string) {
  const lines = card.split('\n');
  const titleLine = lines[0]; // "## Valorant — Patch 10.04"
  const versionMatch = titleLine.match(/## .+ — Patch (.+)/);
  const version = versionMatch?.[1] ?? 'UNKNOWN';

  const sections: Record<string, string> = {};
  const sectionOrder = [
    'TL;DR',
    'What Got Buffed',
    'What Got Nerfed',
    "What's OP Right Now",
    "What's Dead",
    'Under the Radar',
    'Meta Verdict',
  ];

  let currentSection = '';
  for (const line of lines.slice(1)) {
    const sectionMatch = line.match(/^###\s+(.+)/);
    if (sectionMatch) {
      currentSection = sectionMatch[1].trim();
      sections[currentSection] = '';
    } else if (currentSection && line !== '---') {
      sections[currentSection] += line + '\n';
    }
  }

  // Trim whitespace from each section
  for (const key of Object.keys(sections)) {
    sections[key] = sections[key].trim();
  }

  return { version, sections, sectionOrder };
}
```

---

## Implementation Notes

- **Data layer:** Read/write `games.json` and `state.json` directly from the Next.js API routes using `fs/promises`. No database needed.
- **File paths:** Use environment variable `GAMING_UPDATE_DIR` (default: `~/.claude/skills/gaming-update/`) to locate the JSON files. This makes the app portable.
- **Triggering fetches:** `POST /api/updates/fetch?game=valorant` (not yet defined — add in v1.1) should run `fetch_updates.py` as a child process and stream logs. This is a Tier 1 addition.
- **Auth:** No auth required for local use. If exposed publicly, add a static bearer token via `GAMING_UPDATE_API_KEY` env var checked in middleware.
- **Starting point:** Copy `~/next-template/` as the base. The template already has the `/api/` route structure and TypeScript config ready. Add `fs/promises` reads in `app/api/games/route.ts` and `app/api/updates/route.ts`.
