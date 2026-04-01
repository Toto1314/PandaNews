# AI OS — Platform Roadmap
**Version:** 1.0.0 | **Owner:** CEO | **Last Updated:** 2026-03-30
**Active Sprint:** Sprint 1 — Execution Spine

> **For the Orchestrator:** On any open-ended task or "what should we work on?" input, read this file first. Pick the highest-priority `TODO` task in the ACTIVE sprint. Mark it `IN_PROGRESS` before starting. Mark it `DONE` after validator clears. Never start a task in a later sprint while earlier sprint tasks are `TODO` or `IN_PROGRESS`.

---

## Status Legend

| Symbol | Meaning |
|--------|---------|
| `TODO` | Ready to build — no blockers |
| `IN_PROGRESS` | Currently being worked on |
| `BLOCKED` | Waiting on a dependency — see notes |
| `DONE` | Validator cleared — complete |

---

## The Vision (VC Cash Mode)

**Today:** CLI → agent → output → done (stateless, blind, manual)

**After 4 sprints:** Event → API → DAG executor → agents (parallel) → state checkpoint → synthesize → push to Telegram/dashboard → log to registry

Four structural bets that turn a personal tool into an autonomous platform.

---

## Sprint 1 — Execution Spine `[ACTIVE]`

**Goal:** Make chain.py stateful, observable, and resumable. No more starting over when a chain fails at step 4 of 7.

**Exit Criteria:** A chain that fails mid-execution can be resumed from the last checkpoint. Every agent invocation produces a cost + latency trace. LangSmith dashboard shows live run data.

| # | Task | Status | Priority | Files Affected | Notes |
|---|------|--------|----------|---------------|-------|
| 1.1 | **SQLite job store** — add persistent state to chain.py so chains can checkpoint and resume on failure | `IN_PROGRESS` | P0 | `chain.py`, new `job_store.py` | Schema: job_id, status, steps[], current_step, created_at, updated_at |
| 1.2 | **Per-agent telemetry** — capture cost + latency per agent invocation and write to telemetry.db | `TODO` | P0 | `chain.py`, new `telemetry.py` | Fields: agent_name, model, tokens_in, tokens_out, cost_usd, latency_ms, timestamp |
| 1.3 | **DAG executor** — replace linear chain with directed acyclic graph so parallel steps run concurrently | `TODO` | P1 | `chain.py` | Unblocked by 1.1. Fan-out on independent steps, fan-in on synthesis. |
| 1.4 | **LangSmith wiring** — LangSmith is configured in settings.local.json but never actively used; wire telemetry.py to push traces | `TODO` | P1 | `telemetry.py`, `smart_run.py` | LANGCHAIN_TRACING_V2 and project already set. Just needs the push call. |
| 1.5 | **Chain CLI** — add `chain status <job_id>`, `chain resume <job_id>`, `chain list` commands to run.py | `TODO` | P2 | `run.py` | Depends on 1.1 + 1.2 |

---

## Sprint 2 — Agent Registry `[UPCOMING]`

**Goal:** Turn 182 static markdown files into a living, versioned, measurable agent network. Enable A/B testing at the agent level.

**Exit Criteria:** Every agent has a version history. Editing an agent file auto-rebuilds the vector index. Two prompt variants can be deployed side-by-side with performance tracking.

| # | Task | Status | Priority | Files Affected | Notes |
|---|------|--------|----------|---------------|-------|
| 2.1 | **agent_registry.db schema** — SQLite schema for agent versioning: agent_name, version, content_hash, deployed_at, is_active | `TODO` | P0 | new `agent_registry.py` | Foundation for everything else in Sprint 2 |
| 2.2 | **Auto-rebuild vector index on commit** — extend auto_changelog.py pre-commit hook to call vector_router.py rebuild() when agent files change | `TODO` | P0 | `auto_changelog.py`, `vector_router.py` | Fixes the staleness gap. Hook already exists — just extend it. |
| 2.3 | **Version history per agent** — on every agent file save, write a new version row to agent_registry.db | `TODO` | P1 | `agent_registry.py`, hook in `auto_changelog.py` | Depends on 2.1 |
| 2.4 | **A/B slot routing** — support two active versions per agent; route 50/50 based on job_id hash; log which version ran per trace | `TODO` | P1 | `agent_registry.py`, `chain.py` | Depends on 2.1 + 1.2 (telemetry) |
| 2.5 | **Quality score tracking** — add a success/fail rating per agent run; expose `chain rate <job_id> [pass|fail]` | `TODO` | P2 | `telemetry.py`, `run.py` | Feeds into A/B winner selection |

