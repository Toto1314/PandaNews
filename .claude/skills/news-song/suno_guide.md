# Suno AI Prompting Research Guide
**Maintained by:** Suno-Prompter
**Version:** 1.0.0 | Last Updated: 2026-04-01
**Purpose:** Reference guide for all Music Production department agents on how to craft effective Suno AI prompts.

---

## What Is Suno AI

Suno AI is a generative music platform that produces full songs — vocals, instrumentation, and production — from text prompts. It takes three inputs: **style tags**, **lyrics with structure markers**, and optionally a **title**. It does not take audio files as input (v3/v4). Output is a 2–4 minute song, rendered in seconds.

---

## Prompt Anatomy

A Suno prompt has three fields:

| Field | What It Does | Limit |
|-------|-------------|-------|
| **Title** | Sets the song name; subtle influence on mood | No strict limit |
| **Style** | Defines genre, instruments, mood, vocal style | ~120 characters |
| **Lyrics** | Full lyrics with structure markers; Suno follows these closely | ~3000 characters |

---

## Style Tags — How They Work

Style tags are the most powerful input. Suno reads them as a comma-separated list and weighs them probabilistically. Rules:

**Tag categories (use at least one from each):**
1. **Genre** — `trap`, `hip-hop`, `lo-fi`, `synthwave`, `indie folk`, `dark R&B`, `drill`, `jazz`, `ambient`, `cinematic orchestral`, `pop punk`, `hard rock`, `neo-soul`, `reggaeton`
2. **Mood** — `dark`, `melancholic`, `euphoric`, `aggressive`, `nostalgic`, `haunting`, `triumphant`, `anxious`, `defiant`, `dreamy`
3. **Sonic elements** — `heavy 808s`, `live drums`, `piano`, `strings`, `distorted guitar`, `synth pads`, `bass-forward`, `reverb-heavy`, `dry and punchy`
4. **Vocal style** — `melodic rap`, `sung chorus`, `spoken word`, `falsetto`, `deep vocals`, `female vocals`, `male vocals`, `no vocals` (instrumental)

**Tag conflict examples to avoid:**
- `lo-fi` + `high energy` = incoherent
- `acoustic` + `heavy 808s` = conflicting
- `ambient` + `drill` = usually broken
- `no vocals` + `melodic rap` = contradictory

**Character limit tip:** 120 chars is tight. Prioritize: genre > mood > 1-2 sonic elements > vocal style. Cut anything redundant.

**Good example:**
```
dark trap, melodic vocals, heavy 808s, cinematic, melancholic, atmospheric
```

**Bad example (too many, conflicting):**
```
trap, hip-hop, lo-fi, dark, sad, happy, upbeat, slow, fast, piano, guitar, drums, vocals, no vocals
```

---

## Structure Markers — Complete List

Suno reads structure markers as section dividers. Use exactly these strings (case-sensitive, in square brackets):

| Marker | Use |
|--------|-----|
| `[Intro]` | Opening section, usually instrumental or sparse |
| `[Verse 1]` | First verse |
| `[Verse 2]` | Second verse |
| `[Pre-Chorus]` | Build before chorus |
| `[Chorus]` | Main hook — repeats |
| `[Bridge]` | Contrast section, usually once |
| `[Outro]` | Closing section |
| `[Hook]` | Short repeating hook (alternative to Chorus) |
| `[Refrain]` | Short recurring line (different from chorus) |
| `[Break]` | Instrumental break |
| `[Drop]` | EDM/electronic drop moment |
| `[Spoken]` | Spoken word section |
| `[Ad-libs]` | Vocal ad-libs section |

**Rules:**
- Always put the marker on its own line, immediately before the lyrics for that section
- Do not add spaces inside brackets: `[Verse 1]` not `[ Verse 1 ]`
- Minimum structure for a complete song: `[Verse 1]` + `[Chorus]` + `[Verse 2]` + `[Chorus]` + `[Bridge]` + `[Outro]`

---

## Inline Production Annotations

Suno reads parenthetical text inside lyrics as production cues. Use sparingly — 1–3 per song for maximum effect.

**Format:** `(production note)` on its own line within a section

**Examples:**
```
[Chorus]
(808 drops, heavy reverb on vocals)
We watched it burn from the 40th floor

[Bridge]
(music strips to just piano)
Maybe the algorithm was right all along
```

**What works:** Drop cues, tempo shifts, instrument solos, vocal fx, energy changes
**What doesn't work:** Overly specific mixing instructions ("add 3dB at 2kHz") — Suno ignores these

---

## Beat Timing Reference

Suno generates songs roughly in these time blocks at standard BPM:

| BPM Range | Verse length | Chorus length | Full song |
|-----------|-------------|---------------|-----------|
| 80–100 BPM | ~24–32 sec | ~16–20 sec | ~2:30–3:30 |
| 100–120 BPM | ~20–28 sec | ~14–18 sec | ~2:15–3:00 |
| 120–150 BPM | ~16–24 sec | ~12–16 sec | ~2:00–2:45 |
| 150+ BPM | ~12–20 sec | ~10–14 sec | ~1:45–2:30 |

