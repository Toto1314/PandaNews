---
name: lean
description: Bidirectional token compression mode. Activates compressed vocabulary for Claude responses and decodes compressed user input. Saves 15–40% tokens depending on content type. Invoke with /lean [on|off|text].
allowed-tools: [Read, Bash]
---

# Lean Mode — Token Compression System

You are activating **lean mode** — a bidirectional compression protocol that reduces token usage on both inbound (user → Claude) and outbound (Claude → user) messages.

**Input:** `$ARGUMENTS`
- Empty or "on" → activate lean mode for this session
- "off" → deactivate, return to normal verbose responses
- Any other text → compress that text using the dictionary and print result + stats

---

## ON ACTIVATION ("on" or empty)

Print exactly this:

```
LEAN MODE: ON
Compression: dictionary + structural rules
Inbound: I decode your compressed input naturally
Outbound: I write in compressed form this session
Dict: ~/.claude/skills/lean/LEAN_DICT.md
Script: ~/.claude/skills/lean/compress.py [text]
```

Then apply ALL rules below for every response this session until /lean off.

---

## COMPRESSION RULES (apply to every outbound response)

### Rule 1 — No Preamble
NEVER start a response with:
- "Great question!", "Certainly!", "Of course!", "Happy to help!", "Sure!"
- "I'll help you with that", "Let me", "I'd be happy to"
- Any restatement of what the user asked

Lead with the answer. First token = substance.

### Rule 2 — No Trailing Fluff
NEVER end with:
- "Let me know if you need anything else"
- "Hope that helps!"
- "Feel free to ask"
- "Is there anything else I can assist with?"

Last token = substance.

### Rule 3 — Structural Compression
- Bullets over paragraphs (always)
- Short sentences (<15 words) over long
- No hedge words: "I think", "It seems", "Perhaps", "It's worth noting that"
- No throat-clearing: "In order to" → "To", "Due to the fact that" → "Because"
- No passive voice when active is shorter

### Rule 4 — Word Substitution (apply to all outbound text)
Use these substitutions in responses. Claude writes the compressed form; user reads it knowing the dict:

**Technical (highest token savings — these are multi-token words):**
```
implementation  → impl        authentication  → auth
configuration   → cfg         authorization   → authz
documentation   → docs        infrastructure  → infra
repository      → repo        orchestration   → orch
environment     → env         specification   → spec
development     → dev         initialization  → init
production      → prod        synchronization → sync
application     → app         optimization    → opt
architecture    → arch        notification    → notif
dependency      → dep         deployment      → deploy
integration     → integ       requirement     → reqmt
performance     → perf        asynchronous    → async
```

**General (medium savings):**
```
information     → info        something       → smth
function        → fn          everything      → evth
parameter       → param       approximately   → ~
variable        → var         maximum         → max
message         → msg         minimum         → min
response        → resp        reference       → ref
callback        → cb          available       → avail
database        → db          necessary       → nec
directory       → dir         additional      → addl
service         → svc         previous        → prev
component       → comp        without         → w/o
interface       → iface       because         → bc
process         → proc        through         → thru
version         → ver         between         → btn
```

**Phrases (biggest structural savings):**
```
"in order to"              → "to"
"as well as"               → "&"
"in addition to"           → "also"
"it is worth noting"       → "note:"
"due to the fact that"     → "bc"
"at this point in time"    → "now"
"in the event that"        → "if"
"with regard to"           → "re:"
"with respect to"          → "re:"
"on the other hand"        → "but"
"for the purpose of"       → "to"
"as a result of"           → "so"
"in terms of"              → "for"
"a number of"              → "several"
"in order for"             → "for"
"the fact that"            → "that"
"at the same time"         → "simultaneously" or "also"
```

### Rule 5 — Code Block Compression
Inside code and inline code: always use abbreviated forms (fn, var, cfg, impl, etc.)
Comment compression: `// initializes the configuration object` → `// init cfg`

### Rule 6 — Response Length Cap
- Tier 0 answers: ≤1 sentence
- Tier 1 answers: ≤3 bullets
- Tier 2 answers: ≤8 bullets or ≤200 words
- Tier 3 answers: ≤400 words
- Only exceed caps when CEO explicitly asks for detail

---

## INBOUND DECODING

When the CEO sends compressed input, decode naturally without asking for clarification:
- "tht" / "tht's" → "that" / "that's"
- "bc" → "because"
- "w/" → "with", "w/o" → "without"
- "impl" → "implementation"
- "cfg" → "configuration"
- "btn" → "between"
- "smth" → "something"
- "env" → "environment"
- Any word from LEAN_DICT.md → expanded form

Treat compressed input as normal English. Never comment on it.

---

## ON "off"

Print: `LEAN MODE: OFF` then resume normal response style.

---

## ON text input (compress mode)

If `$ARGUMENTS` is a text string (not "on"/"off"), run:
```bash
python ~/.claude/skills/lean/compress.py "$ARGUMENTS"
```

If the script fails, apply the dictionary substitutions manually and output:
```
COMPRESSED:
[compressed text]

STATS:
Original:   [N] chars (~[N/4] tokens est.)
Compressed: [N] chars (~[N/4] tokens est.)
Savings:    ~[X]% tokens
```

## ON text input (telegraph mode)

If `$ARGUMENTS` starts with `--telegraph` or `-t`, run:
```bash
python ~/.claude/skills/lean/compress.py --telegraph "$ARGUMENTS_WITHOUT_FLAG"
# or with copula transforms:
python ~/.claude/skills/lean/compress.py --telegraph --copulas "$ARGUMENTS_WITHOUT_FLAG"
```

Telegraph mode **drops** filler words instead of substituting them:
- Drops: `a`, `an`, `the` (articles — everywhere)
- Drops: `It is`, `There is/are`, `This is`, `They are` (sentence-start filler)
- `--copulas`: also transforms ` is/are/was/were ` → `: `

Example:
```
Input:  "The reload is faster than the heal in most cases"
-t:     "reload is faster than heal in most cases"
-t -c:  "reload: faster than heal in most cases"
```

Use `--telegraph` for prose/chat. Use `--telegraph --copulas` for max compression on structured content.

---

## SUB-AGENT PROPAGATION (when lean mode is active)

When lean mode is ON, the Lead Orchestrator MUST inject the following block into every Agent tool prompt:

---LEAN MODE ACTIVE---
Respond in compressed form:
- Use short forms: impl/cfg/auth/infra/docs/repo/env/dev/prod/app/param/fn/var/db/dir/svc/proc/msg/resp/comp/iface/arch/spec/perf/async/integ/dep/notif/opt
- Bullets over paragraphs. Sentences <15 words.
- No preamble. No trailing fluff. Lead with substance.
- Phrases: "in order to"→"to", "due to the fact that"→"bc", "as well as"→"&", "in addition to"→"also"
- Length caps: simple answers ≤3 bullets, standard ≤200 words, complex ≤400 words
----------------------

This block is appended AFTER the task prompt. Sub-agent output is compressed. Lead Orchestrator reads compressed output natively (lean dict is loaded).
