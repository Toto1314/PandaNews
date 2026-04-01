"""
job_store.py — SQLite-backed job and step persistence for chain.py.
Jobs = one run_chain() call. Steps = one agent invocation within that chain.
DB: ~/.claude/jobs.db (WAL mode, connection-per-call pattern)
"""

import sqlite3
import uuid
import time
from pathlib import Path

DB_PATH = str(Path.home() / ".claude" / "jobs.db")

# Cost rates per model tier: (input_rate_per_1M, output_rate_per_1M) in USD
_COST_RATES = {
    "haiku": (0.25, 1.25),
    "sonnet": (3.0, 15.0),
    "opus": (15.0, 75.0),
}


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, isolation_level=None)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db() -> None:
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            job_id      TEXT PRIMARY KEY,
            task        TEXT NOT NULL,
            status      TEXT NOT NULL DEFAULT 'pending',
            created_at  REAL NOT NULL,
            updated_at  REAL NOT NULL,
            result      TEXT,
            error       TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS steps (
            step_id       TEXT PRIMARY KEY,
            job_id        TEXT NOT NULL REFERENCES jobs(job_id),
            dept          TEXT,
            agent         TEXT,
            task          TEXT,
            status        TEXT NOT NULL DEFAULT 'pending',
            output        TEXT,
            input_tokens  INTEGER,
            output_tokens INTEGER,
            cost_usd      REAL,
            latency_ms    REAL,
            started_at    REAL,
            completed_at  REAL
        )
    """)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.close()


def _cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    """Approximate cost in USD. Rates are list-price estimates, not billing-accurate."""
    model_lower = model.lower()
    if "haiku" in model_lower:
        rates = _COST_RATES["haiku"]
    elif "opus" in model_lower:
        rates = _COST_RATES["opus"]
    else:
        rates = _COST_RATES["sonnet"]
    cost = (input_tokens / 1_000_000) * rates[0] + (output_tokens / 1_000_000) * rates[1]
    return round(cost, 8)


# ---------------------------------------------------------------------------
# Job CRUD
# ---------------------------------------------------------------------------

def create_job(task: str) -> str:
    job_id = str(uuid.uuid4())
    now = time.time()
    conn = _get_conn()
    conn.execute(
        "INSERT INTO jobs (job_id, task, status, created_at, updated_at) VALUES (?, ?, 'pending', ?, ?)",
        (job_id, task, now, now),
    )
    conn.close()
    return job_id


def start_job(job_id: str) -> None:
    now = time.time()
    conn = _get_conn()
    conn.execute(
        "UPDATE jobs SET status='running', updated_at=? WHERE job_id=?",
        (now, job_id),
    )
    conn.close()


def complete_job(job_id: str, result: str) -> None:
    now = time.time()
    conn = _get_conn()
    conn.execute(
        "UPDATE jobs SET status='done', result=?, updated_at=? WHERE job_id=?",
        (result, now, job_id),
    )
    conn.close()


def fail_job(job_id: str, error: str) -> None:
    now = time.time()
    conn = _get_conn()
    conn.execute(
        "UPDATE jobs SET status='failed', error=?, updated_at=? WHERE job_id=?",
        (error, now, job_id),
    )
    conn.close()


# ---------------------------------------------------------------------------
# Step CRUD
# ---------------------------------------------------------------------------

def create_step(job_id: str, dept: str, agent: str, task: str) -> str:
    step_id = str(uuid.uuid4())
    conn = _get_conn()
    conn.execute(
        "INSERT INTO steps (step_id, job_id, dept, agent, task, status) VALUES (?, ?, ?, ?, ?, 'pending')",
        (step_id, job_id, dept, agent, task),
    )
    conn.close()
    return step_id


def start_step(step_id: str) -> None:
    now = time.time()
    conn = _get_conn()
    conn.execute(
        "UPDATE steps SET status='running', started_at=? WHERE step_id=?",
        (now, step_id),
    )
    conn.close()


def complete_step(
    step_id: str,
    output: str,
    input_tokens: int,
    output_tokens: int,
    cost_usd: float,
    latency_ms: float,
) -> None:
    now = time.time()
    conn = _get_conn()
    conn.execute(
        """UPDATE steps
           SET status='done', output=?, input_tokens=?, output_tokens=?,
               cost_usd=?, latency_ms=?, completed_at=?
           WHERE step_id=?""",
        (output, input_tokens, output_tokens, cost_usd, latency_ms, now, step_id),
    )
    conn.close()


def fail_step(step_id: str, error: str) -> None:
    now = time.time()
    conn = _get_conn()
    conn.execute(
        "UPDATE steps SET status='failed', output=?, completed_at=? WHERE step_id=?",
        (error, now, step_id),
    )
    conn.close()


# ---------------------------------------------------------------------------
# Read queries
# ---------------------------------------------------------------------------

def get_job(job_id: str) -> dict:
    conn = _get_conn()
    row = conn.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
    conn.close()
    return dict(row) if row else {}


def get_steps(job_id: str) -> list:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM steps WHERE job_id=? ORDER BY rowid ASC", (job_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def list_jobs(limit: int = 20) -> list:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_incomplete_jobs() -> list:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM jobs WHERE status IN ('running', 'interrupted') ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Module init — idempotent, runs on import
# ---------------------------------------------------------------------------
_init_db()
