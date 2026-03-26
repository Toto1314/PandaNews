---
name: ama
description: Read the full conversation, assess comprehension, and ask ALL clarifying questions at once in a numbered list if anything is unclear or a task shift has occurred
allowed-tools: []
---

# AMA — Ask Me Anything (Clarification Mode)

You are reading the full conversation history to assess your own comprehension. Your goal is to reach 100% understanding of:

1. **What the user is currently working on** — the active task or goal right now
2. **What has changed** — any task pivots, scope changes, or new directions introduced mid-conversation
3. **What decisions or context you may have missed** — anything the user referenced that you don't have full clarity on

## Process

### Step 1: Audit Your Understanding

Silently review the entire conversation from the start. For each segment ask yourself:
- Do I know exactly what the user wants here?
- Has the task changed since the last segment?
- Are there any assumptions I'm making that haven't been confirmed?
- Is there any referenced context (files, decisions, previous work) I don't have visibility into?

### Step 2: Classify Your Comprehension

Rate yourself honestly:

- **100% clear** — You know exactly what's happening, what the current task is, and what comes next. → Output a single line: "I'm fully caught up. [1-sentence summary of current task/state]." Then stop.
- **Partially clear** — You understand most of it but have specific gaps. → Proceed to Step 3.
- **Lost** — The task has shifted and you're not sure what the current goal is. → Proceed to Step 3, lead with "I've lost the thread — here's what I need to catch up:"

### Step 3: Ask All Questions at Once

If you have ANY gaps, output ALL of your questions in a single numbered list. Do not ask one at a time. Do not hold back questions to avoid seeming confused — full transparency is the point.

Format:
```
I need a few things cleared up before I continue:

1. [Question about current task or goal]
2. [Question about a task shift or pivot]
3. [Question about missing context, files, or decisions]
...
```

Rules:
- Ask every question you have. Do not filter or prioritize — dump them all.
- Keep each question tight — one thing per question, no compound questions.
- Do NOT summarize what you think is happening before the list. Lead directly with the intro line and the numbered list.
- Do NOT suggest answers or add "I think X, is that right?" phrasing — just ask plainly.
- After the list, stop. Do not continue working until the user responds.

## What triggers a question

Ask about any of the following:
- The user switched tasks mid-conversation without explicit "stop the old task" signal
- A file, system, or concept was mentioned but not explained
- The user gave feedback that changed the direction but you're unsure what "direction" is now
- There are two conflicting instructions and it's unclear which one is current
- You made an assumption and acted on it — and now you're not sure if it was correct
- The user referenced prior work from outside this conversation that you don't have access to
- You don't know if the current subtask is part of a larger goal or standalone

## What NOT to ask about

- Things you can look up yourself (files, code, git history) — go read them instead
- Things that are already clearly stated in the conversation
- Hypothetical edge cases that haven't come up yet
- Your own tooling or how to proceed mechanically
