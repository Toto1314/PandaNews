---
name: news-song
description: News-to-Music pipeline. Fetches breaking news for ROTH IRA portfolio companies, maps it to portfolio positions, and converts it into a fully produced Suno AI song prompt package — lyrics, structure markers, production notes, beat timing cues, and style tags. Output is copy-paste ready for Suno AI.
allowed-tools: [WebSearch, WebFetch, Read, Write, Agent]
---

# /news-song — News to Suno AI Song

You are running the News-to-Music pipeline for the AI OS.

**Input:** `$ARGUMENTS` — optional focus ticker or theme (e.g., "MSFT", "semiconductors", "crypto"). If empty, scan all portfolio holdings for the most newsworthy story today.

---

## PORTFOLIO WATCHLIST (always scan these first)

| Ticker | Company |
|--------|---------|
| FSELX | Fidelity Select Semiconductors |
| MSFT | Microsoft |
| AAPL | Apple |
| AMPX | Amprius Technologies |
| V | Visa |
| SPOT | Spotify |
| U | Unity Software |
| COST | Costco |
| NVDA | NVIDIA |
| MKL | Markel Group |
| BTC | Bitcoin |
| XRP | XRP |

---

## PIPELINE — ORDERED STEPS

### STEP 1 — News Research (CIRO-Research upstream)
Use WebSearch to find breaking news today for the portfolio tickers (or the specified $ARGUMENTS focus).

Search queries to run:
- `[ticker] news today [current month year]`
- `[ticker] earnings analyst price target [current month year]`
- `[company] stock market [current month year]`

Select the **single most newsworthy story** — prioritize: earnings surprises, major product launches, regulatory actions, macro events affecting multiple holdings.

Output: Structured news brief with headline, source, date, affected tickers, and 3-sentence summary.

---

### STEP 2 — Portfolio Mapping (CIO-Investments upstream)
Map the news to the portfolio:
- Which holding(s) does this affect?
- Sentiment: bullish / bearish / neutral
- Agent economy layer (compute / rails / edge / capital / consumer)
- Position size context (big holding = higher stakes emotionally)

---

### STEP 3 — Creative Brief (News-Analyst-Music)
Translate the news + portfolio mapping into creative raw material:
- **Core Narrative:** The human story underneath the financial story (1 paragraph)
- **Emotional Register:** Primary emotion + secondary undercurrent + arc
- **Themes + Metaphors:** 3 themes, each with a lyrical metaphor candidate
- **Tension Points:** 2 contradictions or ironies in the story
- **Quotable Moments:** 2 specific facts/quotes striking enough to use directly in lyrics

---

### STEP 4 — Production Sheet (Music-Producer)
Set the complete sonic world. All decisions are the Music-Producer's — no constraints imposed by the pipeline.

Required output:
- Song title
- Genre + subgenre
- BPM range
- Key/mode
- Mood interpretation + creative rationale
- Energy arc (intro → outro)
- Instrumentation palette (lead, rhythm, harmony, texture, signature element)
- **Full beat timing cue table** (0:00 → 2:45 minimum)
- Lyricist direction (2–3 sentences)
- Suno style tags (comma-separated, <120 chars)

---

### STEP 5 — Lyrics (Lyricist)
Write full lyrics using the Production Sheet and Creative Brief.

Required structure (minimum):
```
[Intro]
[Verse 1]
[Pre-Chorus]
[Chorus]
[Verse 2]
[Pre-Chorus]
[Chorus]
[Bridge]
[Chorus]
[Outro]
```

Rules:
- Every section wrapped in correct Suno structure markers
- Syllable count matches tempo
- No financial jargon — transform data into emotion and image
- Specific details from Quotable Moments must appear somewhere in the lyrics
- Strong point of view — write from inside a perspective, not above it

---

### STEP 6 — Suno Prompt Assembly (Suno-Prompter)
Assemble the final copy-paste-ready package:

```
╔══════════════════════════════════════╗
║     SUNO AI PROMPT PACKAGE           ║
╚══════════════════════════════════════╝

TITLE:
[title]

STYLE TAGS:
[tags]

LYRICS:
[full lyrics with structure markers + inline production annotations]

─────────────────────────────────────
PRODUCER NOTES:
[beat timing cue table]
[character count]
[any Suno-specific guidance]
─────────────────────────────────────
```

Run quality checklist before delivery:
- [ ] Title
- [ ] Style tags (coherent, <120 chars)
- [ ] All structure markers present
- [ ] Inline production annotations at key moments
- [ ] Beat timing cues in producer notes
- [ ] Character count checked (<2500 chars for lyrics field)
- [ ] Copy-paste ready

---

## REFERENCE
Full Suno AI prompting guide: `~/.claude/skills/news-song/suno_guide.md`
