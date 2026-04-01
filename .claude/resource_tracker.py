#!/usr/bin/env python3
"""
resource_tracker.py — AI OS Resource Impact Tracker
======================================================
Estimates and permanently stores water (mL) and energy (Wh) for every AI
request routed through run.py, chain.py, and the Claude Code IDE session.

Coefficients are per-token estimates from published academic sources:
  - Energy: Luccioni et al. 2023 "Power Hungry Processing: Watts Driving
    the Cost of AI Deployment?" (https://arxiv.org/abs/2311.16863)
  - Water:  Li et al. 2023 "Making AI Less Thirsty: Uncovering and
    Addressing the Secret Water Footprint of AI Models"
    (https://arxiv.org/abs/2304.03271)
  - Local GPU estimate: 350W RTX-class GPU at ~100 tok/s = 0.972 Wh/1K tokens
    (empirical, conservative side for consumer hardware)

These are directional estimates, not metered readings. They are permanently
accumulated so the lifetime counter grows with every request.

Usage (CLI)
-----------
    python resource_tracker.py report        # lifetime + 7-day chart + model breakdown
    python resource_tracker.py today         # today only (hook-friendly)
    python resource_tracker.py bootstrap     # backfill from stats-cache.json + run_log.jsonl
    python resource_tracker.py kv           # Vonnegut-voice lifetime summary

Programmatic API
----------------
    from resource_tracker import record
    record(model="claude-sonnet-4-6", backend="claude",
           input_tokens=500, output_tokens=200,
           ts="2026-03-30T12:00:00Z", agent="CSO-Strategy")
"""

from __future__ import annotations

import json
import sqlite3
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

# ── Carbon & human-scale constants ───────────────────────────────────────────
#
# CO2 intensity: US EPA eGRID 2022 national average = 0.386 kg CO2/kWh.
# Source: https://www.epa.gov/egrid
# Note: Actual cloud datacenter intensity may be lower due to renewable
# commitments (Anthropic, Google), but we use conservative US average.
# Formula: co2_g = energy_wh * CO2_G_PER_WH
CO2_G_PER_WH = 0.386  # grams CO2 per Wh

# Human-scale benchmarks (energy in Wh, water in mL per unit)
# Sources:
#   Google search energy: IEA "The carbon footprint of streaming" 2020
#   Email energy: Berners-Lee "How Bad Are Bananas?" 2020
#   Netflix streaming: Netflix 2022 Environmental Social Governance Report
#   Driving: EPA fuel economy (avg 25 MPG gasoline car, 33.7 kWh/gal)
#   Water benchmarks: scaled from Li et al. 2023 + general literature
HUMAN_BENCHMARKS = {
    "Google searches":       {"energy_wh": 0.30,  "water_ml": 0.10},
    "plain text emails":     {"energy_wh": 4.00,  "water_ml": 0.50},
    "mins of Netflix":       {"energy_wh": 1.28,  "water_ml": 0.08},
    "miles driven (avg car)":{"energy_wh": 570.0, "water_ml": 1.00},
    "phone charges":         {"energy_wh": 8.00,  "water_ml": 0.50},
}

# ── Paths ─────────────────────────────────────────────────────────────────────

CLAUDE_DIR  = Path.home() / ".claude"
DB_PATH     = CLAUDE_DIR / "resource_tracker.db"
STATS_FILE  = CLAUDE_DIR / "stats-cache.json"
RUN_LOG     = CLAUDE_DIR / "run_log.jsonl"
OLLAMA_LOG  = CLAUDE_DIR / "ollama_usage.jsonl"

# ── Resource coefficients ─────────────────────────────────────────────────────
#
# Energy: Wh per 1,000 tokens.
# Water:  mL per 1,000 tokens.
#
# Sources:
#   Cloud (Claude) — Luccioni 2023 Table 4: large generative models average
#     ~0.3 kWh per million tokens at inference; scaled per model tier.
#     Water ratio from Li 2023: ~36 mL / million tokens for US datacenters
#     (WUE ~1.6 L/kWh * ~22 Wh/M tokens).
#   Local (Ollama) — Consumer GPU 350W at ~100 tok/s: 3.5 W·s/tok = 0.00097 Wh/tok.
#     Water: air-cooled consumer PC, effectively 0 datacenter water.
#     Set to 0.001 mL/1K tokens as negligible-but-non-zero.

