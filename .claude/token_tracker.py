"""
Token Budget Tracker
====================
Reads Claude Code's stats-cache.json and session-meta files to report
real token usage and estimated cost, with configurable daily/monthly budgets.

Usage
-----
    python token_tracker.py report          # full report
    python token_tracker.py today           # today's stats (hook-friendly)
    python token_tracker.py check           # exit 1 + warning if over budget
    python token_tracker.py budget          # show current budget config
    python token_tracker.py budget set daily 50000
    python token_tracker.py budget set monthly 500000
    python token_tracker.py sessions [N]   # last N sessions (default 10)
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, date, timedelta, timezone
from pathlib import Path
from typing import Optional

# ── Paths ─────────────────────────────────────────────────────────────────────
CLAUDE_DIR    = Path.home() / ".claude"
STATS_FILE    = CLAUDE_DIR / "stats-cache.json"
SESSION_DIR   = CLAUDE_DIR / "usage-data" / "session-meta"
BUDGET_FILE   = CLAUDE_DIR / "token_budget.json"

# ── Pricing (USD per 1M tokens) ───────────────────────────────────────────────
# Source: Anthropic pricing page (update if rates change)
PRICING: dict[str, dict[str, float]] = {
    "claude-sonnet-4-6": {
        "input":          3.00,
        "output":        15.00,
        "cache_write":    3.75,
        "cache_read":     0.30,
    },
    "claude-opus-4-6": {
        "input":         15.00,
        "output":        75.00,
        "cache_write":   18.75,
        "cache_read":     1.50,
    },
    "claude-haiku-4-5-20251001": {
        "input":          0.80,
        "output":          4.00,
        "cache_write":     1.00,
        "cache_read":      0.08,
    },
    # Fallback for older model IDs
    "claude-sonnet-4-5-20250929": {
        "input":          3.00,
        "output":        15.00,
        "cache_write":    3.75,
        "cache_read":     0.30,
    },
    "claude-opus-4-5-20251101": {
        "input":         15.00,
        "output":        75.00,
        "cache_write":   18.75,
        "cache_read":     1.50,
    },
}

DEFAULT_PRICING = {"input": 3.00, "output": 15.00, "cache_write": 3.75, "cache_read": 0.30}

DEFAULT_BUDGET = {
    "daily_tokens":   100_000,
    "monthly_tokens": 2_000_000,
    "daily_cost_usd":     5.00,
    "monthly_cost_usd":  50.00,
    "warn_pct":           80,      # warn at this % of limit
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def _price(model: str) -> dict[str, float]:
    for key in PRICING:
        if key in model or model in key:
            return PRICING[key]
    return DEFAULT_PRICING

def _cost(tokens: int, rate_per_mtok: float) -> float:
    return tokens / 1_000_000 * rate_per_mtok

def _fmt_tokens(n: int) -> str:
    if n >= 1_000_000:
        return f"{n/1_000_000:.2f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)

def _bar(pct: float, width: int = 30) -> str:
    filled = int(min(pct, 100) / 100 * width)
    color = "!" if pct >= 90 else ("~" if pct >= 80 else "#")
    return f"[{''.join([color] * filled)}{'-' * (width - filled)}] {pct:.0f}%"

def _load_stats() -> dict:
    if not STATS_FILE.exists():
        return {}
    return json.loads(STATS_FILE.read_text(encoding="utf-8"))

def _load_budget() -> dict:
    if BUDGET_FILE.exists():
        saved = json.loads(BUDGET_FILE.read_text(encoding="utf-8"))
        return {**DEFAULT_BUDGET, **saved}
    return DEFAULT_BUDGET.copy()

def _save_budget(b: dict) -> None:
    BUDGET_FILE.write_text(json.dumps(b, indent=2), encoding="utf-8")

def _load_sessions() -> list[dict]:
    if not SESSION_DIR.exists():
        return []
    sessions = []
    for fp in SESSION_DIR.glob("*.json"):
        try:
            sessions.append(json.loads(fp.read_text(encoding="utf-8")))
        except Exception:
            pass
    return sorted(sessions, key=lambda s: s.get("start_time", ""), reverse=True)

def _today_str() -> str:
    return date.today().isoformat()

def _month_str() -> str:
    return date.today().strftime("%Y-%m")

# ── Core calculations ─────────────────────────────────────────────────────────

def lifetime_stats(stats: dict) -> dict:
    """
    Returns per-model and total lifetime cost from modelUsage.
    modelUsage has full input/output/cacheRead/cacheCreation breakdown.
    """
    model_usage = stats.get("modelUsage", {})
    rows = []
    total_cost = 0.0
    total_input = total_output = total_cache_r = total_cache_w = 0

    for model, u in model_usage.items():
        p = _price(model)
        inp   = u.get("inputTokens", 0)
        out   = u.get("outputTokens", 0)
        c_r   = u.get("cacheReadInputTokens", 0)
        c_w   = u.get("cacheCreationInputTokens", 0)
        cost  = (
            _cost(inp,   p["input"])
          + _cost(out,   p["output"])
          + _cost(c_r,   p["cache_read"])
          + _cost(c_w,   p["cache_write"])
        )
        total_cost  += cost
        total_input += inp
        total_output += out
        total_cache_r += c_r
        total_cache_w += c_w
        rows.append({
            "model": model, "input": inp, "output": out,
            "cache_read": c_r, "cache_write": c_w, "cost": cost,
        })

    return {
        "rows": rows,
        "total_cost":    total_cost,
        "total_input":   total_input,
        "total_output":  total_output,
        "total_cache_r": total_cache_r,
        "total_cache_w": total_cache_w,
    }


def daily_stats(stats: dict, days: int = 30) -> list[dict]:
    """
    Returns per-day token+estimated cost for the last N days.
    dailyModelTokens only has combined input+output (no cache breakdown),
    so we estimate cost using the lifetime i/o ratio per model.
    """
    model_usage = stats.get("modelUsage", {})

    # Compute per-model effective rate (blended input/output, no cache)
    model_rate: dict[str, float] = {}
    for model, u in model_usage.items():
        inp = u.get("inputTokens", 0)
        out = u.get("outputTokens", 0)
        total = inp + out
        if total == 0:
            continue
        p = _price(model)
        blended = (inp / total) * p["input"] + (out / total) * p["output"]
        model_rate[model] = blended

    cutoff = date.today() - timedelta(days=days)
    daily = stats.get("dailyModelTokens", [])

    result = []
    for entry in daily:
        d = date.fromisoformat(entry["date"])
        if d < cutoff:
            continue
        tokens_by_model = entry.get("tokensByModel", {})
        day_tokens = sum(tokens_by_model.values())
        day_cost = sum(
            _cost(t, model_rate.get(m, DEFAULT_PRICING["output"]))
            for m, t in tokens_by_model.items()
        )
        activity = next(
            (a for a in stats.get("dailyActivity", []) if a["date"] == entry["date"]),
            {}
        )
        result.append({
            "date": entry["date"],
            "tokens": day_tokens,
            "cost": day_cost,
            "messages": activity.get("messageCount", 0),
            "tool_calls": activity.get("toolCallCount", 0),
            "sessions": activity.get("sessionCount", 0),
        })

    return sorted(result, key=lambda x: x["date"], reverse=True)


def today_usage(stats: dict) -> dict:
    """
    Returns today's token count + cost. Falls back to session-meta if
    stats-cache hasn't been updated yet today.
    """
    today = _today_str()
    daily = daily_stats(stats, days=1)
    for d in daily:
        if d["date"] == today:
            return d

    # stats-cache lags — compute from session-meta directly
    sessions = _load_sessions()
    today_sessions = [
        s for s in sessions
        if s.get("start_time", "").startswith(today)
    ]
    tokens = sum(
        s.get("input_tokens", 0) + s.get("output_tokens", 0)
        for s in today_sessions
    )
    # Estimate cost at sonnet output rate (conservative)
    cost = _cost(tokens, DEFAULT_PRICING["output"])
    return {
        "date": today, "tokens": tokens, "cost": cost,
        "messages": sum(s.get("user_message_count", 0) for s in today_sessions),
        "tool_calls": sum(sum(s.get("tool_counts", {}).values()) for s in today_sessions),
        "sessions": len(today_sessions),
        "source": "session-meta (stats-cache not yet updated for today)",
    }


def monthly_usage(stats: dict) -> dict:
    month = _month_str()
    daily = daily_stats(stats, days=31)
    rows = [d for d in daily if d["date"].startswith(month)]
    return {
        "month":     month,
        "tokens":    sum(r["tokens"] for r in rows),
        "cost":      sum(r["cost"] for r in rows),
        "messages":  sum(r["messages"] for r in rows),
        "sessions":  sum(r["sessions"] for r in rows),
        "days":      len(rows),
    }

# ── Ollama usage ──────────────────────────────────────────────────────────────

OLLAMA_LOG = CLAUDE_DIR / "ollama_usage.jsonl"


def _load_ollama_runs(days: int = 30) -> list[dict]:
    if not OLLAMA_LOG.exists():
        return []
    cutoff = (date.today() - timedelta(days=days)).isoformat()
    runs = []
    for line in OLLAMA_LOG.read_text(encoding="utf-8").splitlines():
        try:
            entry = json.loads(line)
            if entry.get("ts", "")[:10] >= cutoff:
                runs.append(entry)
        except Exception:
            pass
    return runs


def ollama_today_summary() -> dict:
    today = _today_str()
    runs  = [r for r in _load_ollama_runs(days=1) if r.get("ts", "").startswith(today)]
    return {
        "runs":        len(runs),
        "tokens_in":   sum(r.get("tokens_in", 0)  for r in runs),
        "tokens_out":  sum(r.get("tokens_out", 0) for r in runs),
        "elapsed_sum": sum(r.get("elapsed", 0)    for r in runs),
    }


# ── Commands ──────────────────────────────────────────────────────────────────

def cmd_today(stats: dict) -> None:
    u = today_usage(stats)
    budget = _load_budget()
    tok_pct  = u["tokens"] / budget["daily_tokens"] * 100 if budget["daily_tokens"] else 0
    cost_pct = u["cost"]   / budget["daily_cost_usd"] * 100 if budget["daily_cost_usd"] else 0
    print(f"\n  Today ({u['date']})")
    print(f"  Tokens : {_fmt_tokens(u['tokens'])} / {_fmt_tokens(budget['daily_tokens'])}  {_bar(tok_pct)}")
    print(f"  Cost   : ${u['cost']:.4f} / ${budget['daily_cost_usd']:.2f}  {_bar(cost_pct)}")
    print(f"  Msgs   : {u['messages']}  |  Tools: {u['tool_calls']}  |  Sessions: {u['sessions']}")
    if u.get("source"):
        print(f"  Note   : {u['source']}")
    # Ollama sidebar
    ol = ollama_today_summary()
    if ol["runs"]:
        total_ol = ol["tokens_in"] + ol["tokens_out"]
        print(f"  Ollama : {ol['runs']} runs  |  {_fmt_tokens(total_ol)} tokens  |  {ol['elapsed_sum']:.1f}s  (free)")
    print()


def cmd_check(stats: dict) -> int:
    """Returns 0 (ok) or 1 (over budget). Prints warning if over."""
    u = today_usage(stats)
    budget = _load_budget()
    warn_pct = budget["warn_pct"] / 100

    warnings = []
    if u["tokens"] >= budget["daily_tokens"] * warn_pct:
        warnings.append(
            f"Daily token budget {budget['warn_pct']}% reached: "
            f"{_fmt_tokens(u['tokens'])} / {_fmt_tokens(budget['daily_tokens'])}"
        )
    if u["cost"] >= budget["daily_cost_usd"] * warn_pct:
        warnings.append(
            f"Daily cost budget {budget['warn_pct']}% reached: "
            f"${u['cost']:.4f} / ${budget['daily_cost_usd']:.2f}"
        )

    if warnings:
        for w in warnings:
            print(f"[token_tracker] WARNING: {w}")
        return 1
    return 0


def cmd_report(stats: dict) -> None:
    budget = _load_budget()

    # ── Today ──
    cmd_today(stats)

    # ── This month ──
    mo = monthly_usage(stats)
    tok_pct  = mo["tokens"] / budget["monthly_tokens"] * 100 if budget["monthly_tokens"] else 0
    cost_pct = mo["cost"]   / budget["monthly_cost_usd"] * 100 if budget["monthly_cost_usd"] else 0
    print(f"  This month ({mo['month']}, {mo['days']} days active)")
    print(f"  Tokens : {_fmt_tokens(mo['tokens'])} / {_fmt_tokens(budget['monthly_tokens'])}  {_bar(tok_pct)}")
    print(f"  Cost   : ${mo['cost']:.4f} / ${budget['monthly_cost_usd']:.2f}  {_bar(cost_pct)}")
    print(f"  Msgs   : {mo['messages']}  |  Sessions: {mo['sessions']}")
    print()

    # ── Last 7 days ──
    daily = daily_stats(stats, days=7)
    if daily:
        print(f"  {'Date':<12} {'Tokens':>10} {'Est. Cost':>12} {'Msgs':>6} {'Sessions':>9}")
        print(f"  {'-'*55}")
        for d in daily:
            print(f"  {d['date']:<12} {_fmt_tokens(d['tokens']):>10} ${d['cost']:>10.4f} {d['messages']:>6} {d['sessions']:>9}")
        print()

    # ── Lifetime by model ──
    lt = lifetime_stats(stats)
    if lt["rows"]:
        print(f"  Lifetime by model")
        print(f"  {'-'*75}")
        for r in lt["rows"]:
            p = _price(r["model"])
            print(f"  {r['model']}")
            print(f"    Input   : {_fmt_tokens(r['input']):>10}  @ ${p['input']}/MTok")
            print(f"    Output  : {_fmt_tokens(r['output']):>10}  @ ${p['output']}/MTok")
            print(f"    Cache-R : {_fmt_tokens(r['cache_read']):>10}  @ ${p['cache_read']}/MTok")
            print(f"    Cache-W : {_fmt_tokens(r['cache_write']):>10}  @ ${p['cache_write']}/MTok")
            print(f"    Cost    : ${r['cost']:.4f}")
            print()
        print(f"  TOTAL LIFETIME COST: ${lt['total_cost']:.4f}")
        print()


def cmd_sessions(n: int = 10) -> None:
    sessions = _load_sessions()[:n]
    if not sessions:
        print("No session data found.")
        return
    print(f"\n  {'Date':<22} {'Tokens':>8} {'In':>7} {'Out':>7} {'Msgs':>5} {'Tools':>6}  First prompt")
    print(f"  {'-'*90}")
    for s in sessions:
        ts = s.get("start_time", "")[:19].replace("T", " ")
        inp = s.get("input_tokens", 0)
        out = s.get("output_tokens", 0)
        total = inp + out
        msgs  = s.get("user_message_count", 0)
        tools = sum(s.get("tool_counts", {}).values())
        prompt = (s.get("first_prompt") or "")[:40]
        print(f"  {ts:<22} {_fmt_tokens(total):>8} {_fmt_tokens(inp):>7} {_fmt_tokens(out):>7} {msgs:>5} {tools:>6}  {prompt}")
    print()


def cmd_budget_show() -> None:
    b = _load_budget()
    print(f"\n  Budget configuration ({BUDGET_FILE})")
    print(f"  daily_tokens   : {_fmt_tokens(b['daily_tokens'])}")
    print(f"  monthly_tokens : {_fmt_tokens(b['monthly_tokens'])}")
    print(f"  daily_cost_usd : ${b['daily_cost_usd']:.2f}")
    print(f"  monthly_cost_usd: ${b['monthly_cost_usd']:.2f}")
    print(f"  warn_pct       : {b['warn_pct']}%")
    print()


def cmd_budget_set(key: str, value: str) -> None:
    b = _load_budget()
    valid = {"daily_tokens", "monthly_tokens", "daily_cost_usd", "monthly_cost_usd", "warn_pct"}
    if key not in valid:
        print(f"Unknown key '{key}'. Valid: {', '.join(sorted(valid))}")
        sys.exit(1)
    b[key] = float(value) if "." in value or "cost" in key else int(value)
    _save_budget(b)
    print(f"  Budget updated: {key} = {b[key]}")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    args = sys.argv[1:]
    stats = _load_stats()

    if not args or args[0] == "report":
        cmd_report(stats)

    elif args[0] == "today":
        cmd_today(stats)

    elif args[0] == "check":
        sys.exit(cmd_check(stats))

    elif args[0] == "sessions":
        n = int(args[1]) if len(args) > 1 else 10
        cmd_sessions(n)

    elif args[0] == "budget":
        if len(args) == 1 or args[1] == "show":
            cmd_budget_show()
        elif args[1] == "set" and len(args) == 4:
            cmd_budget_set(args[2], args[3])
        else:
            print("Usage: budget [show | set <key> <value>]")

    else:
        print("Commands: report | today | check | sessions [N] | budget [show | set <key> <value>]")
