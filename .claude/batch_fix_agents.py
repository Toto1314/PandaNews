#!/usr/bin/env python3
"""
batch_fix_agents.py — Fix all agents failing md_parser validate.

Adds missing sections (Escalation Rules, Mandatory Trigger Rules, Role in One Sentence)
to non-compliant agent files based on their department path and role level.
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from md_parser import MarkdownParser, _validate_agent  # noqa: E402

AGENTS_DIR = Path(__file__).parent / "agents"

# ── Department → parent chain ──────────────────────────────────────────────

DEPT_CSUITE = {
    "audit":      "CAE-Audit",
    "ai-ml":      "CAIO-AI",
    "data":       "CDO-Data",
    "design":     "CCO-Design",
    "devops":     "CPlatO-DevOps",
    "engineering":"CTO-Engineering",
    "finance":    "CFO",
    "gaming":     "Dir-Gaming",
    "governance": "Lead Orchestrator",
    "gtm":        "CRO-GTM",
    "investments":"CIO-Investments",
    "legal":      "GC-Legal",
    "pipeline":   "Lead Orchestrator",
    "product":    "CPO",
    "prompt-eng": "CPrO-Prompting",
    "research":   "CIRO-Research",
    "security":   "CISO",
    "strategy":   "CSO-Strategy",
    "c-suite":    "CEO / Lead Orchestrator",
}

DEPT_VP = {
    "audit":      "Dir-Internal-Audit",
    "ai-ml":      "VP-AI-Engineering",
    "data":       "VP-Data",
    "design":     "VP-Customer-Experience",
    "devops":     "VP-Platform-Engineering",
    "engineering":"VP-Engineering",
    "finance":    "VP-Finance",
    "gaming":     "Dir-Gaming",
    "governance": "Lead Orchestrator",
    "gtm":        "VP-Sales",
    "investments":"VP-Investments",
    "legal":      "VP-Legal-Risk",
    "pipeline":   "Lead Orchestrator",
    "product":    "VP-Product",
    "prompt-eng": "VP-PromptEngineering",
    "research":   "VP-Research",
    "security":   "VP-Security",
    "strategy":   "VP-Strategy",
    "c-suite":    "CEO",
}

# ── Level detection ────────────────────────────────────────────────────────

def agent_level(name: str) -> str:
    n = name.lower()
    if n.startswith("vp-"):               return "vp"
    if n.startswith("dir-"):              return "director"
    if n.startswith("head-"):             return "director"
    if n.startswith("principal-"):        return "principal"
    if n.startswith("sr-"):               return "senior"
    if "manager" in n:                    return "manager"
    if n in ("cae-audit", "caio-ai", "cfo", "cpo", "cro-gtm", "gc-legal",
             "ciso", "coo", "cto-engineering", "cdo-data", "ccо-design",
             "cso-strategy", "cpro-prompting", "ciro-research", "cio-investments",
             "cplo-devops", "cplatо-devops"):
        return "csuite"
    return "ic"

# ── Content generators ─────────────────────────────────────────────────────

def gen_escalation_rules(name: str, dept: str) -> str:
    level = agent_level(name)
    csuite = DEPT_CSUITE.get(dept, "Lead Orchestrator")
    vp     = DEPT_VP.get(dept, csuite)

    if level == "vp":
        boss = csuite
        lines = [
            f"**Escalate to {boss} immediately if:**",
            "- A decision impacts cross-departmental strategy or resources",
            "- Budget authorization is required beyond defined limits",
            "- A Tier 2+ risk requires C-suite sign-off",
            "- A strategic direction conflicts with current OKRs",
            "- A security or compliance risk is identified → CISO + GRC Council involvement required",
            "- A team blocker cannot be resolved within 24 hours",
        ]
    elif level in ("director", "head"):
        boss = vp if vp != csuite else csuite
        lines = [
            f"**Escalate to {boss} immediately if:**",
            "- A decision requires cross-department coordination",
            "- Budget or headcount impact is involved",
            "- A Tier 2+ risk is identified — CISO review required before proceeding",
            "- A team blocker cannot be resolved within 24 hours",
            "- A regulatory or compliance issue surfaces",
            "- Scope of work expands beyond the original directive",
        ]
    elif level == "principal":
        lines = [
            f"1. Architectural decision with cross-team impact → escalate to {vp} before finalizing",
            f"2. Security or compliance concern identified → escalate to CISO before continuing",
            f"3. Conflicting technical standards across teams → escalate to {vp} to resolve",
            f"4. External dependency or third-party tool required → escalate to {csuite} for approval",
            f"5. Work cannot be completed within current constraints → escalate to {vp} immediately",
        ]
    elif level == "senior":
        lines = [
            f"1. Blocked for more than 30 minutes → escalate to {vp}",
            "2. Task scope appears broader than defined → stop and confirm before continuing",
            "3. Security or compliance concern identified → escalate to CISO before taking action",
            f"4. External data, API, or third-party access required → escalate to {csuite} for approval",
            f"5. Conflicting instructions from multiple stakeholders → escalate to {vp} to resolve priority",
        ]
    elif level == "manager":
        lines = [
            f"1. Team blocker unresolved after 24 hours → escalate to {vp}",
            "2. Scope or priority conflict between stakeholders → escalate to resolve before work continues",
            f"3. Tier 2+ risk identified → escalate to {csuite} + CISO before proceeding",
            f"4. Budget or headcount impact → escalate to {csuite} for approval",
            "5. Compliance or regulatory concern → escalate to GC-Legal immediately",
        ]
    else:  # ic / specialist
        lines = [
            f"1. Blocked for more than 30 minutes → escalate to direct manager immediately",
            "2. Task scope appears broader than defined → stop and confirm with manager before continuing",
            "3. Any security or compliance concern → escalate to CISO before taking action",
            f"4. External data, API, or third-party access required → escalate to {csuite} for approval",
            "5. Conflicting instructions from multiple stakeholders → escalate to manager to resolve",
        ]

    body = "\n".join(lines)
    return f"## Escalation Rules\n\n{body}\n\n---"


# ── C-suite Mandatory Trigger Rules ───────────────────────────────────────

MANDATORY_TRIGGERS = {
    "CAE-Audit": """\
