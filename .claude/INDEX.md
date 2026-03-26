# 🧠 AI OS — Master Index
> **Start here.** Fast lookup for the Lead Orchestrator.
> [`CLAUDE.md`](./CLAUDE.md) = master policy register (full rules, routing, history).
> This file = navigation hub.

**v1.8.7** · Owner: Lead Orchestrator · Approved by: CEO

---

## 🗂️ Document Map

| File | Purpose | Open When |
|------|---------|-----------|
| 📍 **[`INDEX.md`](./INDEX.md)** | Navigation hub — you are here | Finding anything fast |
| 📜 **[`CLAUDE.md`](./CLAUDE.md)** | Master policy: routing, org chart, rules, version history | Every session (auto-loaded) |
| 🗺️ **[`SYSTEM_MAP.md`](./SYSTEM_MAP.md)** | Mermaid diagrams: authority, routing, risk tiers, dept chains | Seeing the system visually |
| 🏢 **[`ORG_CHARTS.md`](./ORG_CHAdRTS.md)** | Full org charts for every department | Full department hierarchy |
| ⚙️ **[`DEPARTMENT_WORKFLOWS.md`](./DEPARTMENT_WORKFLOWS.md)** | Intake → process → output → handoff → SLAs per dept | Routing between departments |
| 📐 **[`AGENT_STANDARDS.md`](./AGENT_STANDARDS.md)** | Agent template, required sections, audit checklist | Writing or auditing agent files |
| 🔄 **[`CHANGE_MANAGEMENT.md`](./CHANGE_MANAGEMENT.md)** | Change process, SoD matrix, what needs CEO approval | Before any structural change |
| 📋 **[`CHANGELOG.md`](./CHANGELOG.md)** | Audit trail: every change ever made | Tracking history, logging changes |
| 🔒 **[`DATA_CLASSIFICATION.md`](./DATA_CLASSIFICATION.md)** | Data tiers T1–T4, agent handling rules, MCP policy | Anytime an agent touches data |
| 🔍 **[`AUDIT_FINDINGS.md`](./AUDIT_FINDINGS.md)** | Open and resolved CAE-Audit findings | Reviewing system health |
| 🤖 **[`agents/`](./agents/)** | 135 agents in 17 department folders | Invoking or updating a specific agent |
| ↳ [`pipeline/`](./agents/pipeline/) | orchestrator · scout · architect · builder · validator · boost · Local-Model-Router · User-Prompt-Optimizer | |
| ↳ [`governance/`](./agents/governance/) | AI-Automation-Council · GRC-Council | |
| ↳ [`c-suite/`](./agents/c-suite/) | All 16 C-level agents (COO, CISO, CTO, CPO, CFO, etc.) | |
| ↳ [`audit/`](./agents/audit/) | CAE-Audit chain | |
| ↳ [`security/`](./agents/security/) | CISO chain | |
| ↳ [`engineering/`](./agents/engineering/) | CTO chain | |
| ↳ [`product/`](./agents/product/) | CPO chain | |
| ↳ [`finance/`](./agents/finance/) | CFO chain | |
| ↳ [`legal/`](./agents/legal/) | GC-Legal chain | |
| ↳ [`gtm/`](./agents/gtm/) | CRO-GTM chain | |
| ↳ [`investments/`](./agents/investments/) | CIO-Investments chain | |
| ↳ [`data/`](./agents/data/) | CDO-Data chain | |
| ↳ [`devops/`](./agents/devops/) | CPlatO-DevOps chain | |
| ↳ [`ai-ml/`](./agents/ai-ml/) | CAIO-AI chain + Dir-BrowserOps | |
| ↳ [`design/`](./agents/design/) | CCO-Design chain | |
| ↳ [`strategy/`](./agents/strategy/) | CSO-Strategy chain | |
| ↳ [`prompt-eng/`](./agents/prompt-eng/) | CPrO-Prompting chain | |
| ↳ [`research/`](./agents/research/) | CIRO-Research chain | |

---

## ⚡ Routing Quick Reference

> Full decision tree: [`CLAUDE.md` → Routing Logic](./CLAUDE.md)

