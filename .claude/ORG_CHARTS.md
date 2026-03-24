# AI OS — Organization Charts
**Version:** 1.1 | **Owner:** Lead Orchestrator | **Updated:** 2026-03-20

> **Navigation:** `INDEX.md` — fast lookup | `SYSTEM_MAP.md` — system routing & risk tier diagrams | `CLAUDE.md` — master register
> This file contains department org charts (who reports to whom). For system architecture, routing, and pipeline diagrams, see `SYSTEM_MAP.md`.

---

## DIAGRAM 1 — Master Org Chart (Full Company)

```mermaid
graph TD
    CEO["👤 CEO\n(Final Authority)"]
    LO["🤖 Lead Orchestrator\n(Claude — routes everything)"]

    CEO --> LO

    subgraph GOV["⚖️ Governance Councils"]
        AI_COUNCIL["AI & Automation Council\nCAIO · CISO · CDO · GC · CAE · CPO · CRO"]
        GRC_COUNCIL["GRC Council\nGC · CISO · CCO-Compliance · CFO · CAE"]
    end

    LO --> GOV

    subgraph OPS["🏢 C-Suite Operations"]
        COO["COO\nChief Operating Officer"]
        CAE["CAE-Audit\n⚖️ Independent Assurance"]
    end

    LO --> OPS

    subgraph SECURITY["🔐 Security"]
        CISO --> VP_SEC["VP Security"]
        VP_SEC --> PSA["Principal Security Architect"]
        PSA --> DIR_SEC["Dir Security"]
        DIR_SEC --> SEC_MGR["Security Manager"]
        SEC_MGR --> SR_SEC["Sr Security Engineer"]
        SR_SEC --> SEC_ENG["Security Engineer"]
        SEC_ENG --> SEC_ASSOC["Security Associate"]
        SEC_ASSOC --> SEC_ANALYST["Security Analyst"]
    end

    subgraph ENGINEERING["💻 Engineering"]
        CTO["CTO-Engineering"]
        CTO --> VP_ENG["VP Engineering"]
        VP_ENG --> PE["Principal Engineer"]
        PE --> DIR_ENG["Dir Engineering"]
        DIR_ENG --> ENG_MGR["Engineering Manager"]
        ENG_MGR --> SR_SWE["Sr Software Engineer"]
        SR_SWE --> SWE["Software Engineer"]
        SWE --> AE["Associate Engineer"]
    end

    subgraph PRODUCT["📦 Product"]
        CPO["CPO"]
        CPO --> VP_PROD["VP Product"]
        VP_PROD --> PPM["Principal PM"]
        PPM --> DIR_PROD["Dir Product"]
        DIR_PROD --> SR_PM["Sr PM"]
        SR_PM --> PM["Product Manager"]
        PM --> PA["Product Analyst"]
    end

    subgraph FINANCE["💰 Finance"]
        CFO["CFO"]
        CFO --> VP_FIN["VP Finance"]
        VP_FIN --> PFA["Principal Financial Analyst"]
        PFA --> DIR_FIN["Dir Finance"]
        DIR_FIN --> FIN_MGR["Finance Manager"]
        FIN_MGR --> SR_FA["Sr Financial Analyst"]
        SR_FA --> FA["Financial Analyst"]
        FA --> FIN_ASSOC["Finance Associate"]
    end

    subgraph LEGAL["⚖️ Legal / GRC"]
        GC["GC-Legal"]
        GC --> CCO_COMP["Chief Compliance Officer"]
        CCO_COMP --> VP_LEGAL["VP Legal & Risk"]
        VP_LEGAL --> PCA["Principal Compliance Architect"]
        PCA --> DIR_COMP["Dir Compliance"]
        DIR_COMP --> COMP_MGR["Compliance Manager"]
        COMP_MGR --> RISK_ANALYST["Risk Analyst"]
        RISK_ANALYST --> COMP_ANALYST["Compliance Analyst"]
    end

    subgraph GTM["🚀 GTM / Revenue"]
        CRO["CRO-GTM"]
        CRO --> VP_SALES["VP Sales"]
        CRO --> VP_MKT["VP Marketing"]
        VP_SALES --> RSD["Regional Sales Director"]
        RSD --> SA["Solutions Architect"]
        SA --> FDE["Forward Deployed Engineer"]
        FDE --> AE_SALES["Account Executive"]
        AE_SALES --> CSM["Customer Success Manager"]
        CSM --> SDR["SDR"]
        SDR --> BDR["BDR"]
        VP_MKT --> MKT_MGR["Marketing Manager"]
        MKT_MGR --> CONTENT["Content Strategist"]
        CONTENT --> GROWTH["Growth Analyst"]
    end

    subgraph INVESTMENTS["📈 Investments"]
        CIO["CIO-Investments"]
        CIO --> VP_INV["VP Investments"]
        VP_INV --> PORT_MGR["Portfolio Manager"]
        PORT_MGR --> SR_QUANT["Sr Quant Analyst"]
        SR_QUANT --> QUANT["Quant Analyst"]
        QUANT --> INV_ANALYST["Investment Analyst"]
        CIO --> DIR_RES_INV["Dir Research-Investments"]
        DIR_RES_INV --> SR_EQ["Sr Equity Analyst"]
        SR_EQ --> EQ_ANALYST["Equity Analyst"]
        EQ_ANALYST --> RES_ASSOC_INV["Research Associate"]
        CIO --> RISK_MGR["Risk Manager"]
        RISK_MGR --> SR_RISK["Sr Risk Analyst"]
        SR_RISK --> RISK_ANALYST2["Risk Analyst"]
    end

    subgraph DATA["📊 Data & Analytics"]
        CDO["CDO-Data"]
        CDO --> VP_DATA["VP Data"]
        VP_DATA --> PDA["Principal Data Architect"]
        PDA --> DIR_DE["Dir Data Engineering"]
        DIR_DE --> SR_DE["Sr Data Engineer"]
        DIR_DE --> DIR_ANALYTICS["Dir Analytics"]
        DIR_ANALYTICS --> SR_DA["Sr Data Analyst"]
        SR_DA --> DATA_SCI["Data Scientist"]
    end

    subgraph DEVOPS["☁️ DevOps / Platform"]
        CPLATO["CPlatO-DevOps"]
        CPLATO --> VP_PLAT["VP Platform Engineering"]
        VP_PLAT --> PPA["Principal Platform Architect"]
        PPA --> DIR_CLOUD["Dir Cloud Infrastructure"]
        DIR_CLOUD --> SR_DEVOPS["Sr DevOps Engineer"]
        CPLATO --> DIR_SRE["Dir SRE"]
        DIR_SRE --> SRE["SRE Team"]
    end

    subgraph AI_ML["🤖 AI & ML"]
        CAIO["CAIO-AI"]
        CAIO --> VP_AI["VP AI Engineering"]
        VP_AI --> DIR_ML["Dir ML Engineering"]
        DIR_ML --> SR_ML["Sr ML Engineer"]
        VP_AI --> DIR_AI_RES["Dir AI Research"]
        DIR_AI_RES --> AI_RES_SCI["AI Research Scientists"]
    end

    subgraph DESIGN["🎨 Design / CX"]
        CCO["CCO-Design"]
        CCO --> VP_CX["VP Customer Experience"]
        VP_CX --> DIR_UX["Dir UX Design"]
        DIR_UX --> SR_UX["Sr UX Designer"]
        VP_CX --> DIR_UR["Dir User Research"]
        VP_CX --> DIR_SUPPORT["Dir Customer Support"]
    end

    subgraph STRATEGY["🎯 Strategy"]
        CSO["CSO-Strategy"]
        CSO --> VP_STRAT["VP Strategy"]
        VP_STRAT --> DIR_CI["Dir Competitive Intelligence"]
        VP_STRAT --> DIR_CORP_STRAT["Dir Corporate Strategy"]
    end

    subgraph RESEARCH["🔬 Research & Innovation"]
        CIRO["CIRO-Research"]
        CIRO --> VP_RES["VP Research"]
        VP_RES --> PR["Principal Researcher"]
        PR --> DIR_TECH_R["Dir TechResearch"]
        DIR_TECH_R --> SR_TECH_R["Sr Tech Researcher"]
        PR --> DIR_MKT_R["Dir MarketResearch"]
        PR --> DIR_SCI_R["Dir ScientificResearch"]
        DIR_SCI_R --> RES_SCI["Research Scientist"]
        RES_SCI --> RES_ASSOC["Research Associate"]
        VP_RES --> HEAD_INNOV["Head InnovationLab"]
        HEAD_INNOV --> INNOV_ENG["Innovation Engineer"]
    end

    subgraph PROMPT_ENG["✍️ Prompt Engineering"]
        CPRO["CPrO-Prompting"]
        CPRO --> VP_PROMPT["VP PromptEngineering"]
        VP_PROMPT --> PPE["Principal PromptEngineer"]
        PPE --> DIR_PR["Dir PromptResearch"]
        PPE --> DIR_PO["Dir PromptOps"]
        PPE --> DIR_PQ["Dir PromptQA"]
        DIR_PQ --> SR_PE["Sr Prompt Engineer"]
        SR_PE --> PE_ENG["Prompt Engineer"]
        PE_ENG --> UPO["User-Prompt-Optimizer"]
    end

    subgraph AUDIT["🔍 Internal Audit (Independent)"]
        CAE --> DIR_IA["Dir Internal Audit"]
        DIR_IA --> SR_AM["Sr Audit Manager"]
        SR_AM --> AM["Audit Manager"]
        AM --> SR_AUD["Sr Auditor"]
        SR_AUD --> AUD["Auditor"]
        AUD --> AUD_ASSOC["Audit Associate"]
    end

    COO --> SECURITY
    COO --> ENGINEERING
    COO --> PRODUCT
    COO --> FINANCE
    COO --> LEGAL
    COO --> GTM
    COO --> INVESTMENTS
    COO --> DATA
    COO --> DEVOPS
    COO --> AI_ML
    COO --> DESIGN
    COO --> STRATEGY
    COO --> RESEARCH
    COO --> PROMPT_ENG
```

