# Lean Dictionary — Token Compression Reference

**Version:** 1.0.0 | **Used by:** `/lean` skill, `compress.py`

Token savings are estimated using ~4 chars/token heuristic (BPE tokenizer).
Highest value compressions listed first.

---

## Category 1 — Technical Terms (Highest Savings: 2–4 tokens → 1)

These are multi-syllable words that BPE tokenizers split into 2–4 subword tokens.
Abbreviating to ≤6 chars collapses them to 1 token.

| Full Word | Compressed | Est. Tokens Saved |
|-----------|-----------|-------------------|
| implementation | impl | 2 |
| authentication | auth | 2 |
| authorization | authz | 2 |
| configuration | cfg | 2 |
| infrastructure | infra | 1–2 |
| documentation | docs | 1–2 |
| orchestration | orch | 2 |
| specification | spec | 1–2 |
| initialization | init | 2 |
| synchronization | sync | 2 |
| optimization | opt | 1–2 |
| architecture | arch | 1 |
| asynchronous | async | 1–2 |
| notification | notif | 1–2 |
| performance | perf | 1 |
| deployment | deploy | 0–1 |
| integration | integ | 1 |
| requirement | reqmt | 1 |
| dependency | dep | 1 |
| repository | repo | 1 |

---

## Category 2 — Common Technical Nouns (Savings: 1–2 tokens → 1)

| Full Word | Compressed | Est. Tokens Saved |
|-----------|-----------|-------------------|
| information | info | 1 |
| environment | env | 1 |
| development | dev | 1 |
| production | prod | 1 |
| application | app | 1 |
| parameter | param | 1 |
| function | fn | 1 |
| variable | var | 1 |
| callback | cb | 1 |
| database | db | 1 |
| directory | dir | 1 |
| interface | iface | 1 |
| component | comp | 1 |
| container | ctr | 1 |
| service | svc | 1 |
| process | proc | 1 |
| message | msg | 0–1 |
| response | resp | 0–1 |
| request | req | 0–1 |
| version | ver | 0–1 |
| reference | ref | 0–1 |
| boolean | bool | 0–1 |
| integer | int | 0–1 |
| object | obj | 0–1 |
| string | str | 0–1 |
| buffer | buf | 0–1 |
| exception | exc | 0–1 |
| error | err | 0–1 |

---

## Category 3 — Common English (Savings: 0–1 tokens, high frequency)

| Full Word | Compressed | Notes |
|-----------|-----------|-------|
| because | bc | High freq |
| without | w/o | High freq |
| within | w/in | — |
| through | thru | High freq |
| though | tho | High freq |
| something | smth | High freq |
| everything | evth | — |
| nothing | nth | — |
| between | btn | — |
| about | abt | — |
| already | alr | — |
| probably | prob | — |
| approximately | ~ | Symbol replacement |
| maximum | max | — |
| minimum | min | — |
| available | avail | — |
| necessary | nec | — |
| additional | addl | — |
| previous | prev | — |
| original | orig | — |
| current | curr | — |
| different | diff | — |
| similar | sim | — |

---

## Category 4 — Verbose Phrases → Single Words/Tokens

These are the **highest ROI compressions** — phrases that become 1–2 tokens.
These save 2–6 tokens per occurrence.

| Verbose Phrase | Compressed | Tokens Saved |
|---------------|-----------|--------------|
| in order to | to | 3 |
| as well as | & | 3 |
| in addition to | also | 2–3 |
| it is worth noting that | note: | 5 |
| due to the fact that | bc | 5 |
| at this point in time | now | 4 |
| in the event that | if | 3 |
| with regard to | re: | 3 |
| with respect to | re: | 3 |
| on the other hand | but | 3 |
| for the purpose of | to | 4 |
| as a result of | so | 3 |
| in terms of | for | 3 |
| a number of | several | 2 |
| the fact that | that | 2 |
| at the same time | also | 3 |
| in order for | for | 2 |
| a lot of | many | 2 |
| make sure that | ensure | 2 |
| keep in mind that | note: | 3 |
| as mentioned above | (above) | 3 |
| as I mentioned | (above) | 3 |
| please note that | note: | 3 |
| it should be noted | note: | 4 |

---

## Category 5 — Response Structure Rules (Structural Compression)

These are not word substitutions — they are writing patterns that reduce total tokens most.
A single structural fix can save more tokens than 50 word substitutions.

| Pattern to REMOVE | Replacement |
|------------------|-------------|
| "Great question!" | (nothing) |
| "Certainly!" / "Of course!" | (nothing) |
| "Happy to help!" | (nothing) |
| "I'd be happy to..." | (start with verb) |
| "Let me explain..." | (just explain) |
| "I think that..." | (state it directly) |
| "It seems like..." | (state it directly) |
| "Perhaps..." as hedge | (state it directly) |
| "In summary," + restatement | (skip summary) |
| "To recap what we covered..." | (skip) |
| "Let me know if you need..." | (nothing) |
| "Feel free to ask..." | (nothing) |
| "Hope that helps!" | (nothing) |
| Any restatement of user's question | (skip) |

**Structural wins (prose → structure):**
- 1 paragraph (100 words) → 5 bullets (40 words) = saves ~15 tokens
- Passive voice → active = saves 1–3 tokens per sentence
- Hedge sentence removed = saves 8–15 tokens
- Preamble removed = saves 10–20 tokens
- Trailing pleasantry removed = saves 10–15 tokens

---

## Token Estimation Guide

```
Characters / 4  ≈  tokens (English prose)
Characters / 3  ≈  tokens (code/technical)
Characters / 6  ≈  tokens (very common short words)
```

**Typical response savings with lean mode:**
- Casual answer: ~15–20% token reduction
- Technical explanation: ~25–35% token reduction
- Code review: ~20–30% token reduction
- Long analysis: ~30–40% token reduction (structural rules dominate)

---

## Bidirectional Use

**Outbound (Claude → CEO):**
Claude applies all substitutions + structural rules automatically in lean mode.

**Inbound (CEO → Claude):**
CEO can type compressed form; Claude decodes naturally without confirmation.
Examples: "tht" = "that", "cfg" = "configuration", "bc" = "because", "impl" = "implementation"
