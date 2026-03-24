# AI OS — Change Management Policy
**Version:** 1.0 | **Owner:** CAE-Audit | **Approved By:** CEO
**COSO Components:** Control Activities · Information & Communication · Monitoring Activities

> **Navigation:** `INDEX.md` — fast lookup | `CLAUDE.md` — master register (routing, org chart, operating rules) | `CHANGELOG.md` — the audit trail you write to after every change | `AUDIT_FINDINGS.md` — findings that drive changes through this policy

---

## PURPOSE

This document governs how changes to the AI Operating System are initiated, documented, propagated, and audited. Every agent creation, update, or removal is a **control event** that must leave a complete audit trail.

No change is complete until:
1. A changelog entry is written in `CHANGELOG.md`
2. The parent agent is updated (if the change affects their scope)
3. `CLAUDE.md` is updated (agent table, routing logic, or version history — as applicable)

---

## CHANGE TYPES

| Type | Description | Required Actions |
|------|-------------|-----------------|
| **AGENT-CREATE** | New agent file created | CHANGELOG entry + CLAUDE.md agent table + parent agent "Manages" section |
| **AGENT-UPDATE** | Existing agent file modified | CHANGELOG entry + CLAUDE.md version bump (if structural) + parent notified if scope changes |
| **AGENT-DEPRECATE** | Agent removed or archived | CHANGELOG entry + CLAUDE.md agent table removal + parent "Manages" updated + archive note |
| **DEPT-CREATE** | New department or chain created | CHANGELOG entry + CLAUDE.md department chain + routing logic + all parent agents updated |
| **DEPT-UPDATE** | Department scope, chain, or ownership changed | CHANGELOG entry + CLAUDE.md routing update + affected parent agents |
| **POLICY-UPDATE** | CLAUDE.md rules, routing, or frameworks changed | CHANGELOG entry + version bump |
| **TOOL-GRANT** | New tool added to an agent | CHANGELOG entry + CISO review required if sensitive tool |
| **TOOL-REVOKE** | Tool removed from an agent | CHANGELOG entry |
| **DATA-CLASS-CHANGE** | Data classification policy updated | CHANGELOG entry + CAE-Audit sign-off + CEO approval |

---

## PROPAGATION RULES

When a change is made, the following must cascade **before the change is considered complete:**

### Agent Created
```
1. Write agent file to /agents/
2. Add to CLAUDE.md agent table (if C-suite or dept lead)
3. Add to CLAUDE.md routing logic (if it changes routing)
4. Update parent agent's "Manages:" line
5. Write CHANGELOG.md entry (AGENT-CREATE)
6. Bump CLAUDE.md version if structural
```

### Agent Updated
```
1. Edit agent file
2. If scope changed → update parent agent "Manages:" or "Reports to:"
3. If routing affected → update CLAUDE.md routing section
4. Write CHANGELOG.md entry (AGENT-UPDATE)
5. If tools added/removed that affect security posture → CISO review
```

### Agent Deprecated
```
1. Add DEPRECATED header to agent file (do not delete — archive)
2. Remove from CLAUDE.md agent table
3. Update parent agent to remove from "Manages:"
4. Update CLAUDE.md routing to redirect affected lanes
5. Write CHANGELOG.md entry (AGENT-DEPRECATE)
```

### Department Added
```
1. Create all agent files for the department
2. Add department chain to CLAUDE.md department section
3. Add C-suite lead to CLAUDE.md agent table
4. Update CLAUDE.md routing logic for new domain
5. Update COO and CISO "Manages" to include new dept (if applicable)
6. Write CHANGELOG.md entry (DEPT-CREATE)
7. Bump CLAUDE.md version (structural change)
```

---

## CHANGELOG ENTRY FORMAT

Every change must produce an entry in `CHANGELOG.md` in this exact format:

```markdown
## [YYYY-MM-DD] | [CHANGE-TYPE] | [Agent or Component Name]

**Changed By:** [Lead Orchestrator | CEO | Agent name]
**Approved By:** [CEO | CISO | CAE-Audit — per tier]
**Risk Tier:** [0 | 1 | 2 | 3]
**COSO Component:** [Control Environment | Risk Assessment | Control Activities | Information & Communication | Monitoring]

**Summary:** [1-2 sentences describing what changed and why]

**Files Modified:**
- `path/to/file.md` — [what changed in this file]

**Propagation Completed:**
- [ ] Parent agent updated: [parent agent name or N/A]
- [ ] CLAUDE.md updated: [section name or N/A]
- [ ] CHANGELOG.md entry written: [YES]

**Sensitive Data Impact:** [NONE | LOW | HIGH — describe if not NONE]
**Rollback:** [how to revert if needed]
```

---

## COSO MAPPING