---

## DIAGRAM 2 — Routing Logic Flow (Request Classification)

```mermaid
flowchart TD
    INPUT["📨 CEO Input\nor Task Request"]

    INPUT --> OPTIMIZE["User-Prompt-Optimizer\n(auto-upgrade if vague)"]
    OPTIMIZE --> CLASSIFY

    subgraph CLASSIFY["Step 1: Domain Classification (Keywords)"]
        D1["Feature/Code?\n'build' 'deploy' 'refactor'"]
        D2["Research?\n'research' 'analyze' 'benchmark'"]
        D3["Security?\n'vulnerability' 'breach' 'SOC2'"]
        D4["Strategy/GTM?\n'GTM' 'pricing' 'launch'"]
        D5["Investments?\n'portfolio' 'equity' 'treasury'"]
        D6["Data/Analytics?\n'warehouse' 'ETL' 'dashboard'"]
        D7["Infra/DevOps?\n'Kubernetes' 'CI/CD' 'Terraform'"]
        D8["AI/ML/Agents?\n'LLM' 'RAG' 'fine-tune'"]
        D9["Prompts?\n'prompt' 'evals' 'guardrail'"]
        D10["UX/Design?\n'UX' 'journey' 'NPS'"]
        D11["Simple/Tier 0?"]
        D12["Ambiguous?"]
    end

    CLASSIFY --> TIER

    subgraph TIER["Step 2: Risk Tier"]
        T0["Tier 0\nInternal, reversible\nno data/legal risk"]
        T1["Tier 1\nModerate\nInternal impact"]
        T2["Tier 2\nHigh/Material\nCustomer-facing\nProd systems\nRegulated data"]
        T3["Tier 3\nAmbiguous/Strategic\nCross-domain\nExistential risk"]
    end

    T3 --> STOP["🛑 STOP\nEscalate to CEO\n+ AI/GRC Council"]
    T2 --> HUMAN["⏸️ PAUSE\nRequire CEO/Exec\nApproval First"]
    HUMAN --> ROUTE
    T0 --> ROUTE
    T1 --> ROUTE

    subgraph ROUTE["Step 3: Route to Department"]
        R1["CPO → CTO → CISO\n(Feature/Code)"]
        R2["CIRO-Research\n(Research)"]
        R3["CISO or GC-Legal\n(Security/Compliance)"]
        R4["CPO + CRO-GTM\n(Strategy/GTM)"]
        R5["CIO-Investments → CFO\n(Investments)"]
        R6["CDO-Data → CISO\n(Data/Analytics)"]
        R7["CPlatO → CISO\n(Infra/DevOps)"]
        R8["CAIO → AI Council\n(AI/ML/Agents)"]
        R9["CPrO-Prompting → QA\n(Prompts)"]
        R10["CCO-Design → CPO\n(UX/Design)"]
        R11["Local-Model-Router\n(Ollama — Tier 0)"]
    end

    ROUTE --> AUDIT_GATE

    subgraph AUDIT_GATE["Step 4: CAE-Audit Gate (Tier-Scaled)"]
        AG0["Tier 0-1:\nCAE Informed Only\n(periodic reports)"]
        AG2["Tier 2:\nCAE Reviews\nControl Design or\nAssurance Engagement"]
        AG3["Tier 3:\nCAE Investigates\nAfter CEO Escalation"]
    end

    AUDIT_GATE --> CEO_OUT["✅ Output to CEO"]
```