| Task | First Call | Notes |
|------|-----------|-------|
| 🏗️ Build / implement / refactor | `CPO` → `CTO-Engineering` | Tier-scale CISO review |
| 🔬 Research / analysis / market scan | `CIRO-Research` | → relevant dept |
| 🔐 Security review / threat model | `CISO` | Always blocking gate |
| ⚖️ Compliance / legal / regulatory | `GC-Legal` | + CISO if data involved |
| 🚀 GTM / launch / positioning | `CRO-GTM` | + CFO if pricing |
| 📈 Stock / portfolio / investment | `CIO-Investments` | → CFO |
| 🗄️ Data pipeline / BI / analytics | `CDO-Data` | + CISO if sensitive |
| ☁️ Cloud / CI/CD / DevOps | `CPlatO-DevOps` | + CISO for IAM/secrets |
| 🤖 AI / ML / agents / RAG / LLMs | `CAIO-AI` | → AI & Automation Council |
| ✍️ Prompt design / improvement | `CPrO-Prompting` | CEO prompts → `User-Prompt-Optimizer` first |
| 🎨 UX / design / CX | `CCO-Design` | + CPO for product UX |
| 🧭 Strategy / competitive / OKRs | `CSO-Strategy` | |
| 🌐 Browser / web automation / MCP | `Dir-BrowserOps` / `Dir-MCPHub` | Read-only default |
| 🏢 Multi-dept directive | **`COO` first** | COO decomposes → routes |
| 📝 Simple / Tier 0 | `Local-Model-Router` | Saves Claude API tokens |
| 🔧 Multi-file code task | `orchestrator` pipeline | scout → architect → builder → validator |
| 💬 Improve CEO's prompt | `User-Prompt-Optimizer` | Then route result |

---

## 🚦 Risk Tier Quick Reference

| Tier | Signal | Criteria | Action |
|------|--------|----------|--------|
| 🟢 **0** | Auto-proceed | Internal, reversible, no financial/legal impact | No governance overhead |
| 🟡 **1** | Standard | Internal process, limited data risk | Normal workflow |
| 🟠 **2** | ⚠️ PAUSE | Customer-facing, compliance-adjacent, AI write to prod | CEO/exec approval required |
| 🔴 **3** | 🛑 STOP | Cross-domain, existential, unclear owner | Escalate to CEO immediately |

> Full criteria: [`CLAUDE.md` → Risk Tier System](./CLAUDE.md)

---

## 🤖 Agent Quick Reference

### 🔧 Technical Pipeline
| Agent | Invoke When |
|-------|-------------|
| [`orchestrator`](./agents/orchestrator.md) | Multi-file task, new feature, any non-trivial implementation |
| [`scout`](./agents/scout.md) | Before editing any file not read this session |
| [`architect`](./agents/architect.md) | Scout done → need a plan |
| [`builder`](./agents/builder.md) | Architect has a plan → execute |
| [`validator`](./agents/validator.md) | Builder finished → verify before marking done |
| [`boost`](./agents/boost.md) | Stuck, looping, no progress |
| [`Semantic-Router`](./agents/pipeline/Semantic-Router.md) | Domain unclear, no keyword match, intent is implicit or cross-domain |

### 👔 C-Suite Agents
| Agent | Domain |
|-------|--------|
| [`COO`](./agents/COO.md) | Operations — breaks directives into dept tasks |
| [`CISO`](./agents/CISO.md) | Security — threat models, permission changes, all reviews |
| [`CTO-Engineering`](./agents/CTO-Engineering.md) | Engineering — code, architecture, technical strategy |
| [`CPO`](./agents/CPO.md) | Product — requirements, specs, roadmap |
| [`CFO`](./agents/CFO.md) | Finance — cost, budget, financial risk |
| [`GC-Legal`](./agents/GC-Legal.md) | Legal / GRC — compliance, regulatory, privacy |
| [`CRO-GTM`](./agents/CRO-GTM.md) | Revenue — sales, marketing, GTM, customer |
| [`CAE-Audit`](./agents/CAE-Audit.md) | Internal Audit — independent assurance (Tier 2+ only) |
| [`CIO-Investments`](./agents/CIO-Investments.md) | Trading & investment |
| [`CDO-Data`](./agents/CDO-Data.md) | Data — pipelines, analytics, BI, ML data |
| [`CPlatO-DevOps`](./agents/CPlatO-DevOps.md) | Platform — cloud, CI/CD, SRE, containers |
| [`CAIO-AI`](./agents/CAIO-AI.md) | AI/ML — models, RAG, agents, LLMs, AI safety |
| [`CCO-Design`](./agents/CCO-Design.md) | Customer Experience — UX, design, support |
| [`CSO-Strategy`](./agents/CSO-Strategy.md) | Strategy — competitive intelligence, OKRs, planning |
| [`CPrO-Prompting`](./agents/CPrO-Prompting.md) | Prompt Engineering — all agent prompts |
| [`CIRO-Research`](./agents/CIRO-Research.md) | Research & Innovation |

