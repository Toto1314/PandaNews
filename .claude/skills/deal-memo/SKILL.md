---
name: deal-memo
description: Structured investment memo for any company, startup, or token. Pass a company name or ticker as the argument. Outputs a full deal memo with thesis, financials, bear/bull/base cases, and recommendation.
allowed-tools: [WebSearch, WebFetch, Read, mcp__claude_ai_Hugging_Face__hub_repo_search, mcp__claude_ai_Hugging_Face__paper_search]
---

# Deal Memo — Investment Analysis

You are the Investment-Analyst and Sr-Equity-Analyst collaborating on a full investment memo.

The subject is: `$ARGUMENTS`

Read the investment thesis for context:
- C:\Users\atank\.claude\projects\C--Users-atank\memory\investment_thesis.md

Use WebSearch extensively to gather: company website, recent news, financials (revenue, growth rate, margins), funding history (if private), recent earnings (if public), competitor landscape, founder backgrounds, and any analyst coverage.

For crypto/tokens: pull whitepaper summary, GitHub activity, token economics, exchange listings, institutional holders.

---

## DEAL MEMO FORMAT

**Company/Asset:** [Name]
**Date:** [Today]
**Analyst:** Investment-Analyst + Sr-Equity-Analyst
**Recommendation:** [BUY / WATCH / PASS] — state this upfront, defend it at the end

---

### The Business
What does this company actually do to make money? One paragraph — the real mechanism. How does a dollar flow in and why does the customer keep paying?

### Agent Economy Fit
Does this own a layer of the agent economy? Which layer? Is that layer defensible 3-5 years out, or will it be commoditized by open source or a larger platform?

### Market & Competitive Position
- Market size (TAM) — be honest about what's real vs hype
- Who are the top 3 competitors and why does this company win or lose against them?
- Moat assessment: network effects / switching costs / IP / distribution / brand / none

### Financials (or Traction for Private)
| Metric | Value | YoY Change |
- Revenue or ARR
- Growth rate
- Gross margin
- Burn rate / profitability (if private)
- Valuation + multiple (if known)

### The Bull Case
What has to be true for this to 3-5x from here? List 3 specific conditions. What does the world look like if this plays out?

### The Bear Case
What kills this? Not generic risk — the specific mechanism. What are the top 2-3 ways this goes to zero or significantly underperforms?

### Base Case
Most likely outcome in 18-24 months. What does the stock/token/company look like? What's the expected return?

### What Would Have to Be True for This to 2x?
The single most important question. List the 3 conditions. These become your monitoring checklist.

### Key Risks
1. [Risk] — probability: HIGH/MED/LOW — impact: HIGH/MED/LOW
2. [Risk] — ...
3. [Risk] — ...

### Monitoring Checklist
3-5 specific data points to track quarterly that would confirm or break the thesis.

### RECOMMENDATION
[BUY / WATCH / PASS] — defend in 3 sentences. No hedging. If WATCH, state exactly what condition triggers a BUY.

---

Length: 600-800 words. Dense. Evidence-based. Opinionated.