| COSO Component | How It Applies to Agent OS |
|---------------|---------------------------|
| **Control Environment** | CEO = final authority. CAE-Audit = independent. No agent self-approves structural changes. |
| **Risk Assessment** | Every change classified by Risk Tier (0-3) before execution. |
| **Control Activities** | This policy. Propagation rules. Tool grant/revoke controls. |
| **Information & Communication** | CHANGELOG.md = authoritative record. CLAUDE.md = master control register. |
| **Monitoring Activities** | CAE-Audit reviews CHANGELOG periodically. Flags gaps in propagation. |

---

## SEGREGATION OF DUTIES

| Action | May Initiate | Must Approve |
|--------|-------------|--------------|
| Create/update agent | Lead Orchestrator | CEO (structural) / automatic (minor) |
| Grant new tool to agent | Lead Orchestrator | CISO (if sensitive tool) |
| Update CLAUDE.md routing | Lead Orchestrator | CEO (structural) |
| Deprecate an agent | Lead Orchestrator | CEO |
| Create new department | Lead Orchestrator | CEO |
| Update data classification | CAE-Audit | CEO |

---

## STRUCTURAL VS MINOR CHANGE DEFINITION

This distinction determines whether CEO approval is required. The Lead Orchestrator cannot self-classify — use this list.

**STRUCTURAL (requires CEO approval):**
- Adding, removing, or renaming a department
- Adding, removing, or renaming a C-suite agent (COO, CISO, CTO, CPO, CFO, GC, CRO, CAE, CDO, CPlatO, CAIO, CCO, CSO, CIRO, CPrO, CIO)
- Changing the authority boundary of any agent (what they can/cannot approve)
- Modifying compliance frameworks in CLAUDE.md (adding/removing COSO, SOC 2, NIST, SOX, COBIT, CIS)
- Changing routing logic for any Tier 2 or Tier 3 domain
- Modifying the Risk Tier definitions (0-3)
- Modifying the Three-File Rule or propagation requirements
- Adding or removing governance councils (AI & Automation Council, GRC Council)
- Deprecating any agent with 5+ subordinates in their chain

**MINOR (Lead Orchestrator may execute automatically):**
- Updating an existing agent's prompt content, frameworks, or output format
- Adding or removing tools from a non-C-suite agent (subject to CISO review for sensitive tools)
- Updating CLAUDE.md version history or changelog entries
- Correcting a reporting chain typo or naming inconsistency
- Adding a new IC-level or Director-level agent within an existing department
- Updating cross-department service sections in research agents

---

## SENSITIVE TOOL CLASSIFICATION

Tools that require CISO review before granting to any agent:

| Tool | Risk Level | Why |
|------|-----------|-----|
| `Bash` | HIGH | Shell execution — code injection risk |
| `Write` | MEDIUM | File creation — could overwrite critical files |
| `WebFetch` | MEDIUM | External network calls — SSRF risk |
| `Agent` | MEDIUM | Spawns sub-agents — blast radius amplification |
| `mcp__*` | MEDIUM | External service integrations — data exfiltration risk |
| `Read`, `Glob`, `Grep`, `Edit` | LOW | Standard file operations |

---

## TIER 2 / TIER 3 APPROVAL RECORD FORMAT

Any Tier 2 or Tier 3 action requires a documented CEO approval **before execution proceeds**. Log the approval as a CHANGELOG entry of type APPROVAL-RECORD using this format:

```markdown
## [YYYY-MM-DD] | APPROVAL-RECORD | [Action Being Approved]

**Approved By:** CEO
**Risk Tier:** [2 | 3]
**Action:** [what was approved — be specific]
**Scope:** [what is included and explicitly what is excluded]
**Conditions:** [any conditions or constraints the CEO attached]
**Expires:** [date after which this approval no longer covers the action, or NONE]
**Logged Before Execution:** YES
```

This entry must appear in CHANGELOG.md before the approved action is taken. No retroactive approval records.

---

## VERSIONING SCHEME

All AI OS documents and the master CLAUDE.md use **Semantic Versioning: MAJOR.MINOR.PATCH**

| Digit | Increment When | Reset Rule |
|-------|---------------|------------|
| **MAJOR** | Transformational rebuild — whole OS redesign, replacement of the governance model | Resets MINOR and PATCH to 0 |
| **MINOR** | Structural change — new department, new C-suite agent, new governance body, major policy overhaul | Resets PATCH to 0 |
| **PATCH** | Fix or remediation — audit findings closed, reporting chain corrected, typo fix, propagation completed | Never resets other digits |

**Examples:**
- New department added → MINOR bump (e.g., 1.6.1 → 1.7.0)
- Audit findings remediated → PATCH bump (e.g., 1.6.0 → 1.6.1)
- OS completely rebuilt from scratch → MAJOR bump (e.g., 1.7.0 → 2.0.0)

---

## POLICY VERSION HISTORY

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-03-19 | Initial change management policy. COSO-mapped. Full propagation rules, changelog format, SoD matrix, and sensitive tool classification. |
| 1.1.0 | 2026-03-19 | Adopted Semantic Versioning (MAJOR.MINOR.PATCH). Added versioning scheme section. |