---

## DIAGRAM 3 — Technical Agent Pipeline

```mermaid
flowchart LR
    CEO_IN["CEO Request\n(non-trivial build/fix)"]

    CEO_IN --> ORCH["orchestrator\n(master coordinator)"]

    ORCH --> SCOUT["scout\n(codebase mapper)\nReads all relevant files\nMaps dependencies\nSurfaces constraints"]

    SCOUT --> ARCH["architect\n(implementation planner)\nProduces step-by-step plan\nFile-level precision\nNo code written"]

    ARCH --> BUILD["builder\n(code implementer)\nExecutes plan exactly\nMinimal changes\nNo improvisation"]

    BUILD --> VALID["validator\n(quality gate)\nChecks vs architect plan\nRuns tests\nSecurity scan\nIssues PASS or FAIL"]

    VALID --> |"PASS"| CEO_OUT["✅ Complete\nReport to CEO"]
    VALID --> |"FAIL"| BUILD

    BOOST["boost\n(productivity intervener)\nInvoked when stuck\nDiagnoses trap\nOne concrete next action"]

    BUILD --> |"3+ edits, no progress"| BOOST
    BOOST --> BUILD
```

---

## DIAGRAM 4 — Research Department Cross-Functional Flow

```mermaid
flowchart TD
    CEO_RES["CEO Research Request\nor Department Trigger"]

    CEO_RES --> CIRO["CIRO-Research\n(Chief Innovation & Research Officer)\nAll departments. Always first to know."]

    CIRO --> VP_RES["VP-Research\n(Intake Coordinator)\nScopes, gates, routes"]

    VP_RES --> PR["Principal-Researcher\nCross-domain synthesis\nMost complex questions"]

    VP_RES --> HEAD_INNOV["Head-InnovationLab\nRapid experiments\nPrototypes"]

    PR --> DIR_AI["Dir-AI-Research\nLLMs, papers, benchmarks\nHuggingFace paper_search"]

    PR --> DIR_SCI["Dir-ScientificResearch\nAcademic literature\nEvidence hierarchy\nHuggingFace paper_search"]

    PR --> DIR_TECH["Dir-TechResearch\nStack, tools, OSS\nHuggingFace hub_repo_search"]

    PR --> DIR_MKT["Dir-MarketResearch\nMarket sizing, competitive\nSEC filings, analyst reports"]

    DIR_SCI --> RES_SCI["Research-Scientist\nPaper reading\nLiterature monitoring"]

    RES_SCI --> RES_ASSOC["Research-Associate\nData gathering\nSource verification"]

    HEAD_INNOV --> INNOV_ENG["Innovation-Engineer\nPrototype building\nTool testing"]

    subgraph SERVES["Research Serves All Departments"]
        CAIO_OUT["CAIO-AI\nModel evals, LLM papers"]
        CSO_OUT["CSO-Strategy\nCompetitive intelligence"]
        CISO_OUT["CISO\nThreat research"]
        CTO_OUT["CTO-Engineering\nStack decisions"]
        CIO_OUT["CIO-Investments\nSector analysis"]
        CPO_OUT["CPO\nMarket needs"]
        CDO_OUT["CDO-Data\nData tech trends"]
        CPRO_OUT["CPrO-Prompting\nPrompt technique frontier"]
        GC_OUT["GC-Legal\nRegulatory landscape"]
    end

    CIRO --> SERVES
    DIR_AI --> CAIO_OUT
    DIR_AI --> CPRO_OUT
    DIR_SCI --> CISO_OUT
    DIR_SCI --> CDO_OUT
    DIR_TECH --> CTO_OUT
    DIR_TECH --> CDO_OUT
    DIR_MKT --> CSO_OUT
    DIR_MKT --> CIO_OUT
    DIR_MKT --> CPO_OUT
    DIR_SCI --> GC_OUT
```