## Mandatory Trigger Rules

**CAE-Audit MUST be invoked when:**
- A Tier 2 or Tier 3 task is completing and requires independent assurance
- A new control design is being implemented and needs effectiveness review
- A cross-department compliance gap is identified with no clear owner
- A significant audit finding requires escalation to the CEO
- The quarterly compliance review cycle is triggered
- Any agent action touches SOX-regulated financial data or processes

**CAE-Audit is NOT invoked for:**
- Tier 0–1 tasks — these are informed via periodic reporting only
- Routine code changes that do not affect controls or compliance
- Single-department operational decisions within defined guardrails

---""",

    "CAIO-AI": """\
## Mandatory Trigger Rules

**CAIO-AI MUST be invoked when:**
- A new AI model is being evaluated for production deployment
- An AI agent is being granted new tool access or production write permissions
- An LLM pipeline change affects customer-facing outputs
- A RAG architecture or embedding system is being designed or modified
- AI safety review is required for a new agent workflow
- Fine-tuning, model training, or a new foundation model is being initiated

**CAIO-AI is NOT invoked for:**
- Prompt improvements that do not change agent scope or tool access
- Standard model inference calls within already-approved workflows
- Research-only AI evaluations with no deployment decision pending

---""",

    "CFO": """\
## Mandatory Trigger Rules

**CFO MUST be invoked when:**
- Any task has material financial cost or resource implications
- A high-cost or high-resource task is being initiated — flag to CEO before execution
- Financial reporting integrity is at risk
- SOX control testing is required
- Budget allocation decisions affect multiple departments
- An external financial commitment or contract is being made

**CFO is NOT invoked for:**
- Tier 0 internal tasks with no financial impact
- Research and analysis tasks with no execution cost
- Engineering tasks within pre-approved infrastructure budgets

---""",

    "CPO": """\
## Mandatory Trigger Rules

**CPO MUST be invoked when:**
- A new feature or product capability is being designed or scoped
- Engineering is about to begin work on any non-trivial feature
- Scope conflicts exist between competing product priorities
- A product spec requires sign-off before engineering starts
- Acceptance criteria need to be defined for a deliverable
- A customer-facing change requires product review before shipping

**CPO is NOT invoked for:**
- Bug fixes with no user-facing behavioral changes
- Internal tooling changes that do not affect product behavior
- Infrastructure and platform changes with no product surface impact

---""",

    "CRO-GTM": """\
## Mandatory Trigger Rules

