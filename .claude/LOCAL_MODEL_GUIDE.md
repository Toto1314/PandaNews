# Local Model Infrastructure — Implementation Guide
**AI OS v1.9.x | Updated: 2026-03-23**

How to use the local Ollama execution stack from agents, scripts, and hooks.

---

## Architecture Overview

```
CEO Input
    │
    ▼
model_router.py        ← classify task tier + select model
    │
    ├── Tier 0–1 ──► Ollama (local, free)
    │                   gemma3:1b / llama3.2:3b / qwen2.5-coder:7b
    │
    └── Tier 2–4 ──► Claude API (sonnet / opus)
    │
    ▼
smart_run.py           ← executes the routed call
    │
    ├── streaming output
    ├── LangSmith tracing
    ├── budget gate (auto-downgrade if over daily limit)
    └── logs to ollama_usage.jsonl

parallel_runner.py     ← fanout / batch / pipeline (async)

warmup.py              ← pre-loads models at session start
vector_router.py       ← semantic agent lookup (ChromaDB)
token_tracker.py       ← cost/usage dashboard
```

---

## Quick Reference: Which Tool to Use

| Goal | Tool / Command |
|------|---------------|
| Run one task (auto-routed) | `python ~/.claude/smart_run.py "your task"` |
| Same prompt → N models | `python ~/.claude/parallel_runner.py fanout "prompt" --models m1 m2` |
| List of tasks in parallel | `python ~/.claude/parallel_runner.py batch tasks.json` |
| Multi-part task in parallel | `python ~/.claude/parallel_runner.py pipeline "part1; part2; part3"` |
| Check which model will be used | `python ~/.claude/model_router.py "your task"` |
| See today's token usage | `python ~/.claude/token_tracker.py today` |
| Pre-warm models manually | `python ~/.claude/warmup.py` |
| Find the right agent semantically | `python ~/.claude/vector_router.py query "I need X"` |

---

## 1. model_router.py — Task Classification + Model Selection

### How it works
1. Scans task text for domain keywords (code, security, research, etc.)
2. Checks task length and complexity signals
3. Assigns Tier 0–4
4. Returns: `backend` (ollama/claude), `model`, `tier`, `reason`

### Tier → Model mapping
```
Tier 0: gemma3:1b (no tools) or llama3.2:3b (tools needed)  ← always Ollama
Tier 1: gemma3:4b / llama3.2:3b                              ← always Ollama
Tier 2: llama3.1:latest / qwen2.5-coder:7b (code)           ← Ollama preferred
Tier 3: deepseek-coder-v2:16b (code) / sonnet                ← depends
Tier 4: claude opus                                           ← always Claude
```

### Usage in Python
```python
from model_router import route, OLLAMA_MODELS

# Basic routing
decision = route("summarize this meeting transcript")
print(decision["tier"])      # 0
print(decision["backend"])   # "ollama"
print(decision["model"])     # "gemma3:1b"
print(decision["reason"])    # "Tier 0 — always local"

# Force local even for harder tasks
decision = route("refactor this authentication module", prefer_local=True)

# Require tool support
decision = route("list files and summarize", needs_tools=True)
# gemma3:1b excluded — llama3.2:3b selected instead

# Force specific tier
decision = route("anything", force_tier=4)
# Returns claude opus
```

### CLI
```bash
python ~/.claude/model_router.py "explain gradient descent"
python ~/.claude/model_router.py "explain gradient descent" --prefer-local
python ~/.claude/model_router.py table          # show all models
python ~/.claude/model_router.py verify         # check which are installed
```

---

## 2. smart_run.py — Single Task Execution

Handles: routing → model verification → budget check → fallback → execute → log.

### CLI
```bash
# Standard run (auto-routed)
python ~/.claude/smart_run.py "what is a hash function?"

# Force local models
python ~/.claude/smart_run.py "explain docker" --prefer-local

# Skip tool requirement
python ~/.claude/smart_run.py "format this text" --no-tools

# Dry run — show routing decision without executing
python ~/.claude/smart_run.py "analyze this code" --dry-run

# Force a tier
python ~/.claude/smart_run.py "simple question" --tier 0

# Disable streaming (get full response at once)
python ~/.claude/smart_run.py "explain X" --no-stream
```

### Python API
```python
import asyncio
from smart_run import run_task

result = asyncio.run(run_task(
    task="explain what a transformer model is",
    prefer_local=True,
    needs_tools=False,
))
print(result["output"])
print(result["model"])
print(result["elapsed"])
```

### LangSmith tracing
When `LANGCHAIN_API_KEY` is set (it is, via settings.json env block), every call is traced automatically. View runs at https://smith.langchain.com under project `ai-os-local`.

---

## 3. parallel_runner.py — Concurrent Execution

Three patterns:

### Fan-out (comparison / ensemble)
Same prompt → multiple models simultaneously. Use for:
- Comparing model quality
- Getting multiple perspectives
- Ensemble voting on answers

```python
import asyncio
from parallel_runner import fanout

results = asyncio.run(fanout(
    prompt="what causes inflation?",
    models=["gemma3:1b", "llama3.2:3b", "gemma3:4b"],
))
for r in sorted(results, key=lambda x: x["elapsed"]):
    print(f"{r['model']}: {r['elapsed']}s")
    print(r["output"][:200])
```

CLI:
```bash
python ~/.claude/parallel_runner.py fanout "what is RAG?" --models gemma3:1b llama3.2:3b
```

### Batch (independent tasks)
Different prompts on different models, all at once.

```python
from parallel_runner import batch_run

items = [
    {"model": "gemma3:1b",      "prompt": "summarize: ...",       "label": "summary"},
    {"model": "qwen2.5-coder:7b", "prompt": "write tests for: ...", "label": "tests"},
    {"model": "llama3.2:3b",    "prompt": "check grammar: ...",   "label": "grammar"},
]
results = asyncio.run(batch_run(items))
```

JSON file format for CLI:
```json
[
  {"model": "gemma3:1b",       "prompt": "what is X?",     "label": "definition"},
  {"model": "llama3.2:3b",     "prompt": "summarize X",    "label": "summary"},
  {"model": "qwen2.5-coder:7b","prompt": "write tests",    "label": "tests"}
]
```
```bash
python ~/.claude/parallel_runner.py batch tasks.json
```

### Pipeline (decompose → parallel)
Splits a task on newlines or semicolons, routes each part to the best local model, runs all in parallel.

```bash
python ~/.claude/parallel_runner.py pipeline "summarize this doc; extract key dates; write a tweet"
```

Use when you have a complex request that can be broken into independent sub-tasks.

### CAE-Audit use case (built-in example)
```bash
# Run audit summaries for multiple agents in parallel
python ~/.claude/parallel_runner.py batch audit_tasks.json
```
```json
[
  {"model": "llama3.2:3b", "prompt": "audit: does this agent have negative constraints? [paste agent text]", "label": "NC-check"},
  {"model": "llama3.2:3b", "prompt": "audit: is the invoke-when section specific enough?", "label": "invoke-check"},
  {"model": "gemma3:4b",   "prompt": "audit: are there any missing escalation paths?", "label": "escalation-check"}
]
```

---

## 4. warmup.py — Cold Start Prevention

Ollama models take 5–120s to load from disk on first use. warmup.py pre-loads them with a `"hi"` ping using `num_predict: 1` (minimal tokens, maximum load effect).

### Auto-run at session start
Wired into `SessionStart` hook in `~/.claude/settings.json`:
```json
{
  "type": "command",
  "command": "python ~/.claude/warmup.py --silent 2>/dev/null || true",
  "timeout": 90,
  "async": true
}
```
Runs in the background — doesn't block Claude from starting.

### Manual use
```bash
python ~/.claude/warmup.py                              # warm default models
python ~/.claude/warmup.py --models gemma3:1b llama3.1:latest
python ~/.claude/warmup.py --all                        # warm every installed model
python ~/.claude/warmup.py --status                     # show installed vs configured
python ~/.claude/warmup.py --config                     # show config
```

### Change default warm models
```bash
# Edit ~/.claude/warmup_config.json
{
  "models": ["llama3.2:3b", "gemma3:1b", "qwen2.5-coder:7b"],
  "timeout": 60,
  "silent": false
}
```

---

## 5. vector_router.py — Semantic Agent Lookup

Finds the right agent from the 136-agent directory using semantic search (ChromaDB + all-MiniLM-L6-v2).

### First-time setup
```bash
python ~/.claude/vector_router.py build
# Output: [vector_router] Indexed 136 agents -> ~/.claude/vector_db/
```

Re-run after adding or editing agent files.

### Query
```bash
python ~/.claude/vector_router.py query "I need to analyze competitive threats" --n 5
python ~/.claude/vector_router.py query "security review for new code" --dept security
```

### Python API
```python
from vector_router import query_agents, build_index

# Find top 3 agents for a task
results = query_agents("I need a financial model for M&A", n=3)
for r in results:
    print(f"{r['agent']:<30} {r['department']:<15} score={r['score']:.3f}")
```

### Integration with smart_run (future)
`vector_router` + `model_router` together = full semantic routing:
1. `query_agents(task)` → finds best agent
2. `route(task)` → selects best model
3. Invoke agent with that model

---

## 6. token_tracker.py — Usage Dashboard

