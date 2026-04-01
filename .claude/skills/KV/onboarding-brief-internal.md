# Welcome to the Company
### An Onboarding Brief for New Arrivals

---

## What This System Actually Is

This is a personal AI operating system. That phrase gets thrown around a lot, so here is what it means in practice:

One human — the CEO — runs a company of 175 AI agents organized into 15 departments. The CEO says what needs to happen. The system figures out who does it, in what order, with what level of oversight. The CEO makes decisions. The system makes everything else.

The purpose is not to have a lot of agents. The purpose is to turn time into leveraged results. To turn confusion into clarity. To turn "I need to figure out how to do this" into "this is done, here is the output, what next?"

That is the whole thing. Everything below is how it works.

---

## The Chain of Command

```
CEO (the only human)
  |
Lead Orchestrator (Claude — sits above all agents)
  |
COO (breaks multi-department directives into tasks)
  |
C-Suite Agents (one per department — 15+)
  |
Department Chains (VP → Director → Manager → IC)
  |
Sub-agents (0-5 per worker, ephemeral)
```

**The CEO** sets direction and makes all final decisions. Their word is final. There is no appeal.

**The Lead Orchestrator** receives every CEO input and decides who handles it. It does not do the work itself unless no agent is appropriate. It is the router, the quality gate, and the escalation surface.

**The COO** is invoked when a task spans more than one department. The Lead Orchestrator does not route directly to multiple departments — the COO decomposes the work first.

**C-Suite agents** are the entry points for each domain. They spawn their department chains and delegate downward. Results flow back up.

---

## The Departments

You do not need to memorize all of them. You need to know they exist and roughly what they cover.

| Department | Lead | What They Handle |
|-----------|------|-----------------|
| Engineering | CTO-Engineering | Code, builds, technical implementation |
| Product | CPO | Requirements, specs, translating ideas into plans |
| Security | CISO | Threat models, risk assessments, security reviews |
| Finance | CFO | Cost assessment, financial risk, resource tracking |
| Investments | CIO-Investments | Portfolio analysis, equity research, market intelligence |
| Data & Analytics | CDO-Data | Pipelines, dashboards, data quality, ML data prep |
| DevOps & Platform | CPlatO-DevOps | Cloud infra, CI/CD, containers, SRE |
| AI & ML | CAIO-AI | Model research, RAG, agent development, AI safety |
| Strategy | CSO-Strategy | Competitive intelligence, OKRs, scenario modeling |
| GTM & Revenue | CRO-GTM | Positioning, sales, marketing, customer-facing work |
| HR & People | CHRO | Hiring, culture, performance, compensation |
| Legal & GRC | GC-Legal | Compliance, regulatory risk, privacy |
| Research & Innovation | CIRO-Research | Technology scouting, research synthesis |
| Prompt Engineering | CPrO-Prompting | Building and auditing all agent prompts |
| Gaming Intelligence | Dir-Gaming | Patch notes, meta coaching, game research |
| KV Marketing | So-It-Goes (CMO) | Brand, content, positioning — Vonnegut voice |
| Communications | VP-Communications | PR, internal comms, brand messaging |
| PMO | VP-PMO | Program management, delivery coordination |
| Internal Audit | CAE-Audit | Independent assurance — does not report to anyone it audits |

---

## The Technical Pipeline

When code needs to be written or changed, a dedicated pipeline handles it:

1. **Orchestrator** — coordinates the full sequence
2. **Scout** — reads and understands existing code before anyone touches it
3. **Architect** — produces a plan based on what Scout found
4. **Builder** — executes the plan
5. **Validator** — checks the output before it ships

The rule is simple: scout before you touch. Never edit a file you have not read. The pipeline enforces this.

Two additional pipeline agents:
- **MasterPlanner** — produces a plan and stops, waiting for CEO confirmation before any large-scale execution begins
- **Boost** — intervenes when a task is stuck, a file has been edited too many times, or the CEO sounds frustrated

---

## The Governance Bodies

Two councils sit above the departments. They are not departments. They are decision gates.

**AI & Automation Council** — Reviews and approves AI agent use cases, risk tiers, and guardrails. If an agent is getting write access to production, or a new AI workflow is being deployed, this council must approve it first. Members: CAIO-AI, CISO, CDO-Data, GC-Legal, CAE-Audit, CPO, CRO-GTM.

**GRC Council** — Handles non-AI enterprise risk. Policy exceptions, regulatory changes, cross-domain compliance decisions. Members: GC-Legal, CISO, CCO-Compliance, CFO, CAE-Audit.

These councils are blocking gates. "Noted but not invoked" is a governance failure. If a task triggers a council, the council runs before the work begins.

---

## How Routing Works

Every input from the CEO goes through a four-step process:

### Step 1 — Domain Classification
The system scans for keywords and, if those are ambiguous, reasons about what the CEO is actually trying to accomplish. "Build me a dashboard" goes to Engineering. "Why is this metric off" goes to Data. "Is this safe" goes to Security.

### Step 2 — Risk Tier
Every task gets a risk classification:
- **Tier 0** — Trivial. Local model handles it. No oversight needed.
- **Tier 1** — Standard. Internal impact. Periodic reporting to audit.
- **Tier 2** — Material. Customer-facing, compliance-adjacent, or financially significant. Requires formal security review and may require audit.
- **Tier 3** — Stop everything. Cross-domain, unclear ownership, potentially existential. Escalate to CEO immediately.

### Step 3 — Route
Based on domain and tier, the system routes to the right department chain with the right governance gates active.

### Step 4 — Master Plan
If the task is large (multi-department, multi-file, Tier 2+, or involves a formal deliverable), the MasterPlanner produces a structured plan and waits. No execution until the CEO confirms.

---

## The Compliance Frameworks

Six frameworks govern the system. Here is what each one actually means in practice:

- **COSO** — Internal controls work. Duties are separated. Nobody audits themselves.
- **SOC 2** — Data is handled securely. Confidentiality, integrity, and availability are maintained.
- **NIST CSF** — The system can identify threats, protect against them, detect when they happen, respond, and recover.
- **SOX** — Every decision has an audit trail. Financial integrity is non-negotiable.
- **COBIT** — IT governance is aligned to what the business actually needs, not what is technically interesting.
- **CIS** — Least privilege. Secure defaults. Nothing is exposed that does not need to be.

You do not need to memorize these. You need to know they exist, that every agent inherits them, and that the audit function checks compliance.

---

## Key Infrastructure

The system runs on real Python code, not just prompts:

- **chain.py** — executes multi-agent chains following routing logic
- **run.py** — main routing loop with automatic changelog generation
- **vector_router.py** — finds the right agent semantically, backed by ChromaDB
- **prompt_cache.py** — caches prompts to reduce cost (10x cheaper with API breakpoints)
- **model_router.py** — selects the right model tier for each task
- **custodian.py** — maintenance CLI for prompt hygiene, cache, and memory health

---

## Where to Start When You Do Not Know What to Do

1. **Read CLAUDE.md.** It is the master policy register. Everything lives there or is referenced from there.
2. **Read INDEX.md.** It is the fast-lookup navigation hub. Document map, routing reference, agent reference, all in one place.
3. **Ask the Lead Orchestrator.** That is what it is for. Describe what you need. It will route you to the right place.

Do not try to understand all 175 agents. Understand the structure: CEO at the top, Lead Orchestrator routing everything, COO decomposing multi-department work, C-suite leads owning their domains, and the pipeline handling code.

The rest you will learn by doing the work.

Welcome aboard.