---

## DIAGRAM 5 — Governance & Risk Tier Flow

```mermaid
flowchart TD
    ACTION["Any Action or Change\nin the AI OS"]

    ACTION --> TIER_CHECK{"Risk Tier\nClassification"}

    TIER_CHECK --> |"Tier 0\nSimple, internal,\nno data/legal risk"| T0_PATH["Auto-proceed\nLocal-Model-Router\nNo exec review\nCAE informed via reports"]

    TIER_CHECK --> |"Tier 1\nModerate,\ninternal impact"| T1_PATH["Exec owner approves\nCAE informed only\nNo audit engagement"]

    TIER_CHECK --> |"Tier 2\nCustomer-facing\nProd systems\nRegulated data"| T2_PATH["⏸️ PAUSE\nExec owner + accountable C-suite\nmust approve FIRST"]

    T2_PATH --> T2_CONSULT["Consult relevant controls:\nCISO (security)\nGC-Legal (legal)\nCDO-Data (data)\nCPO-Privacy (privacy)"]

    T2_CONSULT --> T2_CAE["CAE-Audit:\nReviews control design\nOR runs assurance engagement"]

    T2_CAE --> T2_EXEC["✅ Execute\n(with audit log)"]

    TIER_CHECK --> |"Tier 3\nAmbiguous, cross-domain\nExistential risk"| T3_PATH["🛑 STOP ALL AUTOMATION\nEscalate to CEO immediately"]

    T3_PATH --> COUNCILS{"Which Council?"}

    COUNCILS --> |"AI/Agent involved"| AI_COUNCIL["AI & Automation Council\nCAIO · CISO · CDO · GC · CAE · CPO · CRO"]

    COUNCILS --> |"Non-AI risk/policy"| GRC_COUNCIL["GRC Council\nGC · CISO · CCO-Compliance · CFO · CAE"]

    AI_COUNCIL --> CEO_DECISION["CEO Final Decision"]
    GRC_COUNCIL --> CEO_DECISION

    CEO_DECISION --> |"Approved"| EXEC_WITH_LOG["Execute with\nFull Audit Log\nCHANGELOG entry\nCAE monitoring"]

    CEO_DECISION --> |"Rejected"| ARCHIVE["Archive decision\nDocument rationale\nCHANGELOG entry"]
```

