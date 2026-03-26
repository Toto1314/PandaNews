# PatchPulse — Loveable Build Prompt
**Product:** PatchPulse SaaS for gamers
**Version:** MVP v1.0
**Paste this directly into lovable.dev**

---

## LOVEABLE PROMPT (paste verbatim)

```
Build a SaaS web app called PatchPulse. Dark gaming aesthetic. React + Supabase.

BRAND & VISUAL STYLE
- App name: PatchPulse
- Tagline: "Meta intelligence. Every patch. No noise."
- Color palette:
    - Background: #0d0d0f (near-black)
    - Surface/cards: #16181d
    - Border: #2a2d35
    - Primary accent: #7c3aed (purple — used for CTAs, badges, active states)
    - Success/buff: #22c55e (green)
    - Danger/nerf: #ef4444 (red)
    - Gold/OP: #f59e0b (amber)
    - Text primary: #f1f5f9
    - Text muted: #64748b
- Font: Inter (system fallback sans-serif)
- No rounded corners bigger than 6px. Sharp, dense, information-forward layout.
- No illustrations or decorative graphics. Game logo/icon placeholders only.

PAGE STRUCTURE (5 pages)

1. /auth — Auth Page
   - Centered card on dark background
   - "PatchPulse" wordmark at top with purple accent
   - Tabs: "Sign In" | "Create Account"
   - Fields: Email, Password
   - Sign In button (primary purple)
   - Create Account button (same)
   - No OAuth, no social login
   - On success, redirect to /feed
   - Uses Supabase Auth (email + password)

2. /feed — Game Feed (home, default route after auth)
   - Top nav: PatchPulse logo left, username right with sign-out dropdown
   - Page header: "Your Games" with a small "Manage" link (goes to /settings)
   - Grid of GameCards (2 columns desktop, 1 column mobile)
   - Each GameCard contains:
       - Game name (large, bold, white)
       - Current patch version — e.g. "Patch 12.05" (muted text, smaller)
       - "NEW" badge (purple pill, shown if patch_date is within 48 hours of now)
       - TL;DR text (1-2 sentences, muted text, truncated at 2 lines with ellipsis)
       - "View Patch Card" button (outline style, full width, goes to /game/:id)
       - Last updated timestamp ("Updated 3h ago" format)
   - If a user has no games subscribed yet, show an empty state: "No games yet. Add your first game in Settings." with a link to /settings
   - Only show games where the user has an active subscription (from user_game_subscriptions table)

3. /game/:id — Full Patch Card View
   - Back button ("← Feed") top left
   - Game name + patch version as page header
   - Patch date below header in muted text
   - Horizontal pill tabs for patch history: "Latest" | "Previous patches" dropdown (up to 10)
   - Main card body — 7 sections rendered in order:
       Section 1 — TL;DR: white box with slightly lighter background, full text
       Section 2 — What Got Buffed: left border accent green (#22c55e), label "BUFFED" in green
       Section 3 — What Got Nerfed: left border accent red (#ef4444), label "NERFED" in red
       Section 4 — What's OP Right Now: left border accent amber (#f59e0b), label "OP NOW" in amber, slightly highlighted background
       Section 5 — What's Dead: left border accent red, label "DEAD" in red, muted opacity
       Section 6 — Under the Radar: left border accent purple (#7c3aed), label "SLEEPER" in purple
       Section 7 — Meta Verdict: full-width card with purple accent border, label "META VERDICT", body text slightly larger
   - Each section renders as markdown (use a lightweight markdown renderer)

4. /settings — Game Subscription Settings
   - Page header: "Your Games"
   - Full list of all available games from the games table
   - Each row: game name, toggle switch (purple when on), notification toggle (bell icon, purple when on)
   - Toggle state writes to user_game_subscriptions table
   - Save changes happens on toggle (no save button — instant)
   - Available games: Valorant, Overwatch 2, Helldivers 2, Fortnite, League of Legends

5. /history/:id — Patch History for a Game
   - Back button ("← [Game Name]") top left
   - Page header: "[Game Name] — Patch History"
   - Reverse-chronological list of past patches (up to 10)
   - Each row: patch version, date, TL;DR one-liner, "View" link
   - Clicking "View" renders the same full patch card as /game/:id but for that historical version

SUPABASE DATA MODEL

Table: games
- id: text PRIMARY KEY (e.g. "valorant")
- name: text NOT NULL
- enabled: boolean DEFAULT true
- search_query: text
- patch_url: text
- created_at: timestamptz DEFAULT now()

Table: patch_cards
- id: uuid PRIMARY KEY DEFAULT gen_random_uuid()
- game_id: text REFERENCES games(id)
- version: text NOT NULL (e.g. "12.05")
- patch_date: timestamptz
- tldr: text
- card_markdown: text NOT NULL
- sections: jsonb
- push_sent: boolean DEFAULT false
- created_at: timestamptz DEFAULT now()
- UNIQUE(game_id, version)

Table: user_game_subscriptions
- id: uuid PRIMARY KEY DEFAULT gen_random_uuid()
- user_id: uuid REFERENCES auth.users(id) ON DELETE CASCADE
- game_id: text REFERENCES games(id)
- notify: boolean DEFAULT true
- created_at: timestamptz DEFAULT now()
- UNIQUE(user_id, game_id)

MAIN USER FLOWS

Flow 1 — New User Onboarding:
/auth (create account) → /settings (pick games) → /feed (see game cards)

Flow 2 — Returning User:
/feed → sees NEW badge → clicks "View Patch Card" → reads all 7 sections

Flow 3 — Checking Old Patch:
/game/valorant → clicks "Previous patches" → selects older version → reads that card

ADDITIONAL REQUIREMENTS
- All routes behind auth guard except /auth — redirect unauthenticated users to /auth
- Supabase Row Level Security: users can only read their own user_game_subscriptions rows
- patch_cards table is readable by any authenticated user
- games table is readable by any authenticated user
- No admin UI needed in MVP
- Responsive layout: works on desktop and mobile browsers
- Use skeleton loaders on all data-fetching screens
- Error state: if patch card fails to load, show "Card unavailable — check back soon"
```