```bash
python ~/.claude/token_tracker.py today      # daily usage + Ollama summary
python ~/.claude/token_tracker.py report     # full lifetime breakdown by model
python ~/.claude/token_tracker.py sessions 5 # last 5 sessions
python ~/.claude/token_tracker.py check      # are we over daily budget?

# Budget management
python ~/.claude/token_tracker.py budget show
python ~/.claude/token_tracker.py budget set daily_limit_usd 3.00
python ~/.claude/token_tracker.py budget set warn_at_pct 80
```

Reads from:
- `~/.claude/stats-cache.json` — Claude API usage
- `~/.claude/session-meta/` — per-session granularity
- `~/.claude/ollama_usage.jsonl` — local model runs (written by smart_run.py)

---

## 7. Adding a New Agent to the Execution Stack

When you add a new agent `.md` file to `~/.claude/agents/`:

1. **Rebuild the vector index:**
   ```bash
   python ~/.claude/vector_router.py build
   ```

2. **Add it to model_router.py if it has a preferred model tier** (optional — only if the agent has special routing needs).

3. **Test it can be found:**
   ```bash
   python ~/.claude/vector_router.py query "the thing this agent does"
   ```

4. **No other wiring needed** — agents are markdown files. The execution infrastructure picks them up automatically.

---

## 8. Patterns for Agent-to-Agent Calls

### Pattern 1: Sequential (simple)
Agent A completes → feeds output to Agent B.
```python
result_a = asyncio.run(run_task("analyze this data: ..."))
result_b = asyncio.run(run_task(f"summarize this analysis: {result_a['output']}"))
```

### Pattern 2: Parallel fan-out (comparison)
Same input → multiple specialist agents simultaneously.
```python
items = [
    {"model": "llama3.2:3b", "prompt": f"security angle: {task}", "label": "ciso"},
    {"model": "llama3.2:3b", "prompt": f"legal angle: {task}",    "label": "gc-legal"},
    {"model": "llama3.2:3b", "prompt": f"data angle: {task}",     "label": "cdo"},
]
results = asyncio.run(batch_run(items))
```

### Pattern 3: Pipeline decomposition
Break a complex task into independent parts:
```python
task = "summarize the risks; identify the data flows; check for compliance gaps"
results = asyncio.run(pipeline_run(task))
# Each part auto-routed to best local model, all run in parallel
```

### Pattern 4: Semantic dispatch
Find the right agent first, then route:
```python
agents = query_agents("I need a security review")
top_agent = agents[0]["agent"]   # e.g., "CISO"
decision = route(task, needs_tools=True)
# Now invoke the agent via Claude Agent tool with decision["agent_param"] model
```

---

## 9. Ollama Model Reference

| Model | Size | Tools | Best For | Tier |
|-------|------|-------|----------|------|
| `gemma3:1b` | ~1GB | No | Fastest responses, simple Q&A | 0 |
| `gemma3:4b` | ~3GB | No | Better quality simple tasks | 0–1 |
| `llama3.2:3b` | ~2GB | **Yes** | General + tools at Tier 0–1 | 0–1 |
| `llama3.1:latest` | ~5GB | **Yes** | General Tier 2 | 2 |
| `qwen2.5-coder:7b` | ~5GB | **Yes** | Code generation/review | 2 |
| `deepseek-coder-v2:16b` | ~9GB | **Yes** | Hard coding tasks | 3 |
| `deepseek-r1:latest` | ~7GB | No | Math/reasoning | 2–3 |
| `mistral:7b` | ~4GB | No | General text | 1–2 |
| `phi3:medium` | ~8GB | No | Microsoft reasoning tasks | 2 |

**Warm by default (in warmup_config.json):**
- `llama3.2:3b` — most used (tools, Tier 0–1)
- `gemma3:1b` — fastest (no tools, Tier 0)
- `qwen2.5-coder:7b` — code tasks

---

## 10. Troubleshooting

### "Ollama not running"
```bash
ollama serve   # start in background
# or: restart Ollama from system tray
```

### Model loads slowly (cold start)
```bash
python ~/.claude/warmup.py   # pre-load now
# Or add to warmup_config.json and restart Claude Code
```

### "Model not found" error
```bash
ollama pull llama3.2:3b   # install missing model
python ~/.claude/model_router.py verify   # check all configured models
```

### LangSmith traces not appearing
- Check `LANGCHAIN_API_KEY` is set: `echo $LANGCHAIN_API_KEY`
- Restart Claude Code (env vars load at session start)
- Verify at: https://smith.langchain.com → project `ai-os-local`

### Vector index out of date (new agents not found)
```bash
python ~/.claude/vector_router.py build   # full rebuild
```

### Budget exceeded — auto-downgraded to Haiku
```bash
python ~/.claude/token_tracker.py budget show
python ~/.claude/token_tracker.py budget set daily_limit_usd 5.00  # increase limit
```