COEFFICIENTS: dict[str, dict[str, float]] = {
    # ── Claude API models ──────────────────────────────────────────────────
    # Sonnet: mid-tier; estimated 0.30 Wh/1K, 36 mL/M = 0.036 mL/1K
    "claude-sonnet-4-6":           {"energy_wh": 0.30,  "water_ml": 0.036},
    "claude-sonnet-4-5-20250929":  {"energy_wh": 0.30,  "water_ml": 0.036},
    # Opus: largest model; ~3x Sonnet energy estimate
    "claude-opus-4-6":             {"energy_wh": 0.90,  "water_ml": 0.108},
    "claude-opus-4-5-20251101":    {"energy_wh": 0.90,  "water_ml": 0.108},
    # Haiku: smallest Claude; ~1/5th Sonnet
    "claude-haiku-4-5-20251001":   {"energy_wh": 0.06,  "water_ml": 0.007},
    # ── Ollama local models ────────────────────────────────────────────────
    # Local GPU (350W, ~100 tok/s) = 0.972 Wh/1K. Air-cooled, minimal water.
    "gemma3:1b":                   {"energy_wh": 0.12,  "water_ml": 0.001},
    "gemma3:4b":                   {"energy_wh": 0.35,  "water_ml": 0.001},
    "llama3.1:latest":             {"energy_wh": 0.80,  "water_ml": 0.001},
    "llama3.2:3b":                 {"energy_wh": 0.25,  "water_ml": 0.001},
    "qwen2.5-coder:7b":            {"energy_wh": 0.55,  "water_ml": 0.001},
    "deepseek-r1:latest":          {"energy_wh": 0.97,  "water_ml": 0.001},
    "deepseek-coder-v2:16b":       {"energy_wh": 0.97,  "water_ml": 0.001},
    "mistral:7b":                  {"energy_wh": 0.55,  "water_ml": 0.001},
    "phi3:medium":                 {"energy_wh": 0.60,  "water_ml": 0.001},
}

# Defaults for unknown models (conservative)
_DEFAULT_CLOUD = {"energy_wh": 0.30, "water_ml": 0.036}
_DEFAULT_LOCAL = {"energy_wh": 0.70, "water_ml": 0.001}


def _coeff(model: str, backend: str) -> dict[str, float]:
    """Return coefficient dict for a model. Falls back to default by backend."""
    # Direct match
    if model in COEFFICIENTS:
        return COEFFICIENTS[model]
    # Partial match (e.g. "claude-sonnet" in "claude-sonnet-4-6-...")
    for key, val in COEFFICIENTS.items():
        if key in model or model in key:
            return val
    return _DEFAULT_CLOUD if backend == "claude" else _DEFAULT_LOCAL


# ── Database ──────────────────────────────────────────────────────────────────

_SCHEMA = """
CREATE TABLE IF NOT EXISTS requests (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          TEXT    NOT NULL,          -- ISO 8601 UTC timestamp
    date        TEXT    NOT NULL,          -- YYYY-MM-DD (for date-range queries)
    model       TEXT    NOT NULL,          -- full model ID
    backend     TEXT    NOT NULL,          -- 'claude' | 'ollama'
    agent       TEXT    DEFAULT '',
    input_tok   INTEGER DEFAULT 0,
    output_tok  INTEGER DEFAULT 0,
    total_tok   INTEGER DEFAULT 0,
    energy_wh   REAL    DEFAULT 0.0,
    water_ml    REAL    DEFAULT 0.0,
    source      TEXT    DEFAULT 'live'     -- 'live' | 'bootstrap'
);
CREATE INDEX IF NOT EXISTS idx_requests_date  ON requests(date);
CREATE INDEX IF NOT EXISTS idx_requests_model ON requests(model);
"""


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    conn.commit()
    return conn


# ── Core API ──────────────────────────────────────────────────────────────────