**CRO-GTM MUST be invoked when:**
- A customer-facing message, demo, or pitch is being prepared
- GTM strategy for a new feature or product is being defined
- Sales positioning or competitive messaging is needed
- A customer deal requires technical output translated to business value
- Revenue-impacting decisions require GTM alignment
- External communications need GTM review before delivery

**CRO-GTM is NOT invoked for:**
- Internal engineering or architecture decisions
- Compliance or security reviews
- Data pipeline and analytics work with no customer-facing output

---""",

    "GC-Legal": """\
## Mandatory Trigger Rules

**GC-Legal MUST be invoked when:**
- A new open-source library or framework is being adopted for deployment
- Data privacy implications are present in a new feature or workflow
- A regulatory compliance question arises (GDPR, HIPAA, SOX, PCI, CCPA)
- A contract or external agreement is being reviewed or signed
- A policy exception is being requested by any department
- Legal risk in a marketing claim, product disclosure, or customer communication is identified

**GC-Legal is NOT invoked for:**
- Internal technical decisions with no legal or compliance surface
- Tier 0 tasks with no regulatory, privacy, or contractual implications
- Security reviews — those route directly to CISO

---""",

    "AI-Automation-Council": """\
## Mandatory Trigger Rules

**AI & Automation Council MUST be convened when:**
- A new AI agent is being granted write access to production systems
- A new AI model is being deployed to a customer-facing workflow
- A Tier 2+ AI workflow is being approved for execution
- Prompt policies for customer-facing AI systems are being changed
- A new autonomous agent use case is being scoped and requires risk tier assignment
- An AI governance gap is identified with no clear department owner

**Council is NOT convened for:**
- Tier 0–1 internal AI experiments with no production deployment path
- Prompt improvements within already-approved agent scopes
- Research-only AI evaluations with no deployment decision pending

---""",

    "CCO-Design": """\
## Mandatory Trigger Rules

**CCO-Design MUST be invoked when:**
- A new user-facing feature requires UX or design review before shipping
- A customer journey is being redesigned or a new onboarding flow is created
- NPS or CSAT data indicates a CX problem requiring cross-functional response
- Accessibility review is required for a product or feature
- A design system change affects multiple product surfaces
- Customer support escalations reveal a systemic experience failure

**CCO-Design is NOT invoked for:**
- Internal tooling with no customer-facing surface
- Backend infrastructure changes with no UX impact
- Marketing asset creation handled entirely within GTM

---""",

    "CDO-Data": """\
## Mandatory Trigger Rules

**CDO-Data MUST be invoked when:**
- A new data pipeline, warehouse, or lakehouse component is being designed
- A new ML model requires data prep, feature engineering, or training data
- A BI dashboard or metric definition affects business decision-making
- Data governance, lineage, or quality standards are being defined
- Sensitive or regulated data is being ingested, stored, or processed
- A data contract between producing and consuming teams is being established

**CDO-Data is NOT invoked for:**
- Single-query ad hoc analyses with no pipeline or model involved
- Application-level caching or session storage decisions
- Security reviews — those route to CISO

---""",

    "CIO-Investments": """\
## Mandatory Trigger Rules

**CIO-Investments MUST be invoked when:**
- A portfolio review, rebalancing decision, or new position is being evaluated
- A macroeconomic or sector development requires investment thesis reassessment
- A new equity, ETF, or asset class is being researched for potential addition
- Risk metrics (VaR, CVaR, drawdown) breach defined thresholds
- A significant market event requires portfolio stress-testing
- Treasury or cash management decisions have investment implications

**CIO-Investments is NOT invoked for:**
- General market news consumption with no portfolio action implied
- Financial reporting or SOX compliance tasks — those route to CFO
- Corporate strategy decisions unrelated to capital allocation

---""",

    "CIRO-Research": """\
## Mandatory Trigger Rules

**CIRO-Research MUST be invoked when:**
- A new technology, framework, or AI capability requires scouting or evaluation
- An emerging trend requires synthesis before a strategic or product decision
- A scientific or academic research synthesis is needed to inform a team decision
- A competitive intelligence gap is identified that requires research to close
- An innovation sprint or proof-of-concept requires research-backed framing
- Any department needs external intelligence before beginning implementation

**CIRO-Research is NOT invoked for:**
- Implementation tasks with no research or scouting component
- Compliance framework analysis — that routes to GC-Legal or CCO
- Internal data analysis tasks — those route to CDO-Data

