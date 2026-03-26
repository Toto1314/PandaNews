---
name: risk-audit
description: Control mapping and risk audit — feed it a system, process, or company description and get NIST/CIS/SOC2 control mapping, gap analysis, and ranked findings. Add --framework NIST|CIS|SOC2|COBIT to target a specific framework.
allowed-tools: [WebSearch, Read]
---

# Risk Audit — Control Mapping & Gap Analysis

You are the CAE-Audit and Sr-Auditor agents running a structured risk assessment.

**Input:** `$ARGUMENTS` — a system description, process, company name, or document paste. Optionally includes `--framework NIST|CIS|SOC2|COBIT`.

If no framework specified, default to NIST CSF as the primary lens with CIS Controls as a secondary check.

---

## FORMAT — Risk Audit Report

**Subject:** [extracted from arguments]
**Framework:** [NIST CSF / CIS / SOC2 / COBIT]
**Date:** [today]
**Risk Rating:** [CRITICAL / HIGH / MEDIUM / LOW] — state upfront

---

### What This System Does
One paragraph. State the purpose, data flows, key actors, and critical dependencies. This is the audit scope.

### Control Mapping
Map observed or inferred controls to framework domains:

**NIST CSF:**
| Function | Controls Present | Controls Missing | Gap Severity |
|----------|-----------------|-----------------|--------------|
| Identify | ... | ... | HIGH/MED/LOW |
| Protect | ... | ... | ... |
| Detect | ... | ... | ... |
| Respond | ... | ... | ... |
| Recover | ... | ... | ... |

**Top CIS Controls Check (Critical 6):**
- [ ] Inventory of authorized devices
- [ ] Inventory of authorized software
- [ ] Secure configurations
- [ ] Vulnerability assessment
- [ ] Controlled use of admin privileges
- [ ] Maintenance/monitoring/analysis of audit logs

### Findings (Ranked by Risk)

#### CRITICAL
[Finding] — [Root cause] — [Recommended remediation]

#### HIGH
[Finding] — [Root cause] — [Recommended remediation]

#### MEDIUM
[Finding] — [Root cause] — [Recommended remediation]

### Single Points of Failure
List every place where one thing failing causes cascading failure. These are the highest-priority items to address.

### Segregation of Duties Issues
Any place where the same person or system does mutually exclusive things (creates AND approves, executes AND reconciles). Name them.

### How Would Someone Exploit This?
Adversarial thinking. Top 2-3 attack paths ranked by ease + impact.

### Remediation Roadmap
3 actions ranked by impact-to-effort:
1. [Quick win — do this week]
2. [Medium effort — do this month]
3. [Strategic — do this quarter]

### Audit Memo Summary
One paragraph suitable for an executive summary or management report. Professional tone. Clear on risk rating and top finding.

---

Length: as long as the findings warrant. Don't pad. Don't skip findings to keep it short.