def record(
    model: str,
    backend: str,
    input_tokens: int,
    output_tokens: int,
    ts: Optional[str] = None,
    agent: str = "",
    source: str = "live",
) -> None:
    """
    Record one AI request to the SQLite database. Non-blocking — any DB error
    is swallowed so a tracker failure never blocks an AI response.

    Args:
        model:         Full model ID (e.g. "claude-sonnet-4-6" or "llama3.1:latest")
        backend:       "claude" | "ollama"
        input_tokens:  Input token count (0 if unknown)
        output_tokens: Output token count (0 if unknown)
        ts:            ISO 8601 UTC string; defaults to now
        agent:         Agent name for attribution
        source:        "live" (default) | "bootstrap"
    """
    try:
        if ts is None:
            ts = datetime.now(timezone.utc).isoformat()
        day = ts[:10]  # YYYY-MM-DD
        total = input_tokens + output_tokens
        coeff = _coeff(model, backend)
        energy = (total / 1000.0) * coeff["energy_wh"]
        water  = (total / 1000.0) * coeff["water_ml"]

        conn = _get_conn()
        conn.execute(
            "INSERT INTO requests (ts, date, model, backend, agent, "
            "input_tok, output_tok, total_tok, energy_wh, water_ml, source) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (ts, day, model, backend, agent,
             input_tokens, output_tokens, total,
             energy, water, source),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass  # Never block the caller


# ── Bootstrap ─────────────────────────────────────────────────────────────────

def bootstrap_from_stats_cache() -> int:
    """
    Backfill resource history from Claude Code's stats-cache.json.
    Distributes daily token totals (dailyModelTokens) as one row per
    model per day. Skips days already present in the DB (idempotent).
    Returns number of rows inserted.
    """
    if not STATS_FILE.exists():
        return 0

    try:
        stats = json.loads(STATS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return 0

    # Build per-model coefficient map
    conn = _get_conn()
    inserted = 0

    for entry in stats.get("dailyModelTokens", []):
        day = entry.get("date", "")
        if not day:
            continue
        ts_day = f"{day}T12:00:00+00:00"  # noon UTC as representative time

        for model, tokens in entry.get("tokensByModel", {}).items():
            if tokens <= 0:
                continue
            # Check not already bootstrapped for this day+model
            existing = conn.execute(
                "SELECT COUNT(*) FROM requests WHERE date=? AND model=? AND source='bootstrap'",
                (day, model),
            ).fetchone()[0]
            if existing > 0:
                continue

            coeff = _coeff(model, "claude")
            energy = (tokens / 1000.0) * coeff["energy_wh"]
            water  = (tokens / 1000.0) * coeff["water_ml"]

            conn.execute(
                "INSERT INTO requests (ts, date, model, backend, agent, "
                "input_tok, output_tok, total_tok, energy_wh, water_ml, source) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (ts_day, day, model, "claude", "bootstrap",
                 0, 0, tokens, energy, water, "bootstrap"),
            )
            inserted += 1

    conn.commit()
    conn.close()
    return inserted


def bootstrap_from_run_log() -> int:
    """
    Backfill from run_log.jsonl (programmatic runs via run.py).
    Idempotent — uses ts+model as dedup key, source='bootstrap'.
    """
    if not RUN_LOG.exists():
        return 0

    conn = _get_conn()
    inserted = 0

    for line in RUN_LOG.read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(line)
        except Exception:
            continue

        ts    = r.get("ts", "")
        model = r.get("model", "")
        if not ts or not model:
            continue

        # Check dedup
        existing = conn.execute(
            "SELECT COUNT(*) FROM requests WHERE ts=? AND model=? AND source='bootstrap'",
            (ts, model),
        ).fetchone()[0]
        if existing > 0:
            continue

        inp  = r.get("input_tokens", 0)
        out  = r.get("output_tokens", 0)
        backend = r.get("backend", "claude")
        agent   = r.get("agent", "")
        total   = inp + out
        coeff   = _coeff(model, backend)
        energy  = (total / 1000.0) * coeff["energy_wh"]
        water   = (total / 1000.0) * coeff["water_ml"]
        day     = ts[:10]

        conn.execute(
            "INSERT INTO requests (ts, date, model, backend, agent, "
            "input_tok, output_tok, total_tok, energy_wh, water_ml, source) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (ts, day, model, backend, agent,
             inp, out, total, energy, water, "bootstrap"),
        )
        inserted += 1

    conn.commit()
    conn.close()
    return inserted