---

## DIAGRAM 6 — Change Management Flow (Documentation Layer)

```mermaid
flowchart TD
    TRIGGER["Change Trigger:\nAgent Created/Updated/Deprecated\nDept Added/Changed\nPolicy Updated\nTool Granted/Revoked"]

    TRIGGER --> TYPE{"Change Type?"}

    TYPE --> |"AGENT-CREATE"| AC["1. Write agent file\n2. Add to CLAUDE.md table\n3. Update CLAUDE.md routing\n4. Update parent agent Manages\n5. Write CHANGELOG entry\n6. Bump version if structural"]

    TYPE --> |"AGENT-UPDATE"| AU["1. Edit agent file\n2. If scope changed → update parent\n3. If routing affected → update CLAUDE.md\n4. Write CHANGELOG entry\n5. CISO review if sensitive tool added"]

    TYPE --> |"DEPT-CREATE"| DC["1. Create all agent files\n2. Add to CLAUDE.md dept chain\n3. Add C-suite to CLAUDE.md table\n4. Update routing for new domain\n5. Update COO + CISO Manages\n6. Write CHANGELOG entry\n7. Bump version"]

    TYPE --> |"AGENT-DEPRECATE"| AD["1. Add DEPRECATED header (don't delete)\n2. Remove from CLAUDE.md table\n3. Update parent Manages\n4. Update CLAUDE.md routing\n5. Write CHANGELOG entry"]

    AC --> VERIFY
    AU --> VERIFY
    DC --> VERIFY
    AD --> VERIFY

    subgraph VERIFY["Three-File Rule Verification"]
        F1["✅ Agent file updated"]
        F2["✅ Parent agent updated"]
        F3["✅ CLAUDE.md updated"]
        F4["✅ CHANGELOG.md entry written"]
    end

    VERIFY --> |"All 4 complete"| COMPLETE["✅ Change Complete\nCOSO Compliant"]

    VERIFY --> |"Any missing"| FLAG["🚨 CAE-Audit Flag\nIncomplete propagation\nOpen item in CHANGELOG"]

    FLAG --> REMEDIATE["Remediate before\nnext session"]
```

