# Custodian Cleaning Plan
**Generated:** 2026-03-27 22:15
**Status:** PENDING CPrO / Dir-PromptQA APPROVAL
**Required:** Explicit approval before any changes are applied.

---

## Proposed Actions

### 1. Agent Prompt Compressions
- **Risk-Manager-Investments** | sonnet | ~4171→2000 tokens | Priority: MEDIUM
  - Compress to under 2000 tokens — remove repeated context and inline boilerplate
  - Deduplicate: remove 5 repeated sentence(s)
- **Associate-Engineer** | haiku | ~2318→600 tokens | Priority: MEDIUM
  - Haiku: keep only role, core actions, output format, and hard constraints. Strip all narrative.
  - Merge sections with < 3 bullets into their parent section
- **CPrO-Prompting** | sonnet | ~5408→2000 tokens | Priority: MEDIUM
  - Compress to under 2000 tokens — remove repeated context and inline boilerplate
  - Merge sections with < 3 bullets into their parent section
- **Sr-Quant-Analyst** | sonnet | ~4218→2000 tokens | Priority: MEDIUM
  - Compress to under 2000 tokens — remove repeated context and inline boilerplate
  - Deduplicate: remove 1 repeated sentence(s)
- **SDR** | haiku | ~2116→600 tokens | Priority: MEDIUM
  - Haiku: keep only role, core actions, output format, and hard constraints. Strip all narrative.
- **Product-Analyst** | haiku | ~2096→600 tokens | Priority: MEDIUM
  - Haiku: keep only role, core actions, output format, and hard constraints. Strip all narrative.
- **scout** | haiku | ~1128→600 tokens | Priority: MEDIUM
  - Haiku: keep only role, core actions, output format, and hard constraints. Strip all narrative.
  - Haiku agents should drop or inline these sections: scout — codebase context agent
- **Compliance-Analyst** | haiku | ~2005→600 tokens | Priority: MEDIUM
  - Haiku: keep only role, core actions, output format, and hard constraints. Strip all narrative.
- **Dir-Competitive-Intelligence** | sonnet | ~3619→2000 tokens | Priority: MEDIUM
  - Compress to under 2000 tokens — remove repeated context and inline boilerplate
  - Deduplicate: remove 1 repeated sentence(s)
- **Dir-User-Research** | sonnet | ~3603→2000 tokens | Priority: MEDIUM
  - Compress to under 2000 tokens — remove repeated context and inline boilerplate
  - Deduplicate: remove 1 repeated sentence(s)

### 2. Model Tier Corrections (Haiku agents doing Sonnet-level work)
- **Associate-Engineer** | ~2318 tokens | Recommend: bump to `sonnet`
- **SDR** | ~2116 tokens | Recommend: bump to `sonnet`
- **Product-Analyst** | ~2096 tokens | Recommend: bump to `sonnet`
- **Compliance-Analyst** | ~2005 tokens | Recommend: bump to `sonnet`
- **Risk-Analyst** | ~1518 tokens | Recommend: bump to `sonnet`

### 4. Prompt Cache Cleanup
- Remove 68 stale entries (source file changed)
- Remove 0 orphaned entries (source file deleted)
- 104 valid entries will be preserved

### 5. Memory Hygiene
- **investment_thesis.md** — Large (4382 chars) — consider splitting into focused sub-memories
- **portfolio_roth_ira.md** — Large (7043 chars) — consider splitting into focused sub-memories
- **portfolio_watchlist.md** — Large (4537 chars) — consider splitting into focused sub-memories
- **unresolved_kiriko.md** — Not referenced in MEMORY.md index — orphaned memory file

---

## Summary
| Category | Actions |
|---|---|
| Agent compressions | 47 |
| Model tier corrections | 8 |
| Compliance gap fixes | 0 |
| Cache entries to remove | 68 |
| Memory file issues | 4 |
| **Total actions** | **127** |

---

## Approval Required
This plan must be reviewed and approved by **CPrO-Prompting** or **Dir-PromptQA** before execution.
To approve: `python custodian.py cycle --live`
To approve specific agents only: `python custodian.py analyze <AgentName>` then edit manually.

_Custodian does not self-authorize execution. Plan → Review → Approve → Execute._