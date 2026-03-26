#!/usr/bin/env python3
"""
run_daily.py — One-shot daily runner for the gaming-update skill.
Calls fetch_updates.py then push_updates.py in sequence.
Designed to be scheduled via Windows Task Scheduler at 9am daily.

Schedule command (run once in an elevated PowerShell to register):
    schtasks /create /tn "GamingUpdateDaily" /tr "python C:\Users\atank\.claude\skills\gaming-update\run_daily.py" /sc daily /st 09:00 /f

To verify the task was created:
    schtasks /query /tn "GamingUpdateDaily"

To remove the task:
    schtasks /delete /tn "GamingUpdateDaily" /f
"""

import os
import sys
import subprocess
import logging
from datetime import datetime, timezone

# ── Paths ───────────────────────────────────────────────────────────────────

HOME      = os.path.expanduser("~")
SKILL_DIR = os.path.join(HOME, ".claude", "skills", "gaming-update")
LOG_FILE  = os.path.join(SKILL_DIR, "gaming_update.log")

FETCH_PY  = os.path.join(SKILL_DIR, "fetch_updates.py")
PUSH_PY   = os.path.join(SKILL_DIR, "push_updates.py")

# ── Logging ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger("run_daily")

# ── Runner ───────────────────────────────────────────────────────────────────

def run_step(label: str, script: str) -> bool:
    """Run a Python script as a subprocess. Returns True on success."""
    log.info("--- %s ---", label)
    try:
        result = subprocess.run(
            [sys.executable, script],
            capture_output=False,  # let output flow to stdout/log naturally
            timeout=900,           # 15 min total ceiling for all games
        )
        if result.returncode == 0:
            log.info("%s completed (rc=0).", label)
            return True
        else:
            log.error("%s exited with rc=%d.", label, result.returncode)
            return False
    except subprocess.TimeoutExpired:
        log.error("%s timed out.", label)
        return False
    except Exception as e:
        log.error("%s error: %s", label, e)
        return False


def main():
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    log.info("========== gaming-update daily run started at %s ==========", ts)

    fetch_ok = run_step("fetch_updates", FETCH_PY)
    push_ok  = run_step("push_updates", PUSH_PY)

    ts_end = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    status = "OK" if (fetch_ok and push_ok) else "PARTIAL"
    log.info("========== gaming-update daily run complete at %s [%s] ==========", ts_end, status)

    sys.exit(0 if (fetch_ok and push_ok) else 1)


if __name__ == "__main__":
    main()