def bootstrap_from_ollama_log() -> int:
    """
    Backfill from ollama_usage.jsonl (Ollama runs logged by token_tracker.py).
    """
    if not OLLAMA_LOG.exists():
        return 0

    conn = _get_conn()
    inserted = 0

    for line in OLLAMA_LOG.read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(line)
        except Exception:
            continue

        ts    = r.get("ts", "")
        model = r.get("model", "")
        if not ts or not model:
            continue

        existing = conn.execute(
            "SELECT COUNT(*) FROM requests WHERE ts=? AND model=? AND source='bootstrap'",
            (ts, model),
        ).fetchone()[0]
        if existing > 0:
            continue

        inp   = r.get("tokens_in",  0)
        out   = r.get("tokens_out", 0)
        total = inp + out
        coeff = _coeff(model, "ollama")
        energy = (total / 1000.0) * coeff["energy_wh"]
        water  = (total / 1000.0) * coeff["water_ml"]
        day    = ts[:10]

        conn.execute(
            "INSERT INTO requests (ts, date, model, backend, agent, "
            "input_tok, output_tok, total_tok, energy_wh, water_ml, source) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (ts, day, model, "ollama", "",
             inp, out, total, energy, water, "bootstrap"),
        )
        inserted += 1

    conn.commit()
    conn.close()
    return inserted


# ── Query helpers ─────────────────────────────────────────────────────────────

def _lifetime(conn: sqlite3.Connection) -> dict:
    row = conn.execute(
        "SELECT COUNT(*) AS reqs, SUM(total_tok) AS tok, "
        "SUM(energy_wh) AS energy, SUM(water_ml) AS water "
        "FROM requests"
    ).fetchone()
    return {
        "requests": row["reqs"] or 0,
        "tokens":   row["tok"]  or 0,
        "energy":   row["energy"] or 0.0,
        "water":    row["water"]  or 0.0,
    }


def _today_stats(conn: sqlite3.Connection) -> dict:
    today = date.today().isoformat()
    row = conn.execute(
        "SELECT COUNT(*) AS reqs, SUM(total_tok) AS tok, "
        "SUM(energy_wh) AS energy, SUM(water_ml) AS water "
        "FROM requests WHERE date=?", (today,)
    ).fetchone()
    return {
        "date":     today,
        "requests": row["reqs"] or 0,
        "tokens":   row["tok"]  or 0,
        "energy":   row["energy"] or 0.0,
        "water":    row["water"]  or 0.0,
    }


def _daily_rows(conn: sqlite3.Connection, days: int = 7) -> list[dict]:
    cutoff = (date.today() - timedelta(days=days - 1)).isoformat()
    rows = conn.execute(
        "SELECT date, COUNT(*) AS reqs, SUM(total_tok) AS tok, "
        "SUM(energy_wh) AS energy, SUM(water_ml) AS water "
        "FROM requests WHERE date >= ? "
        "GROUP BY date ORDER BY date DESC",
        (cutoff,),
    ).fetchall()
    return [dict(r) for r in rows]


def _model_rows(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT model, backend, COUNT(*) AS reqs, SUM(total_tok) AS tok, "
        "SUM(energy_wh) AS energy, SUM(water_ml) AS water "
        "FROM requests "
        "GROUP BY model ORDER BY energy DESC"
    ).fetchall()
    return [dict(r) for r in rows]


# ── Formatting ────────────────────────────────────────────────────────────────

def _fmt_energy(wh: float) -> str:
    if wh >= 1000:
        return f"{wh/1000:.2f} kWh"
    if wh >= 1:
        return f"{wh:.2f} Wh"
    return f"{wh*1000:.1f} mWh"


def _fmt_water(ml: float) -> str:
    if ml >= 1000:
        return f"{ml/1000:.2f} L"
    if ml >= 1:
        return f"{ml:.1f} mL"
    return f"{ml*1000:.1f} uL"


def _fmt_tokens(n: int) -> str:
    if n >= 1_000_000:
        return f"{n/1_000_000:.2f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def _fmt_co2(g: float) -> str:
    if g >= 1000:
        return f"{g/1000:.2f} kg CO2"
    if g >= 1:
        return f"{g:.1f} g CO2"
    return f"{g*1000:.0f} mg CO2"


def _human_scale_lines(energy_wh: float, water_ml: float) -> list[str]:
    """Return human-readable equivalence strings for energy and water totals."""
    lines = []
    for label, bench in HUMAN_BENCHMARKS.items():
        e_equiv = energy_wh / bench["energy_wh"] if bench["energy_wh"] else 0
        if e_equiv >= 0.01:
            lines.append(f"    {e_equiv:>8.1f}x  {label}")
    # Water comparison — pick the most readable unit
    if water_ml >= 1:
        glasses = water_ml / 250.0
        drops   = water_ml / 0.05
        if glasses >= 0.1:
            lines.append(f"    {glasses:>8.2f}x  glasses of water (250 mL each)")
        else:
            lines.append(f"    {drops:>8.0f}x  drops of water (~0.05 mL each)")
    return lines


