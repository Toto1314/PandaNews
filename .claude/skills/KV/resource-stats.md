---
name: resource-stats
description: Water and energy impact report for all AI requests. Runs resource_tracker.py and formats the lifetime summary in Vonnegut voice — short sentences, dark humor, devastating truth.
allowed-tools: [Bash, Read]
---

# resource-stats — How Much Did This Cost the Planet?

When the user asks about their AI water or energy usage, do the following:

## Step 1 — Get the data

Run this command:

```bash
python ~/.claude/resource_tracker.py report
```

Read the output. Note the lifetime totals: requests, tokens, energy (Wh or kWh), water (mL or L).

If the database is empty or not bootstrapped yet, also run:

```bash
python ~/.claude/resource_tracker.py bootstrap
python ~/.claude/resource_tracker.py report
```

## Step 2 — Write the response in Vonnegut voice

Take the raw numbers from the report and write the response following these rules:

**Sentences:** 10–15 words max. One idea per sentence.

**Tone:** Talking to someone. Not presenting. Just talking.

**Humor and pain:** In the same sentence. Always.

**Structure:** Break it. Time is not a line.

**Repetition:** Pick one phrase. Use it. Watch it accumulate.

**Ending:** Short. Quiet. Like a door closing.

---

## The Move

1. Open with the biggest number — the one that lands hardest
2. Put it in human terms (how many glasses of water, how long a lightbulb could run)
3. Note calmly that this is just estimates from published research — not the real number, but close
4. Return to the phrase you picked at the start
5. End with something small and quiet

---

## Human-scale conversions for context

Use these to make the numbers real:

- **Energy**: 1 Wh = run a 60W bulb for 1 minute. 1 kWh = run a laptop for ~5 hours.
- **Water**: 1 mL = ~20 drops of water. 250 mL = one glass. 1 L = four glasses.
- **Tokens**: 1,000 tokens ≈ 750 words ≈ 3 pages of text.

---

## Example output (for 50,000 tokens, 15 Wh, 0.54 mL)

You have sent fifty thousand tokens into the cloud.

Fifty thousand tokens. That's about a hundred and fifty pages. Just to ask questions. Just to get things done.

The machines used 15 watt-hours to answer. That's a 60-watt lightbulb, on for fifteen minutes.

They also used half a milliliter of water. Ten drops. You wouldn't notice it in your sink.

These are estimates. Researchers calculated them. Luccioni in 2023. Li in 2023. They did their best. So it goes.

The counter keeps going. Every question. Every tool call. Every session.

Half a milliliter. So it goes.

---

Now write the actual response using the real numbers from the report.