---

## MVP Feature Set

| # | Feature | Why it's in MVP |
|---|---|---|
| F1 | Game Feed | Core landing surface — card per game with patch TL;DR |
| F2 | Full Patch Card View | Core value — all 7 sections with color-coded labels |
| F3 | Game Subscriptions | Personalizes the feed, gates the product |
| F4 | Patch History | Lets users reference old patches (competitive players need this) |
| F5 | Auth | Required to persist preferences |

**Out of scope (v2):** Tier lists, coaching, improvement plans, Telegram per-user notifications, custom game additions, mobile app.

---

## Backend Work (Before or Alongside Loveable)

These parts Loveable cannot build. All are based on existing scripts.

### 1. Adapt fetch_updates.py to write to Supabase
```python
# Add to top of fetch_updates.py:
from supabase import create_client
import os
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Replace the json.dump state save with:
supabase.table('patch_cards').upsert({
    'game_id': game_id,
    'version': version,
    'tldr': tldr,
    'card_markdown': card,
    'patch_date': ts_now,
    'push_sent': False
}, on_conflict='game_id,version').execute()
```

### 2. Seed games table (one-time)
Run once to populate Supabase from your existing games.json:
```python
import json
from supabase import create_client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
games = json.load(open('games.json'))
for g in games:
    supabase.table('games').upsert(g).execute()
```

### 3. Seed patch_cards table (one-time)
Import the current state.json data so Loveable has live data on day one.

### 4. Daily cron
Existing run_daily.py + Windows Task Scheduler works for local dev. For production, migrate to Render cron job, Railway, or Supabase Edge Function cron.

---

## Positioning

> **PatchPulse** turns every game patch into a 60-second meta briefing — structured update cards that tell competitive players exactly what changed, what's OP, and what to play, without reading a single line of official patch notes. Built for serious ranked players across Valorant, Overwatch 2, League of Legends, Fortnite, and Helldivers 2 who lose ELO because they're playing last patch's meta. The alternative takes 20+ minutes and gives you no verdict; PatchPulse hands you the verdict first.

---

## Do This Order

1. Create Supabase project
2. Run the Supabase data model SQL (tables above)
3. Seed games table from games.json
4. Adapt fetch_updates.py to write to Supabase + run it once (seeds patch_cards)
5. Paste the Loveable prompt above into lovable.dev
6. Connect Loveable to your Supabase project
7. Test: sign up → subscribe to games → view patch cards

Loveable will have real data from step 4 and render actual patch cards on first load.