def _bar(val: float, max_val: float, width: int = 20) -> str:
    if max_val <= 0:
        return f"[{'-' * width}]"
    filled = int(min(val / max_val, 1.0) * width)
    return f"[{'#' * filled}{'-' * (width - filled)}]"


# ── CLI commands ──────────────────────────────────────────────────────────────

def cmd_today() -> None:
    conn = _get_conn()
    t = _today_stats(conn)
    conn.close()
    co2 = t["energy"] * CO2_G_PER_WH
    print(f"\n  Today ({t['date']})")
    print(f"  Requests : {t['requests']}")
    print(f"  Tokens   : {_fmt_tokens(t['tokens'])}")
    print(f"  Energy   : {_fmt_energy(t['energy'])}")
    print(f"  Water    : {_fmt_water(t['water'])}")
    print(f"  CO2      : {_fmt_co2(co2)}")
    if t["energy"] > 0:
        scale = _human_scale_lines(t["energy"], t["water"])
        for line in scale:
            print(f" {line}")
    print()


def cmd_report() -> None:
    conn = _get_conn()
    lt   = _lifetime(conn)
    td   = _today_stats(conn)
    days = _daily_rows(conn, days=7)
    mods = _model_rows(conn)
    conn.close()

    SEP = "-" * 58

    # -- Today ----------------------------------------------------------------
    print(f"\n  {SEP}")
    print(f"  RESOURCE IMPACT -- Today ({td['date']})")
    print(f"  {SEP}")
    print(f"  Requests : {td['requests']}")
    print(f"  Tokens   : {_fmt_tokens(td['tokens'])}")
    print(f"  Energy   : {_fmt_energy(td['energy'])}")
    print(f"  Water    : {_fmt_water(td['water'])}")
    print()

    # -- Lifetime -------------------------------------------------------------
    print(f"  {SEP}")
    print(f"  LIFETIME TOTALS (since first request)")
    print(f"  {SEP}")
    print(f"  Total Requests : {lt['requests']:,}")
    print(f"  Total Tokens   : {_fmt_tokens(lt['tokens'])}")
    print(f"  Total Energy   : {_fmt_energy(lt['energy'])}")
    print(f"  Total Water    : {_fmt_water(lt['water'])}")
    print()

    # -- 7-day chart ----------------------------------------------------------
    if days:
        max_e = max(d["energy"] for d in days) or 1.0
        print(f"  {SEP}")
        print(f"  LAST 7 DAYS")
        print(f"  {SEP}")
        print(f"  {'Date':<12} {'Energy':>10}  {'Bar':<22}  {'Water':>8}")
        print(f"  {'-'*58}")
        for d in sorted(days, key=lambda x: x["date"], reverse=True):
            bar = _bar(d["energy"], max_e, width=20)
            print(
                f"  {d['date']:<12} {_fmt_energy(d['energy']):>10}  {bar}  "
                f"{_fmt_water(d['water']):>8}"
            )
        print()

    # -- Model breakdown ------------------------------------------------------
    if mods:
        print(f"  {SEP}")
        print(f"  BY MODEL")
        print(f"  {SEP}")
        print(f"  {'Model':<36} {'Reqs':>5} {'Tokens':>9} {'Energy':>10} {'Water':>8}")
        print(f"  {'-'*72}")
        for m in mods:
            name = m["model"][:35]
            print(
                f"  {name:<36} {m['reqs']:>5} "
                f"{_fmt_tokens(m['tok'] or 0):>9} "
                f"{_fmt_energy(m['energy'] or 0.0):>10} "
                f"{_fmt_water(m['water'] or 0.0):>8}"
            )
        print()

    # -- Carbon footprint -----------------------------------------------------
    co2 = lt["energy"] * CO2_G_PER_WH
    print(f"  {SEP}")
    print(f"  CARBON FOOTPRINT (lifetime)")
    print(f"  {SEP}")
    print(f"  CO2 equivalent : {_fmt_co2(co2)}")
    print(f"  (US avg grid: 0.386 kg CO2/kWh | EPA eGRID 2022)")
    print()

    # -- Human scale ----------------------------------------------------------
    print(f"  {SEP}")
    print(f"  IN HUMAN TERMS (lifetime energy + water)")
    print(f"  {SEP}")
    scale_lines = _human_scale_lines(lt["energy"], lt["water"])
    for line in scale_lines:
        print(f" {line}")
    print()

    # -- Source note ----------------------------------------------------------
    print(f"  Sources: Luccioni 2023 (energy) | Li 2023 (water) | EPA eGRID 2022 (CO2)")
    print(f"  Note: Estimates only -- not metered readings. Directionally accurate.")
    print()


