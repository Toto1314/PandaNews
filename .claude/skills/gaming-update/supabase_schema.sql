-- PatchPulse — Supabase Schema
-- Run this in your Supabase SQL editor before seeding data.
-- Project: https://supabase.com → New Project → SQL Editor → paste + run

-- ── GAMES ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS games (
    id          TEXT PRIMARY KEY,              -- e.g. "valorant"
    name        TEXT NOT NULL,                 -- e.g. "Valorant"
    enabled     BOOLEAN DEFAULT true,
    search_query TEXT,
    patch_url   TEXT,
    created_at  TIMESTAMPTZ DEFAULT now()
);

-- ── PATCH CARDS ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS patch_cards (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    game_id       TEXT REFERENCES games(id) ON DELETE CASCADE,
    version       TEXT NOT NULL,               -- e.g. "12.05"
    patch_date    TIMESTAMPTZ,
    tldr          TEXT,
    card_markdown TEXT NOT NULL,               -- full raw markdown card
    sections      JSONB,                       -- parsed sections (optional)
    push_sent     BOOLEAN DEFAULT false,
    created_at    TIMESTAMPTZ DEFAULT now(),
    UNIQUE(game_id, version)
);

-- ── USER GAME SUBSCRIPTIONS ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS user_game_subscriptions (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    game_id    TEXT REFERENCES games(id) ON DELETE CASCADE,
    notify     BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, game_id)
);

-- ── ROW LEVEL SECURITY ─────────────────────────────────────────────────────
ALTER TABLE games                    ENABLE ROW LEVEL SECURITY;
ALTER TABLE patch_cards              ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_game_subscriptions  ENABLE ROW LEVEL SECURITY;

-- games: any authenticated user can read
CREATE POLICY "games_read" ON games
    FOR SELECT TO authenticated USING (true);

-- patch_cards: any authenticated user can read
CREATE POLICY "patch_cards_read" ON patch_cards
    FOR SELECT TO authenticated USING (true);

-- user_game_subscriptions: users can only see + edit their own rows
CREATE POLICY "subs_select" ON user_game_subscriptions
    FOR SELECT TO authenticated USING (auth.uid() = user_id);

CREATE POLICY "subs_insert" ON user_game_subscriptions
    FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);

CREATE POLICY "subs_update" ON user_game_subscriptions
    FOR UPDATE TO authenticated USING (auth.uid() = user_id);

CREATE POLICY "subs_delete" ON user_game_subscriptions
    FOR DELETE TO authenticated USING (auth.uid() = user_id);

-- ── SERVICE ROLE WRITE ACCESS (for backend scripts) ───────────────────────
-- Your seed scripts and fetch_updates.py use SUPABASE_SERVICE_KEY which
-- bypasses RLS automatically — no extra policies needed for backend writes.