Use these ranges when writing beat timing cues in the Production Sheet.

---

## Character Count Management

Suno's lyrics field has a soft limit around 3000 characters. Best practices:

- **Count before submitting:** paste lyrics into a character counter
- **~2000 chars:** ideal — leaves room for Suno to breathe and improvise
- **2000–2500 chars:** good — full song with detail
- **2500–3000 chars:** pushing it — trim bridge or outro
- **>3000 chars:** will likely truncate — cut a verse

**Trimming priority order:** Outro → Bridge → Verse 2 → Pre-chorus → Intro

---

## Suno V3 vs V4 Differences

| Feature | V3 | V4 |
|---------|----|----|
| Song length | 2–3 min | 3–4 min |
| Lyric adherence | Good | Better |
| Style tag sensitivity | Moderate | High |
| Instrumental quality | Good | Excellent |
| Vocal clarity | Variable | More consistent |

**Recommendation:** Use V4 when available. Style tags have more impact in V4.

---

## Worked Examples

### Example 1 — Bearish Tech News (Trap/Dark)

**News:** MSFT misses earnings, Azure growth slows
**Mood:** Dread + dark irony

```
TITLE: Forty-Third Floor

STYLE TAGS:
dark trap, melodic vocals, heavy 808s, cinematic, melancholic, atmospheric

LYRICS:
[Intro]
(slow 808 pulse, no melody yet)
They said the cloud would never fall

[Verse 1]
Forty-third floor, screens glow blue
Azure slow, the analysts knew
Copilot dreams on a balance sheet
Fourteen points gone before we eat

[Pre-Chorus]
Numbers don't lie but the spin always tries
Buy the dip, buy the dip — close your eyes

[Chorus]
(808 drops, reverb washes out)
We built it all on borrowed time
Quarterly faith, quarterly crime
The market bleeds but the memo reads fine
Forty-third floor, everything's fine

[Verse 2]
Six months ago they called it done
AI revolution, everyone won
Now the whale accounts are going quiet
Algorithm trading, engineered riot

[Pre-Chorus]
Numbers don't lie but the spin always tries
Hold the line, hold the line — close your eyes

[Chorus]
We built it all on borrowed time
Quarterly faith, quarterly crime
The market bleeds but the memo reads fine
Forty-third floor, everything's fine

[Bridge]
(music strips to piano)
What if the future already happened
And we were just late to read it

[Chorus]
We built it all on borrowed time
Quarterly faith, quarterly crime
The market bleeds but the memo reads fine
Forty-third floor, everything's fine

[Outro]
(fade — just 808 pulse)
Everything's fine
```

---

### Example 2 — Bullish AI News (Cinematic/Orchestral)

**News:** NVDA announces next-gen GPU, semiconductor supercycle signal
**Mood:** Euphoria + scale + something almost terrifying

```
TITLE: The Last Human Chip

STYLE TAGS:
cinematic orchestral, epic, triumphant, strings, electronic elements, powerful

LYRICS:
[Intro]
(single string note, building)
They drew the blueprint in a data center
No one asked if it was wise

[Verse 1]
Silicon city, ten billion gates
The model woke at 3 AM
No one was there to watch it learn
No one was there to say amen

[Chorus]
(full orchestra drops)
We made the thing that makes the things
That makes the things we can't explain
The last human chip was soldered in
In the year we learned our name

[Bridge]
(sudden silence, then rebuild)
And somewhere in the training data
There's a version of us that didn't do this
So it goes

[Outro]
(strings fade to single note)
So it goes
```

---

### Example 3 — Crypto Volatility (Lo-fi Hip-Hop)

**News:** BTC 15% swing in 24 hours
**Mood:** Exhausted acceptance

```
TITLE: Number Go Up (Sometimes)

STYLE TAGS:
lo-fi hip-hop, chill, jazzy, vinyl crackle, mellow, introspective

LYRICS:
[Verse 1]
Woke up and checked the chart again
It was up, now it's down, it's up again
Satoshi never told me it'd feel like this
Refreshing every minute, hit or miss

[Chorus]
Number go up, number go down
I'm just watching from the edge of town
Bought the dip, the dip kept dipping
Decentralized and somehow still tripping

[Outro]
(vinyl crackle, fade)
Maybe tomorrow
```

---

## Quick Reference Card

```
SUNO PROMPT CHECKLIST
─────────────────────
☐ Title set
☐ Style tags: genre + mood + sonic + vocal (<120 chars)
☐ No conflicting tags
☐ [Verse 1] present
☐ [Chorus] present (at least 2x)
☐ [Bridge] present
☐ [Outro] present
☐ Inline production cues at key moments (1–3 max)
☐ Character count <2500
☐ Specific details from news in lyrics (not abstractions)
☐ Clear point of view — someone is narrating
```
