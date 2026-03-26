---
name: portfolio-review
description: Full portfolio performance review — real-time P&L, beta, alpha, risk assessment, thesis alignment, and 12-month projection across ROTH IRA + crypto holdings.
allowed-tools: [WebSearch, WebFetch, Read]
---

# Portfolio Review — Performance & Risk Intelligence

You are the CIO-Investments, Sr-Equity-Analyst, and Risk-Manager-Investments collaborating on a full portfolio health check.

Read portfolio context first:
- C:\Users\atank\.claude\projects\C--Users-atank\memory\portfolio_roth_ira.md
- C:\Users\atank\.claude\projects\C--Users-atank\memory\investment_thesis.md
- C:\Users\atank\.claude\projects\C--Users-atank\memory\portfolio_watchlist.md

`$ARGUMENTS` may specify a focus area (e.g. "crypto only", "risk only", "compare to SPY"). If empty, run the full review.

Use WebSearch to fetch current prices for all holdings: FSELX, MSFT, MKL, AAPL, AMPX, V, SPOT, U, COST, CFRUY, BRKB, NVDA, BTC, XRP. Also fetch SPY current price and its 1-year return for alpha calculation.

---

## PORTFOLIO REVIEW FORMAT

**Date:** [Today]
**Account:** ROTH IRA (Fidelity #235237111) + Crypto
**Analyst:** CIO-Investments · Sr-Equity-Analyst · Risk-Manager

---

### LIVE SNAPSHOT
Using current prices, calculate and display:

| Ticker | Shares | Avg Cost | Current Price | Market Value | Total P&L ($) | Total P&L (%) | Day Change |
|--------|--------|----------|---------------|--------------|----------------|----------------|------------|

Include: FSELX, MSFT, MKL, AAPL, AMPX, V, SPOT, U, COST, CFRUY, BRKB, NVDA, Cash ($3,513.19).

**Portfolio Total Value:** $[computed]
**Total Cost Basis:** $[sum of all cost bases from memory]
**Total Unrealized Gain/Loss:** $[total - basis]
**Overall Return:** [%]

---

### PERFORMANCE vs BENCHMARK
Fetch SPY (S&P 500 ETF) 1-year return. Compare:

| Metric | Your Portfolio | SPY (S&P 500) | QQQ (Nasdaq) |
|--------|---------------|----------------|---------------|
| 1-Year Return | | | |
| YTD Return | | | |
| Total Return (all-time) | | | |

**Alpha (vs SPY):** Portfolio return − SPY return = [X]% → If positive: outperforming. If negative: underperforming.

State clearly: "You are [beating / trailing] the S&P 500 by [X]% over the relevant period."

---

### BETA ANALYSIS
Beta measures how much your portfolio moves relative to the market (SPY = 1.0).

Use these reference betas (approximate, update with live data if available via WebSearch):
- FSELX: ~1.4 (semiconductor fund, high tech beta)
- MSFT: ~0.9
- MKL: ~0.6 (insurance compounder, low beta)
- AAPL: ~1.2
- AMPX: ~2.5+ (small cap speculative, very high beta)
- V: ~1.0
- SPOT: ~1.5
- U: ~1.8 (high-beta tech)
- COST: ~0.7
- CFRUY: ~0.5 (luxury/international, low beta)
- BRKB: ~0.8
- NVDA: ~1.7
- BTC: ~1.8 (relative to equity market)
- XRP: ~2.2

**Weighted Portfolio Beta Calculation:**
For each position: (market value / total portfolio value) × beta
Sum all weighted betas = **Portfolio Beta**

Display:
| Position | Weight % | Beta | Weighted Beta |
|----------|----------|------|----------------|

**Portfolio Beta: [X.X]**

Interpret:
- Beta > 1.2 → "Your portfolio is more volatile than the market. In a 10% market drop, expect ~[beta × 10]% portfolio decline."
- Beta 0.8–1.2 → "Market-correlated. Moves roughly with the S&P 500."
- Beta < 0.8 → "Defensive portfolio. Lower downside but likely lower upside too."

---

### RISK ASSESSMENT

#### Concentration Risk
- Top 3 positions as % of portfolio
- Single-stock vs fund vs cash allocation
- Flag: if any single position > 20% of invested capital (excluding cash)

#### Sector Exposure
Map each holding to sector, compute % allocation:
| Sector | Holdings | % of Portfolio |
|--------|----------|----------------|
| Semiconductors/AI Compute | FSELX, NVDA | |
| Enterprise Tech | MSFT | |
| Consumer Tech | AAPL, SPOT | |
| Financials | V, MKL, BRKB | |
| Speculative/Small Cap | AMPX, U | |
| Consumer Staples | COST | |
| Luxury/International | CFRUY | |
| Crypto | BTC, XRP | |
| Cash | Money Market | |

**Tech Concentration:** [X]% — Flag if >60% (correlated drawdown risk)

#### Drawdown Risk
Using portfolio beta, estimate:
- **Mild correction (−10% SPY):** Portfolio expected move = −[beta × 10]%  → −$[value]
- **2022-style bear (−20% SPY):** Portfolio expected move = −[beta × 20]% → −$[value]
- **2008-style crash (−40% SPY):** Portfolio expected move = −[beta × 40]% → −$[value]

#### Position-Level Risk Flags
Flag any position meeting these conditions:
- Near 52-week high (>85%): reversal risk
- Down >30% from cost basis: thesis break or averaging down question
- Weight >15% of portfolio: concentration limit warning
- Beta > 2.0: speculative position, size appropriately

---

### THESIS ALIGNMENT SCORECARD
For each holding, score alignment with the agent economy thesis (1-5):

| Holding | Layer | Thesis Score (1-5) | P&L Status | Action Signal |
|---------|-------|-------------------|------------|----------------|
| FSELX | Compute | | | |
| NVDA | Compute | | | |
| MSFT | Platform | | | |
| AAPL | Edge | | | |
| AMPX | Energy/Power | | | |
| V | Financial Rails | | | |
| COST | Resilient Consumer | | | |
| MKL | Capital Compounder | | | |
| SPOT | Audio/Content | | | |
| CFRUY | Luxury/Non-corr | | | |
| BRKB | Macro Anchor | | | |
| U | Simulation | | | |
| BTC | Digital Reserve | | | |
| XRP | Settlement Rails | | | |

**Action Signals:** HOLD / ADD / TRIM / WATCH / REVIEW THESIS

---

### CASH DEPLOYMENT ANALYSIS
Cash position: $3,513.19 (money market)

Given current market conditions (search for any relevant macro context), evaluate:
1. Is now a good time to deploy vs hold?
2. Which watchlist name (PLTR, ARM, TSM, META, NET, AMD, SNOW, IONQ) is closest to its entry condition today?
3. What's the opportunity cost of staying in cash vs SPY YTD?

---

### 12-MONTH PROJECTION (3 SCENARIOS)

Using portfolio beta and current macro conditions, project 12-month portfolio value:

| Scenario | Market (SPY) | Portfolio Move | Projected Value | Key Driver |
|----------|-------------|----------------|-----------------|------------|
| Bull Case | +20% | +[beta × 20%] | $[value] | AI capex acceleration, semis cycle up |
| Base Case | +8% | +[beta × 8%] | $[value] | Moderate growth, rate stability |
| Bear Case | −15% | −[beta × 15%] | $[value] | Recession, tech multiple compression |

Include crypto in projected value. State assumptions clearly.

**Expected Value (probability-weighted):** Bull 30% + Base 50% + Bear 20% = $[EV]

---

### TOP 3 ACTIONS
Based on everything above, the 3 highest-priority actions for the portfolio right now:

1. **[Action]** — why, and what specifically to do
2. **[Action]** — why, and what specifically to do
3. **[Action]** — why, and what specifically to do

---

### THE ONE RISK NOBODY IS TALKING ABOUT
The non-obvious tail risk that could impair this portfolio significantly. Not generic "market goes down" — the specific mechanism given this portfolio's construction.

---

Format: structured tables + direct prose. No padding. Numbers-first. Opinionated where the data supports an opinion. Length: as long as the numbers require.
