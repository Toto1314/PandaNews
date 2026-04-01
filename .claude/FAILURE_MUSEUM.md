# FAILURE MUSEUM
**Owner:** CAE-Audit | **Maintained by:** All agents | **Retention:** 90 days minimum (SOX)

> This is not an audit findings log. That's AUDIT_FINDINGS.md.
> This is a learning artifact. The difference: audit findings track compliance gaps. The Failure Museum tracks **intelligence failures** — times the OS gave bad advice, routed wrong, missed context, or produced output the CEO rejected.
> Good systems learn from success. Great systems learn from failure.

---

## Format

```
### [DATE] — [FAILURE TYPE] — [SHORT TITLE]
**What was attempted:** [one sentence]
**What went wrong:** [one sentence]
**Root cause:** routing | context loss | model tier | agent prompt | hallucination | bad framing | other
**What was learned:** [one sentence]
**What changed:** [file/agent updated, or "nothing yet"]
```

---

## Failure Types

| Type | Meaning |
|------|---------|
| `routing` | Wrong agent was invoked for the task |
| `context loss` | Agent lacked context that was available but not loaded |
| `model tier` | Wrong model used — too weak for the task, or overkill |
| `agent prompt` | Agent's system prompt produced suboptimal behavior |
| `hallucination` | Agent produced confident but incorrect information |
| `bad framing` | Agent answered the wrong question because input was framed poorly |
| `governance miss` | A gate (CISO, MasterPlanner, Five-File Rule) was skipped and caused a problem |
| `scope creep` | Agent expanded beyond its mandate and caused side effects |

---

## Log

*No entries yet. The first entry will be the most valuable one.*

---

## Quarterly Pattern Review (CAE-Audit)

Each quarter, CAE-Audit reviews this log and surfaces:
- Most common failure type
- Most frequently failing department or agent
- Whether any failure recurred (same root cause, second incident)
- Whether the "what changed" was actually implemented

Pattern review output → one paragraph appended to AUDIT_FINDINGS.md as a Tier 1 observation.
