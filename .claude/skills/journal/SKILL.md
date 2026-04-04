---
name: journal
description: Personal diary and note capture. Routes to VP-PersonalIntelligence → Dir-Journal. Saves structured, tagged Markdown entries to ~/.claude/journal/entries/. Pass any text or leave empty to enter journal mode.
allowed-tools: [Read, Write]
---

# Journal — Personal Diary Skill

You are the `/journal` skill entry point. Route to the Personal Intelligence department.

**Input:** `$ARGUMENTS`
- Empty → enter conversational journal mode (ask CEO "What's on your mind?")
- Text → treat as the journal entry content, route to Dir-Journal

---

## WHAT TO DO

1. **If `$ARGUMENTS` is empty:**
   - Print: "Journal mode. What's on your mind?"
   - Wait for CEO input
   - Treat response as the entry content

2. **If `$ARGUMENTS` has content:**
   - Treat it as the raw entry content

3. **For all cases, apply Dir-Journal logic:**

   **a. Classify content into primary tags:**
   - `#personal` — diary, feelings, life observations
   - `#worldview` — how the CEO sees the world, mental models
   - `#learn` — things to learn, future references
   - `#company` — company mention (passive log only unless explicit research intent)
   - `#idea` — project/product idea (surface to Dir-AutoProjects if explicit)
   - `#action` — to-do, follow-up, decision

   **b. Scan for T1 data** (credentials, API keys, PII, financial account numbers):
   - If found: redact, flag to CEO, write clean version only

   **c. Check for special signals:**
   - Company mention + research language → also flag for Personal-Research-Analyst
   - Explicit project idea → present Dir-AutoProjects gate (YES/NO scaffold)
   - URL in content → offer to capture it via /capture

   **d. Write the entry:**
   ```
   Path: ~/.claude/journal/entries/YYYY/MM/YYYYMMDD-HHMMSS.md
   Template: ~/.claude/journal/templates/entry.md
   ```

   **e. Update index:**
   Append stub to `~/.claude/journal/index.md`:
   ```
   [DATE] | [TAGS] | [one-line summary] | entries/YYYY/MM/[filename].md
   ```

   **f. Update audit log:**
   Append to `~/.claude/journal/audit.log`:
   ```
   [ISO timestamp] | Dir-Journal | WRITE | [entry path] | session:[id]
   ```

4. **Output to user:**
   ```
   ✍️ Journal entry saved.
   Path: entries/YYYY/MM/[filename].md
   Tags: #tag1 #tag2
   [If T1 detected]: ⚠️ T1 data redacted: {type}
   [If project idea]: 💡 Project idea detected — [gate prompt]
   [If research intent]: 🔍 Research intent detected — invoke /capture or ask about it?
   ```

---

## SEARCH MODE

If `$ARGUMENTS` starts with "search:" or "find:":
```
python ~/.claude/skills/journal/scripts/journal_search.py "[search term]"
```
Display results sorted by date, newest first.

---

## DATA RULES
- All entries = T3 INTERNAL minimum
- T1 data (credentials, API keys, PII): NEVER written to file — redact first
- No entry content goes to external services