def cmd_kv() -> str:
    """
    Return lifetime stats as raw data for Vonnegut-voice formatting.
    Prints a plain summary that the KV skill or Claude can rewrite.
    """
    conn = _get_conn()
    lt = _lifetime(conn)
    conn.close()
    co2 = lt["energy"] * CO2_G_PER_WH
    scale = _human_scale_lines(lt["energy"], lt["water"])
    scale_str = " | ".join(s.strip() for s in scale) if scale else ""
    summary = (
        f"Lifetime AI request impact: {lt['requests']:,} total requests, "
        f"{_fmt_tokens(lt['tokens'])} tokens processed, "
        f"{_fmt_energy(lt['energy'])} of energy consumed, "
        f"{_fmt_water(lt['water'])} of water used, "
        f"{_fmt_co2(co2)} of CO2 emitted. "
        f"Human scale: {scale_str}. "
        f"Estimates from Luccioni 2023, Li 2023, EPA eGRID 2022. "
        f"Not metered. Directionally correct."
    )
    print(summary)
    return summary


SNAPSHOT_PATH = CLAUDE_DIR / "resource_snapshot.md"


def _week_stats(conn: sqlite3.Connection, weeks_ago: int = 0) -> dict:
    """Return aggregated stats for a given ISO week (0 = this week, 1 = last week)."""
    today = date.today()
    # Start of the target week (Monday)
    start = today - timedelta(days=today.weekday()) - timedelta(weeks=weeks_ago)
    end   = start + timedelta(days=6)
    row = conn.execute(
        "SELECT COUNT(*) AS reqs, SUM(total_tok) AS tok, "
        "SUM(energy_wh) AS energy, SUM(water_ml) AS water "
        "FROM requests WHERE date >= ? AND date <= ?",
        (start.isoformat(), end.isoformat()),
    ).fetchone()
    return {
        "start":    start.isoformat(),
        "end":      end.isoformat(),
        "requests": row["reqs"]   or 0,
        "tokens":   row["tok"]    or 0,
        "energy":   row["energy"] or 0.0,
        "water":    row["water"]  or 0.0,
    }


def _trend(current: float, previous: float) -> str:
    if previous <= 0:
        return "(new)"
    delta = (current - previous) / previous * 100
    if delta > 5:
        return f"(+{delta:.0f}% vs last week)"
    if delta < -5:
        return f"({delta:.0f}% vs last week)"
    return "(~flat vs last week)"


def _snapshot_week_key(start: str) -> str:
    """Return the week key string used as an anchor in the snapshot file."""
    return f"## Week of {start}"


def _already_logged(start: str) -> bool:
    """True if this week's entry already exists in the snapshot file."""
    if not SNAPSHOT_PATH.exists():
        return False
    return _snapshot_week_key(start) in SNAPSHOT_PATH.read_text(encoding="utf-8")