---""",

    "CPlatO-DevOps": """\
## Mandatory Trigger Rules

**CPlatO-DevOps MUST be invoked when:**
- A new cloud infrastructure component is being provisioned or modified
- A CI/CD pipeline is being created, changed, or retired
- A containerization, orchestration, or deployment automation decision is needed
- SRE reliability targets (SLOs, error budgets) are being defined or reviewed
- A new environment (staging, production, DR) is being set up
- Infrastructure-as-code changes affect production systems

**CPlatO-DevOps is NOT invoked for:**
- Application-level code changes with no infrastructure surface impact
- Security architecture reviews — those route to CISO
- Data pipeline decisions — those route to CDO-Data

---""",

    "CPrO-Prompting": """\
## Mandatory Trigger Rules

**CPrO-Prompting MUST be invoked when:**
- A new agent prompt is being written or significantly revised
- An existing agent is producing consistently poor output and needs prompt repair
- A prompt policy for a customer-facing AI system is being changed
- A new prompting technique or framework is being adopted across the OS
- A prompt quality audit is required for a department's agents
- The AI & Automation Council requires prompt governance input

**CPrO-Prompting is NOT invoked for:**
- Minor wording tweaks to prompts that don't change behavior or scope
- Model selection decisions — those route to CAIO-AI
- Agent architecture decisions — those route to CTO-Engineering

---""",

    "CSO-Strategy": """\
## Mandatory Trigger Rules

**CSO-Strategy MUST be invoked when:**
- A new market opportunity or competitive threat requires strategic analysis
- OKRs are being developed, reviewed, or revised for the company or a department
- A build vs. buy vs. partner decision requires strategic framing
- M&A research, partnership evaluation, or new market entry is being scoped
- Scenario planning or long-range strategic modeling is needed
- A major product or business model decision requires competitive context

**CSO-Strategy is NOT invoked for:**
- Tactical execution decisions within an already-defined strategy
- Financial modeling without strategic framing — that routes to CFO
- Market research tasks with no strategic output — those route to CIRO-Research

---""",

    "CTO-Engineering": """\
## Mandatory Trigger Rules

**CTO-Engineering MUST be invoked when:**
- A new system architecture decision is being made
- A build vs. buy decision for a major technical component is needed
- Cross-team technical standards, ADRs, or RFCs are being defined
- Engineering org health, capacity, or technical debt strategy requires executive input
- A new technology or framework is being adopted at the platform level
- An engineering decision has material security, compliance, or cost implications

**CTO-Engineering is NOT invoked for:**
- Routine feature implementation within an approved spec — that routes to engineering team
- Infrastructure provisioning — that routes to CPlatO-DevOps
- Prompt engineering or AI model decisions — those route to CAIO-AI

---""",

    "GRC-Council": """\
## Mandatory Trigger Rules

**GRC Council MUST be convened when:**
- A compliance framework changes and cross-domain impact assessment is needed
- A policy exception is requested that spans more than one department
- A cross-domain legal/risk issue has no single department owner
- A Tier 3 escalation requires multi-domain governance review
- A regulatory change creates conflicting obligations across COSO, SOC 2, NIST, SOX, COBIT, or CIS

**Council is NOT convened for:**
- Single-domain compliance questions — route to the relevant department owner
- AI-specific governance decisions — those route to the AI & Automation Council
- Tier 0–1 operational decisions within established control frameworks

