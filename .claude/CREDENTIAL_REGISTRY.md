# AI OS — Credential Registry
**Version:** 1.0 | **Owner:** CISO | **Approved By:** CEO
**COSO Component:** Control Activities · Monitoring Activities
**Frameworks:** NIST CSF · CIS · SOC 2 · COSO

> **Navigation:** `INDEX.md` — fast lookup | `DATA_CLASSIFICATION.md` — T1 RESTRICTED handling policy | `Dir-MCPHub.md` — MCP credential management | `CHANGE_MANAGEMENT.md` — how to log credential lifecycle events

---

## PURPOSE

Every external credential used by any agent in this AI OS is a T1 RESTRICTED asset. This registry is the single source of truth for credential lifecycle management: what credentials exist, who owns them, when they expire, and how to revoke them.

**Core Principle:** If a credential is not in this registry, it should not exist in the system. Discovery of an unregistered credential is a CISO-level finding.

---

## CREDENTIAL LIFECYCLE RULES

1. **Registration is mandatory** — any new credential (API key, token, OAuth secret, service account password) must be added to this registry before use.
2. **Rotation schedule** — all credentials must have a defined expiry date. Maximum rotation interval is 90 days unless the issuing service enforces a shorter period.
3. **Expiry alerting** — Dir-MCPHub flags credentials expiring within 14 days to CISO on the first session after the alert window opens.
4. **Revocation** — a credential removed from service must have a REVOKED entry appended (never deleted — the audit trail must show it existed).
5. **One-credential-per-server** — credentials are never reused across multiple MCP servers or services.
6. **Storage** — credentials themselves are never stored here. Only metadata. The actual value lives in environment variables or a secrets manager.

---

## REGISTRY

| ID | Credential Name | Owner Agent | Issuing Service | Created | Expiry | Last Rotated | Status | Revocation Procedure |
|----|----------------|-------------|-----------------|---------|--------|--------------|--------|---------------------|
| CR-001 | HF_TOKEN | Dir-MCPHub | Hugging Face | — | 90-day cycle | — | ACTIVE — pending issuance | Revoke at hf.co/settings/tokens; remove from shell profile; update .mcp.json |
| CR-002 | TELEGRAM_BOT_TOKEN | Dir-MCPHub | Telegram BotFather | — | 90-day cycle | — | ACTIVE — in use (kiriko_bot.py) | Revoke via BotFather /revoke; remove from env; restart kiriko_bot.py |
| CR-003 | LANGSMITH_API_KEY | Dir-MCPHub | LangSmith | — | 90-day cycle | — | REDACTED (2026-04-01 — key was exposed; placeholder in settings files) | Already redacted. Rotate at smith.langchain.com/settings/api-keys |

> **How to add a row:** Copy the template row below, fill all fields, set Status = ACTIVE, get CISO review before first use.

---

## NEW CREDENTIAL TEMPLATE

```
| CR-XXX | [credential name / env var name] | [agent that uses it] | [issuing service] | [YYYY-MM-DD] | [YYYY-MM-DD] | [YYYY-MM-DD or —] | ACTIVE | [step-by-step revocation] |
```

---

## REVOCATION LOG

When a credential is revoked or rotated, append an entry here (never delete the registry row):

| Date | ID | Action | Performed By | Reason |
|------|----|--------|--------------|--------|
| 2026-04-01 | CR-003 | REDACTED | Lead Orchestrator (auto) | LangSmith API key found in committed settings files (chore/security commit ebd2892) |

---

## QUARTERLY REVIEW CHECKLIST

CISO runs this checklist every quarter (next due: 2026-07-02):

- [ ] All active credentials have been verified as still in use
- [ ] No credential has exceeded its rotation interval without rotation
- [ ] All credentials expiring in the next 14 days are flagged to Dir-MCPHub
- [ ] Any unregistered credentials found in codebase scans are added or revoked
- [ ] AUDIT_FINDINGS.md updated with review outcome
- [ ] CHANGELOG.md entry written for any rotation or revocation actions

---

## POLICY VERSION HISTORY

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-04-02 | Initial credential registry created. 3 known credentials registered (HF_TOKEN, TELEGRAM_BOT_TOKEN, LANGSMITH_API_KEY). Lifecycle rules, rotation schedule, revocation log, quarterly review checklist. |