def cmd_snapshot(force: bool = False) -> None:
    """
    Append a new weekly entry to ~/.claude/resource_snapshot.md.
    Each week gets one entry. The file grows forever — history is never deleted.
    Auto-skips if this week's entry already exists, unless force=True.
    """
    conn = _get_conn()
    lt      = _lifetime(conn)
    this_wk = _week_stats(conn, weeks_ago=0)
    last_wk = _week_stats(conn, weeks_ago=1)
    mods    = _model_rows(conn)
    conn.close()

    # Skip if this week is already logged
    if not force and _already_logged(this_wk["start"]):
        return

    co2_life = lt["energy"] * CO2_G_PER_WH
    co2_week = this_wk["energy"] * CO2_G_PER_WH
    scale    = _human_scale_lines(lt["energy"], lt["water"])
    today_str = date.today().isoformat()

    # ── Build the new entry block ─────────────────────────────────────────
    entry = [
        f"",
        f"---",
        f"",
        f"{_snapshot_week_key(this_wk['start'])} (logged {today_str})",
        f"",
        f"| Metric | This Week | Last Week | Trend |",
        f"|--------|-----------|-----------|-------|",
        f"| Requests | {this_wk['requests']:,} | {last_wk['requests']:,} | {_trend(this_wk['requests'], last_wk['requests'])} |",
        f"| Tokens | {_fmt_tokens(this_wk['tokens'])} | {_fmt_tokens(last_wk['tokens'])} | {_trend(this_wk['tokens'], last_wk['tokens'])} |",
        f"| Energy | {_fmt_energy(this_wk['energy'])} | {_fmt_energy(last_wk['energy'])} | {_trend(this_wk['energy'], last_wk['energy'])} |",
        f"| Water | {_fmt_water(this_wk['water'])} | {_fmt_water(last_wk['water'])} | {_trend(this_wk['water'], last_wk['water'])} |",
        f"| CO2 | {_fmt_co2(co2_week)} | {_fmt_co2(last_wk['energy'] * CO2_G_PER_WH)} | {_trend(co2_week, last_wk['energy'] * CO2_G_PER_WH)} |",
        f"",
        f"**Lifetime at time of entry:** {lt['requests']:,} requests | "
        f"{_fmt_tokens(lt['tokens'])} tokens | "
        f"{_fmt_energy(lt['energy'])} | "
        f"{_fmt_water(lt['water'])} | "
        f"{_fmt_co2(co2_life)}",
        f"",
        f"**In human terms (lifetime):** " + " | ".join(s.strip() for s in scale),
        f"",
    ]

    # ── Create file with header if it doesn't exist yet ───────────────────
    if not SNAPSHOT_PATH.exists():
        header = [
            f"# AI OS Resource Impact — History Log",
            f"",
            f"A permanent, append-only record of weekly AI resource usage.",
            f"One entry per week. The file grows forever. History is never deleted.",
            f"",
            f"**Sources:** Luccioni 2023 (energy) | Li 2023 (water) | EPA eGRID 2022 (CO2)",
            f"**Note:** Estimates only — not metered readings. Directionally accurate.",
            f"",
        ]
        SNAPSHOT_PATH.write_text("\n".join(header), encoding="utf-8")

    # ── Append the entry ──────────────────────────────────────────────────
    with SNAPSHOT_PATH.open("a", encoding="utf-8") as f:
        f.write("\n".join(entry))

    print(f"  Entry for week of {this_wk['start']} appended to {SNAPSHOT_PATH}")


def cmd_bootstrap() -> None:
    print("  Bootstrapping resource history...")
    n1 = bootstrap_from_stats_cache()
    print(f"  stats-cache.json : {n1} rows inserted")
    n2 = bootstrap_from_run_log()
    print(f"  run_log.jsonl    : {n2} rows inserted")
    n3 = bootstrap_from_ollama_log()
    print(f"  ollama_usage.jsonl : {n3} rows inserted")
    total = n1 + n2 + n3
    print(f"  Total            : {total} rows added to {DB_PATH}")
    if total > 0:
        conn = _get_conn()
        lt = _lifetime(conn)
        conn.close()
        print(f"  Lifetime totals  : {_fmt_energy(lt['energy'])} energy, "
              f"{_fmt_water(lt['water'])} water, "
              f"{_fmt_tokens(lt['tokens'])} tokens")
    print()


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    args = sys.argv[1:]
    cmd  = args[0] if args else "report"

    if cmd == "today":
        cmd_today()
    elif cmd == "report":
        cmd_report()
    elif cmd == "kv":
        cmd_kv()
    elif cmd == "bootstrap":
        cmd_bootstrap()
    elif cmd == "snapshot":
        cmd_snapshot(force=True)
    elif cmd == "lifetime":
        conn = _get_conn()
        lt = _lifetime(conn)
        conn.close()
        print(f"\n  Lifetime: {lt['requests']:,} requests | "
              f"{_fmt_tokens(lt['tokens'])} tokens | "
              f"{_fmt_energy(lt['energy'])} | "
              f"{_fmt_water(lt['water'])}\n")
    else:
        print("Commands: report | today | lifetime | bootstrap | snapshot | kv")

    # Auto-refresh snapshot if stale (runs silently on every CLI invocation)
    try:
        cmd_snapshot(force=False)
    except Exception:
        pass