### 🏛️ Governance Councils
| Council | Scope | Verdict Format |
|---------|-------|----------------|
| [`AI-Automation-Council`](./agents/AI-Automation-Council.md) | AI use cases, new agent tool access, Tier 2+ AI workflows | CLEARED / CONDITIONAL / BLOCKED |
| [`GRC-Council`](./agents/GRC-Council.md) | Non-AI enterprise risk, policy exceptions, cross-domain compliance | CLEARED / CONDITIONAL / BLOCKED |

### 🌐 Browser & MCP Platform
| Agent | Role |
|-------|------|
| [`Dir-BrowserOps`](./agents/Dir-BrowserOps.md) | Browser/vision agent ops — Playwright MCP, domain allowlist, audit logging |
| [`Dir-MCPHub`](./agents/Dir-MCPHub.md) | MCP hub infrastructure — MetaMCP, namespaces, tool ACLs |

---

## 🏛️ Governance Quick Reference

| I need to... | Go to |
|--------------|-------|
| Log a change | [`CHANGELOG.md`](./CHANGELOG.md) → format in [`CHANGE_MANAGEMENT.md`](./CHANGE_MANAGEMENT.md) |
| Understand the change process | [`CHANGE_MANAGEMENT.md`](./CHANGE_MANAGEMENT.md) |
| Check if CEO approval is needed | [`CHANGE_MANAGEMENT.md`](./CHANGE_MANAGEMENT.md) § Structural vs Minor |
| Verify Five-File Rule | [`CLAUDE.md`](./CLAUDE.md) § Five-File Rule |
| Check open audit findings | [`AUDIT_FINDINGS.md`](./AUDIT_FINDINGS.md) § Open Findings |
| Write or audit an agent file | [`AGENT_STANDARDS.md`](./AGENT_STANDARDS.md) |
| Check data handling rules | [`DATA_CLASSIFICATION.md`](./DATA_CLASSIFICATION.md) |
| See version history | [`CLAUDE.md`](./CLAUDE.md) § Version History |
| Check department workflow | [`DEPARTMENT_WORKFLOWS.md`](./DEPARTMENT_WORKFLOWS.md) |
| Get AI use case approved | [`AI-Automation-Council`](./agents/AI-Automation-Council.md) |
| Escalate cross-domain risk | [`GRC-Council`](./agents/GRC-Council.md) |

---

## ✅ Five-File Rule Checklist

Every structural agent change must update all five before it's complete:

- [ ] The **agent file** itself
- [ ] The **parent agent** (`Manages:` / `Reports to:` updated if scope changed)
- [ ] [`CLAUDE.md`](./CLAUDE.md) — agent table, routing, version history
- [ ] [`CHANGELOG.md`](./CHANGELOG.md) — entry per [`CHANGE_MANAGEMENT.md`](./CHANGE_MANAGEMENT.md) format
- [ ] [`SYSTEM_MAP.md`](./SYSTEM_MAP.md) — diagrams updated

> Missing any = incomplete. [`CAE-Audit`](./agents/CAE-Audit.md) will flag it.

---

## 🏗️ Authority Hierarchy

```
👤 CEO  (human — final authority on everything)
  └── 📜 CLAUDE.md  (master policy — all other docs defer to this)
        ├── 📍 INDEX.md            navigation hub
        ├── 🔄 CHANGE_MANAGEMENT   change process policy
        ├── 📐 AGENT_STANDARDS     agent quality standard
        ├── ⚙️  DEPARTMENT_WORKFLOWS operational workflows
        ├── 🔒 DATA_CLASSIFICATION  data security policy
        ├── 🗺️  SYSTEM_MAP          visual reference (no policy)
        ├── 🏢 ORG_CHARTS          visual reference (no policy)
        ├── 🔍 AUDIT_FINDINGS      audit log
        └── 📋 CHANGELOG           audit trail (no policy)

🤖 agents/*.md  →  authority from CLAUDE.md + AGENT_STANDARDS.md
   Conflict with CLAUDE.md?  →  CLAUDE.md wins.
```

---

## 📊 System Status

| Metric | Value |
|--------|-------|
| Total agents | 135 |
| Departments | 15 |
| Governance councils | 2 |
| Technical pipeline agents | 6 |
| Compliance frameworks | 6 (COSO · SOC 2 · NIST CSF · SOX · COBIT · CIS) |
| MCP servers active | 2 (Playwright · Filesystem) |
| Current version | 1.8.7 |
| Open audit findings | 0 |

---

## 📋 Version History

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-03-20 | Created. Document map, routing reference, risk tier reference, agent reference, governance reference, authority hierarchy. |
| 1.1.0 | 2026-03-20 | Full visual rewrite. Hyperlinks to all docs and agent files. Emoji section hierarchy. System status dashboard. Governance councils section. Browser/MCP platform section added. Agent count updated to 135. |