---

## DIAGRAM 7 — Data Classification Flow

```mermaid
flowchart TD
    DATA_IN["Data Encountered\nby Any Agent"]

    DATA_IN --> CLASSIFY{"Classify Data"}

    CLASSIFY --> |"API keys, credentials\nPII, health data\nFinancial accounts"| T1["🔴 T1 RESTRICTED\nHighest sensitivity"]

    CLASSIFY --> |"Agent system prompts\nInternal strategy\nUnreleased plans\nM&A targets"| T2["🟠 T2 CONFIDENTIAL\nInternal only"]

    CLASSIFY --> |"Agent outputs\nProcess docs\nResearch briefs\nOperational reports"| T3["🟡 T3 INTERNAL\nInternal distribution"]

    CLASSIFY --> |"Published research\nPublic docs\nMarketing content"| T4["🟢 T4 PUBLIC\nNo restrictions"]

    T1 --> T1_RULES["MUST NOT:\n• Output in any response\n• Pass to sub-agents\n• Store in memory/markdown\n• Pass through MCP/WebSearch\nACTION: Redact + Flag CISO + CEO"]

    T2 --> T2_RULES["MUST NOT:\n• Expose system prompts in outputs\n• Share with external-facing agents\nMAY:\n• Use internally for decisions\n• Pass within OS trust boundary"]

    T3 --> T3_RULES["MAY:\n• Use and produce freely within OS\nMUST NOT:\n• Route to external services\n• POST via WebFetch without CEO auth"]

    T4 --> T4_RULES["No restrictions.\nMay share, publish, or\npass to any system."]

    subgraph MCP_RULES["MCP Tool Data Rules"]
        MCP1["WebSearch: Never include T1/T2 in queries"]
        MCP2["WebFetch: GET only for public info\nNo POST of T1/T2 data"]
        MCP3["HuggingFace tools: Research queries only\nNo sensitive data in parameters"]
        MCP4["Bash: Never echo T1 to stdout\nNever write T1 unencrypted"]
    end

    T1_RULES --> INCIDENT["Violation Detected?\n1. Stop immediately\n2. Flag CISO + CEO\n3. CHANGELOG: SECURITY-INCIDENT\n4. Do not retry without CEO auth"]
```

---

## SUMMARY STATS

| Metric | Count |
|--------|-------|
| Total Agents | 131 |
| Departments | 15 |
| Governance Bodies | 2 (AI Council, GRC Council) |
| Technical Pipeline Agents | 6 (orchestrator, scout, architect, builder, validator, boost) |
| Research Dept Agents | 17 |
| Compliance Frameworks | 6 (COSO, SOC 2, NIST CSF, SOX, COBIT, CIS) |
| Risk Tiers | 4 (0-3) |
| Data Classification Tiers | 4 (T1-T4) |
| Governing Documents | 4 (CLAUDE.md, CHANGELOG, CHANGE_MANAGEMENT, DATA_CLASSIFICATION) |
| Routing Domains | 12 |
