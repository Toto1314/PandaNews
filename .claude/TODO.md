# AI OS — Todo List

> Backlog of ideas, integrations, and improvements to build when ready.
> Owner: CEO | Updated: 2026-04-02

---

## Integrations

- [ ] **Logseq → AI OS context reader** — AI agents read your Logseq graph as context before answering. Requires Logseq to be installed and a graph created first. Start with indexing `.md` pages into ChromaDB via `vector_router.py`. *(blocked: Logseq not yet installed)*

---

## Security

### Quick wins (do first)
- [x] **[SEC-1] Add security controls to `DATA_CLASSIFICATION.md`** — v1.1 — "Application Security Controls" section added *(done 2026-04-02)*
- [x] **[SEC-2] Add security requirements block to `AGENT_STANDARDS.md`** — v2.1.0 — external-facing system agents section + audit checklist item added *(done 2026-04-02)*
- [x] **[SEC-3] Update `Application-Security-Engineer.md`** — v1.1.0 — Core Responsibilities 8-10 + Mandatory AppSec Controls Checklist added *(done 2026-04-02)*

### Medium effort
- [ ] **[SEC-4] Hardcoded secrets scan** — grep all 8 projects for API keys/passwords/tokens; check `.gitignore` covers `.env*`; check `dist/build/out` for leaked creds. Report by project + file + severity.
- [ ] **Run `npm audit fix`** in `~/` — resolve 13 vulnerabilities (9 high): LangChain secret extraction, MCP SDK data leak, axios proto pollution
- [ ] **Verify `openclaw`** global npm package — confirm intentional or remove with `npm uninstall -g openclaw`
- [ ] **pip-audit** — install and run `pip-audit` for Python package supply chain scan

### Heavy lift (later — Tier 2, needs CISO clearance)
- [ ] **[SEC-5] Full OWASP security audit** across all 8 projects — auth controls, injection, CORS, CVE deps, debug endpoints, IDOR, security headers. Findings → `AUDIT_FINDINGS.md` (Critical/High/Medium/Low). CAE-Audit sign-off required.

---

## Platform / Infra

- [x] Parallel runner (`parallel_runner.py`) — **EXISTS and has been run** *(confirmed 2026-04-02)*
- [x] Vector router (`vector_router.py`) + ChromaDB (`vector_db/`) — **EXISTS and populated** *(confirmed 2026-04-02)*
- [ ] Wire `vector_router.py` into live agent lookup chain (built but not wired into Claude routing)
- [ ] Create `session_notes/` directory — CNO is documented to write here but dir doesn't exist
- [ ] Create `token_budget.json` — `token_tracker.py` reads this for budget config; currently running on defaults
- [ ] MetaMCP / per-agent tool ACLs — `Dir-MCPHub` documented but no MetaMCP config exists; MCP limited to 2 servers (Playwright + filesystem)

---

## AI OS Features

- [ ] Chief-Notes-Officer → Logseq daily journal writer (option 1 from session 2026-04-02)
- [ ] Memory ↔ Logseq page sync (option 2 from session 2026-04-02)

---

## Skills — Need Code (Docs-Only Right Now)

- [ ] `/news-song` — has `SKILL.md` + `suno_guide.md` but zero Python; full pipeline needs to be built
- [ ] 23 of 27 skills are prompt/docs only — no executable code; prioritize which skills get real automation

---

## OpenClaw Integration

- [ ] Audit conflict: `kiriko_bot.py` and OpenClaw both use the same Telegram bot token — decide which owns the bot (one must be decommissioned or they need separate tokens)
- [ ] Map OpenClaw capabilities (cron, agents/, memory/, gateway:18789, skills/) against AI OS gaps — determine what to delegate vs. rebuild
- [ ] Decide integration model: OpenClaw as execution runtime vs. standalone parallel system
