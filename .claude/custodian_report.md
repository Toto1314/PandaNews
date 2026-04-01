# Custodian Maintenance Report
**Generated:** 2026-03-27 21:59 | **Pattern window:** 14 days

## Usage Patterns
_No run log found or no entries in window._

## Agent Bloat Analysis
**Total agents scanned:** 172 | **Need attention:** 52

**Haiku** (25 agents): 25 over budget
**Sonnet** (140 agents): 51 over budget
**Opus** (7 agents): 0 over budget

### Top Issues (sorted by bloat score)

#### Risk-Manager-Investments
Model: `sonnet` | Tokens: ~4990 / 2000 budget | Bloat score: 0.60
- ⚠️  Over sonnet budget: ~4990 tokens vs 2000 target (+149%)
- ⚠️  5 repeated sentences — content duplication detected
- ⚠️  High section count (24) — consider consolidating thin sections
- 💡 Compress to under 2000 tokens — remove repeated context and inline boilerplate
- 💡 Deduplicate: remove 5 repeated sentence(s)
- 💡 Merge sections with < 3 bullets into their parent section

#### Risk-Analyst
Model: `haiku` | Tokens: ~2534 / 600 budget | Bloat score: 0.55
- ⚠️  Over haiku budget: ~2534 tokens vs 600 target (+322%)
- ⚠️  1 repeated sentences — content duplication detected
- ⚠️  High section count (16) — consider consolidating thin sections
- 💡 Haiku: keep only role, core actions, output format, and hard constraints. Strip all narrative.
- 💡 Deduplicate: remove 1 repeated sentence(s)
- 💡 Merge sections with < 3 bullets into their parent section

#### Investment-Analyst
Model: `haiku` | Tokens: ~2174 / 600 budget | Bloat score: 0.51
- ⚠️  Over haiku budget: ~2174 tokens vs 600 target (+262%)
- ⚠️  Compressible sections in Haiku agent: immutable portfolio context
- 💡 Haiku: keep only role, core actions, output format, and hard constraints. Strip all narrative.
- 💡 Haiku agents should drop or inline these sections: immutable portfolio context

#### Financial-Analyst
Model: `haiku` | Tokens: ~2120 / 600 budget | Bloat score: 0.50
- ⚠️  Over haiku budget: ~2120 tokens vs 600 target (+253%)
- ⚠️  1 repeated sentences — content duplication detected
- ⚠️  High section count (15) — consider consolidating thin sections
- 💡 Haiku: keep only role, core actions, output format, and hard constraints. Strip all narrative.
- 💡 Deduplicate: remove 1 repeated sentence(s)
- 💡 Merge sections with < 3 bullets into their parent section

#### Associate-Engineer
Model: `haiku` | Tokens: ~2318 / 600 budget | Bloat score: 0.49
- ⚠️  Over haiku budget: ~2318 tokens vs 600 target (+286%)
- ⚠️  High section count (15) — consider consolidating thin sections
- 💡 Haiku: keep only role, core actions, output format, and hard constraints. Strip all narrative.
- 💡 Merge sections with < 3 bullets into their parent section

#### Finance-Associate
Model: `haiku` | Tokens: ~2267 / 600 budget | Bloat score: 0.48
- ⚠️  Over haiku budget: ~2267 tokens vs 600 target (+277%)
- ⚠️  High section count (15) — consider consolidating thin sections
- 💡 Haiku: keep only role, core actions, output format, and hard constraints. Strip all narrative.
- 💡 Merge sections with < 3 bullets into their parent section

#### Finance-Manager
Model: `haiku` | Tokens: ~2211 / 600 budget | Bloat score: 0.47
- ⚠️  Over haiku budget: ~2211 tokens vs 600 target (+268%)
- ⚠️  High section count (15) — consider consolidating thin sections
- 💡 Haiku: keep only role, core actions, output format, and hard constraints. Strip all narrative.
- 💡 Merge sections with < 3 bullets into their parent section

#### Security-Analyst
Model: `haiku` | Tokens: ~2514 / 600 budget | Bloat score: 0.40
- ⚠️  Over haiku budget: ~2514 tokens vs 600 target (+319%)
- 💡 Haiku: keep only role, core actions, output format, and hard constraints. Strip all narrative.

#### CPrO-Prompting
Model: `sonnet` | Tokens: ~5408 / 2000 budget | Bloat score: 0.37
- ⚠️  Over sonnet budget: ~5408 tokens vs 2000 target (+170%)
- ⚠️  High section count (40) — consider consolidating thin sections
- 💡 Compress to under 2000 tokens — remove repeated context and inline boilerplate
- 💡 Merge sections with < 3 bullets into their parent section

#### Sr-Quant-Analyst
Model: `sonnet` | Tokens: ~4218 / 2000 budget | Bloat score: 0.36
- ⚠️  Over sonnet budget: ~4218 tokens vs 2000 target (+110%)
- ⚠️  1 repeated sentences — content duplication detected
- ⚠️  High section count (17) — consider consolidating thin sections
- 💡 Compress to under 2000 tokens — remove repeated context and inline boilerplate
- 💡 Deduplicate: remove 1 repeated sentence(s)
- 💡 Merge sections with < 3 bullets into their parent section

#### Software-Engineer
Model: `haiku` | Tokens: ~2131 / 600 budget | Bloat score: 0.36
- ⚠️  Over haiku budget: ~2131 tokens vs 600 target (+255%)
- 💡 Haiku: keep only role, core actions, output format, and hard constraints. Strip all narrative.

#### SDR
Model: `haiku` | Tokens: ~2116 / 600 budget | Bloat score: 0.35
- ⚠️  Over haiku budget: ~2116 tokens vs 600 target (+252%)
- 💡 Haiku: keep only role, core actions, output format, and hard constraints. Strip all narrative.

#### Product-Analyst
Model: `haiku` | Tokens: ~2096 / 600 budget | Bloat score: 0.35
- ⚠️  Over haiku budget: ~2096 tokens vs 600 target (+249%)
- 💡 Haiku: keep only role, core actions, output format, and hard constraints. Strip all narrative.

#### scout
Model: `haiku` | Tokens: ~1113 / 600 budget | Bloat score: 0.34
- ⚠️  Over haiku budget: ~1113 tokens vs 600 target (+85%)
- ⚠️  Compressible sections in Haiku agent: scout — codebase context agent
- 💡 Haiku: keep only role, core actions, output format, and hard constraints. Strip all narrative.
- 💡 Haiku agents should drop or inline these sections: scout — codebase context agent

#### Compliance-Analyst
Model: `haiku` | Tokens: ~2005 / 600 budget | Bloat score: 0.33
- ⚠️  Over haiku budget: ~2005 tokens vs 600 target (+234%)
- 💡 Haiku: keep only role, core actions, output format, and hard constraints. Strip all narrative.

## Prompt Cache
- Valid: 94
- Stale: 0
- Orphaned: 0

## Memory Audit

### investment_thesis.md (age: 3.2d, 4382 chars)
- Large (4382 chars) — consider splitting into focused sub-memories

### portfolio_roth_ira.md (age: 3.2d, 7043 chars)
- Large (7043 chars) — consider splitting into focused sub-memories

### portfolio_watchlist.md (age: 3.2d, 4537 chars)
- Large (4537 chars) — consider splitting into focused sub-memories

### unresolved_kiriko.md (age: 3.0d, 954 chars)
- Not referenced in MEMORY.md index — orphaned memory file

---
_Report generated by Custodian v1.0.0_