---

## Sprint 3 — API Surface `[UPCOMING]`

**Goal:** Break out of the CLI. Build a REST/WebSocket API so any client (Kiriko, web dashboard, webhooks) can invoke the OS.

**Exit Criteria:** Any agent can be invoked via HTTP POST. Chain status is queryable. Kiriko bot is a client of the API, not a direct CLI caller. External events (price alerts, patch drops) can trigger agent chains.

| # | Task | Status | Priority | Files Affected | Notes |
|---|------|--------|----------|---------------|-------|
| 3.1 | **FastAPI server scaffold** — `api_server.py` with startup, lifespan, CORS, auth token middleware | `TODO` | P0 | new `api_server.py` | Requires FastAPI + uvicorn. GC-Legal license check before deploy. |
| 3.2 | **POST /run** — fire any agent by name with a prompt; returns job_id; async execution via job store | `TODO` | P0 | `api_server.py`, `chain.py` | Depends on 3.1 + 1.1 |
| 3.3 | **GET /agents** — return registry of all agents with name, description, model tier, version | `TODO` | P0 | `api_server.py`, `agent_registry.py` | Depends on 3.1 + 2.1 |
| 3.4 | **GET /jobs/{id} + GET /jobs** — chain status, steps, cost, latency | `TODO` | P1 | `api_server.py` | Depends on 3.1 + 1.2 |
| 3.5 | **WebSocket /stream** — real-time streaming output for a running job | `TODO` | P1 | `api_server.py` | Depends on 3.2 |
| 3.6 | **POST /webhook** — inbound event triggers (price_alert, patch_drop, earnings_release, custom) → maps to chain | `TODO` | P1 | `api_server.py`, new `webhook_router.py` | Depends on 3.2 |
| 3.7 | **Refactor kiriko_bot.py** — replace direct `claude --print` calls with POST /run calls to api_server | `TODO` | P2 | `kiriko_bot.py` | Depends on 3.2. Makes Kiriko a proper client. |

---

## Sprint 4 — Dashboard `[UPCOMING]`

**Goal:** Visual interface for the AI OS. See what's running, what it costs, which agents are firing, and your portfolio + gaming status at a glance.

**Exit Criteria:** A web dashboard reads live data from the Sprint 3 API. Agent roster, job queue, cost telemetry, and key intelligence panels are visible without opening a terminal.

| # | Task | Status | Priority | Files Affected | Notes |
|---|------|--------|----------|---------------|-------|
| 4.1 | **Next.js project scaffold** — initialize dashboard at `~/ai-dashboard/` with Tailwind + shadcn/ui | `TODO` | P0 | new project dir | Reads from Sprint 3 API. No backend code here — pure client. |
| 4.2 | **Agent roster panel** — lists all 182 agents by department, model tier, version, last invoked | `TODO` | P0 | dashboard | Reads GET /agents |
| 4.3 | **Job queue panel** — active and recent chains with status, step progress, cost, latency | `TODO` | P1 | dashboard | Reads GET /jobs |
| 4.4 | **Cost telemetry charts** — daily/weekly spend by agent, by model tier, by department | `TODO` | P1 | dashboard | Reads telemetry.db via API endpoint |
| 4.5 | **Intelligence panels** — portfolio pulse, agent economy watchlist, gaming patch status | `TODO` | P2 | dashboard | Reads from portfolio brief + gaming cache endpoints |

---

## Completed

*(Nothing yet — Sprint 1 is active)*

---

## Orchestrator Integration Notes

When the CEO says "pick something to work on", "what's next", "continue the sprint", or similar:

1. Read this file
2. Find the ACTIVE sprint
3. Find the first `TODO` task by priority (P0 before P1 before P2)
4. Present the task to CEO with: what it is, what files are affected, what done looks like
5. On CEO confirmation → invoke the pipeline: `scout → architect → builder → validator`
6. Update this file: set task to `IN_PROGRESS` before build starts, `DONE` after validator clears

**Never start Sprint 2+ tasks while Sprint 1 has TODO items.**
**Always ask CEO before marking a sprint complete and advancing to the next.**