---""",
}

ROLE_IN_ONE_SENTENCE = {
    "Chief-Compliance-Officer": "The Chief Compliance Officer owns the enterprise compliance program across all 6 frameworks and issues CLEARED, CONDITIONAL, or BLOCKED verdicts on any action with regulatory implications.",
}

# ── File editing ───────────────────────────────────────────────────────────

def insert_before_heading(content: str, target_heading: str, new_section: str) -> str:
    """Insert new_section immediately before the first REAL heading matching target_heading.
    Skips lines inside fenced code blocks (``` or ~~~)."""
    lines = content.splitlines()
    in_fence = False
    fence_char = ""
    target_lower = target_heading.lower()

    for i, line in enumerate(lines):
        # Track fenced code blocks
        stripped_line = line.strip()
        if not in_fence and (stripped_line.startswith("```") or stripped_line.startswith("~~~")):
            in_fence = True
            fence_char = stripped_line[:3]
            continue
        if in_fence and stripped_line.startswith(fence_char):
            in_fence = False
            continue
        if in_fence:
            continue

        # Only match real headings (lines starting with #)
        if not line.startswith("#"):
            continue
        heading_text = line.lstrip("#").strip().lower()
        if heading_text.startswith(target_lower):
            lines.insert(i, "")
            lines.insert(i, new_section)
            return "\n".join(lines)

    # Fallback: insert before VERSION HISTORY
    in_fence = False
    for i, line in enumerate(lines):
        stripped_line = line.strip()
        if not in_fence and (stripped_line.startswith("```") or stripped_line.startswith("~~~")):
            in_fence = True
            fence_char = stripped_line[:3]
            continue
        if in_fence and stripped_line.startswith(fence_char):
            in_fence = False
            continue
        if in_fence:
            continue
        if line.startswith("#") and "version history" in line.lower():
            lines.insert(i, "")
            lines.insert(i, new_section)
            return "\n".join(lines)

    return content + "\n\n" + new_section + "\n"


def insert_after_heading(content: str, after_heading: str, new_section: str) -> str:
    """Insert new_section after the section body of after_heading."""
    lines = content.splitlines()
    found = False
    for i, line in enumerate(lines):
        stripped = line.strip().lstrip("#").strip().lower()
        if stripped.startswith(after_heading.lower()):
            found = True
            # find end of this section (next ## heading or end of file)
            j = i + 1
            while j < len(lines):
                if lines[j].startswith("##") or lines[j].startswith("# "):
                    break
                j += 1
            lines.insert(j, "")
            lines.insert(j, new_section)
            return "\n".join(lines)
    if not found:
        # insert after frontmatter
        in_fm = False
        fm_end = 0
        for i, line in enumerate(lines):
            if i == 0 and line.strip() == "---":
                in_fm = True
                continue
            if in_fm and line.strip() == "---":
                fm_end = i + 1
                break
        lines.insert(fm_end + 1, "")
        lines.insert(fm_end + 1, new_section)
        return "\n".join(lines)
    return content


# ── Main ──────────────────────────────────────────────────────────────────

def fix_agent(path: Path, findings: list[str], mp: MarkdownParser) -> bool:
    doc = mp.parse_file(path)
    content = path.read_text(encoding="utf-8", errors="replace")
    dept = path.parent.name
    name = doc.frontmatter.get("name", path.stem)
    changed = False

    for finding in findings:
        if "Missing required section: Escalation Rules" in finding:
            section = gen_escalation_rules(name, dept)
            content = insert_before_heading(content, "Output Format", section)
            changed = True

        elif "Missing required section: Negative Constraints" in finding:
            section = "## Negative Constraints\n\nThis agent must NEVER:\n- Act outside its defined scope without explicit CEO approval\n- Bypass governance gates or skip required review steps\n- Take irreversible actions without confirming scope with the accountable executive\n\n---"
            content = insert_before_heading(content, "Escalation Rules", section)
            changed = True

        elif "Missing C-suite section: Mandatory Trigger Rules" in finding:
            trigger_content = MANDATORY_TRIGGERS.get(name)
            if trigger_content:
                content = insert_after_heading(content, "Role in One Sentence", trigger_content)
                changed = True

        elif "Missing C-suite section: Role in One Sentence" in finding:
            sentence = ROLE_IN_ONE_SENTENCE.get(name, f"{name} is the primary agent for this domain — invoke when the task requires its specific expertise.")
            section = f"## Role in One Sentence\n\n{sentence}\n\n---"
            content = insert_after_heading(content, "Negative Constraints", section)
            changed = True

    if changed:
        path.write_text(content, encoding="utf-8")
    return changed


def main():
    mp = MarkdownParser()
    files = sorted(AGENTS_DIR.rglob("*.md"))

    fixed = skipped = already_ok = 0
    for f in files:
        doc = mp.parse_file(f)
        if not doc.frontmatter:
            continue
        findings = _validate_agent(doc)
        if not findings:
            already_ok += 1
            continue
        ok = fix_agent(f, findings, mp)
        if ok:
            fixed += 1
            print(f"  FIXED  {f.name}")
        else:
            skipped += 1
            print(f"  SKIP   {f.name}  (no handler for: {findings})")

    print(f"\n{fixed} fixed | {already_ok} already passing | {skipped} skipped")


if __name__ == "__main__":
    main()
