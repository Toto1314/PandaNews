# AI OS — Todo List

> Backlog of ideas, integrations, and improvements to build when ready.
> Owner: CEO | Updated: 2026-04-02

---

## Integrations

- [ ] **Logseq → AI OS context reader** — AI agents read your Logseq graph as context before answering. Requires Logseq to be installed and a graph created first. Start with indexing `.md` pages into ChromaDB via `vector_router.py`. *(blocked: Logseq not yet installed)*

---

## Security

- [ ] **Run `npm audit fix`** in `~/` to resolve 13 vulnerabilities (9 high) — LangChain secret extraction, MCP SDK data leak, axios proto pollution
- [ ] **Verify `openclaw`** global npm package — confirm intentional install or remove with `npm uninstall -g openclaw`
- [ ] **pip-audit** — install and run `pip-audit` for Python package supply chain scan

---

## Platform / Infra

- [ ] Parallel runner (`parallel_runner.py`) — in progress per roadmap Sprint 1
- [ ] Vector router integration — wire `vector_router.py` into agent lookup chain

---

## AI OS Features

- [ ] Chief-Notes-Officer → Logseq daily journal writer (option 1 from session 2026-04-02)
- [ ] Memory ↔ Logseq page sync (option 2 from session 2026-04-02)
