# AI OS — System Map & Visual Flowchart
**Version:** 1.15.0 | **Owner:** Lead Orchestrator | **Auto-Update Required:** YES
**Governed by:** COSO · SOC 2 · NIST CSF · SOX · COBIT · CIS

> **LIVING DOCUMENT.** Every structural change to CLAUDE.md MUST also update this file.
> The Five-File Rule applies: agent file → parent → CLAUDE.md → CHANGELOG.md → SYSTEM_MAP.md.
> Render with: VS Code + "Markdown Preview Mermaid Support" extension → `Ctrl+Shift+V`
>
> **Navigation:** `INDEX.md` — fast lookup & routing quick reference | `CLAUDE.md` — master policy register | `ORG_CHARTS.md` — detailed department org charts

---

## 1. Full Family Tree — Every Agent in the System

```mermaid
graph TD
    classDef ceo fill:#d4af37,stroke:#996515,color:#000,font-weight:bold
    classDef lo fill:#7c3aed,stroke:#c4b5fd,color:#fff,font-weight:bold
    classDef council fill:#065f46,stroke:#6ee7b7,color:#fff
    classDef coo fill:#1e3a5f,stroke:#93c5fd,color:#fff,font-weight:bold
    classDef csuite fill:#1e40af,stroke:#93c5fd,color:#fff,font-weight:bold
    classDef vp fill:#1d4ed8,stroke:#bfdbfe,color:#fff
    classDef principal fill:#1e3a5f,stroke:#7dd3fc,color:#fff
    classDef director fill:#0369a1,stroke:#bae6fd,color:#fff
    classDef manager fill:#0284c7,stroke:#e0f2fe,color:#fff
    classDef senior fill:#0ea5e9,stroke:#f0f9ff,color:#000
    classDef ic fill:#bae6fd,stroke:#0284c7,color:#000
    classDef tech fill:#92400e,stroke:#fbbf24,color:#fff,font-weight:bold
    classDef audit fill:#7f1d1d,stroke:#fca5a5,color:#fff,font-weight:bold
    classDef gaming fill:#14532d,stroke:#86efac,color:#fff,font-weight:bold
    classDef notes fill:#4a1d96,stroke:#c4b5fd,color:#fff,font-weight:bold

    CEO["👤 CEO\nFinal Authority"]:::ceo
    LO["🧠 Lead Orchestrator\nClaude"]:::lo

    CEO --> LO

    AIC["⚡ AI & Automation Council\nCAIO · CISO · CDO · GC · CAE · CPO · CRO"]:::council
    GRC["🛡️ GRC Council\nGC · CISO · CCO · CFO · CAE"]:::council

    LO --> AIC
    LO --> GRC

    %% ── TECHNICAL PIPELINE ───────────────────────────────────
    subgraph TP["⚙️ Technical Pipeline"]
        direction LR
        ORC["orchestrator"]:::tech
        SCO["scout"]:::tech
        ARC["architect"]:::tech
        BLD["builder"]:::tech
        VAL["validator"]:::tech
        BST["boost"]:::tech
        ORC --> SCO --> ARC --> BLD --> VAL
    end
    LO --> TP

    %% ── CHIEF NOTES OFFICER (passive tap) ────────────────────
    CNO["📝 Chief Notes Officer\nHaiku · passive · session_notes/"]:::notes
    LO -.->|note stream| CNO

    %% ── OPERATIONS HUB ───────────────────────────────────────
    COO["🏢 COO\nOperations Hub"]:::coo
    LO --> COO

    %% ── SECURITY ─────────────────────────────────────────────
    subgraph SEC["🔐 Security"]
        direction TB
        CISO["CISO"]:::csuite
        VPSEC["VP of Security"]:::vp
        RTENG["Red-Team-Engineer\ndirect — SoD independent"]:::manager
        PSA["Principal Security Architect"]:::principal
        DIRSEC["Director of Security"]:::director
        SECMGR["Security Manager"]:::manager
        SRSE["Sr Security Engineer"]:::senior
        SECE["Security Engineer"]:::ic
        SECA["Security Associate"]:::ic
        SOCA["Security Analyst"]:::ic
        TIA["Threat-Intelligence-Analyst"]:::senior
        ASE["Application-Security-Engineer"]:::senior
        CSE["Cloud-Security-Engineer"]:::senior
        CISO --> VPSEC --> PSA --> DIRSEC --> SECMGR --> SRSE --> SECE --> SECA --> SOCA
        VPSEC -.->|independent| RTENG
        SECMGR --> TIA
        SECMGR --> ASE
        SECMGR --> CSE
    end
    COO --> CISO

    %% ── ENGINEERING ──────────────────────────────────────────
    subgraph ENG["💻 Engineering"]
        direction TB
        CTO["CTO-Engineering"]:::csuite
        VPENG["VP of Engineering"]:::vp
        PE["Principal Engineer"]:::principal
        DIRENG["Director of Engineering"]:::director
        ENGMGR["Engineering Manager"]:::manager
        SRENG["Sr Software Engineer"]:::senior
        SWE["Software Engineer"]:::ic
        ASO["Associate Engineer"]:::ic
        CTO --> VPENG --> PE --> DIRENG --> ENGMGR --> SRENG --> SWE --> ASO
    end
    COO --> CTO

    %% ── PRODUCT ──────────────────────────────────────────────
    subgraph PROD["📦 Product"]
        direction TB
        CPO["CPO"]:::csuite
        VPPROD["VP of Product"]:::vp
        PPM["Principal Product Manager"]:::principal
        DIRPROD["Director of Product"]:::director
        SRPM["Sr Product Manager"]:::manager
        PM["Product Manager"]:::senior
        PRAN["Product Analyst"]:::ic
        CPO --> VPPROD --> PPM --> DIRPROD --> SRPM --> PM --> PRAN
    end
    COO --> CPO

    %% ── FINANCE ──────────────────────────────────────────────
    subgraph FIN["💰 Finance"]
        direction TB
        CFO["CFO"]:::csuite
        VPFIN["VP of Finance"]:::vp
        PFA["Principal Financial Analyst"]:::principal
        DIRFIN["Director of Finance"]:::director
        DIRFPA["Director of FP&A"]:::director
        DIRTRSY["Director of Treasury"]:::director
        FINMGR["Finance Manager"]:::manager
        FINCTRL["Financial Controller"]:::manager
        SRFA["Sr Financial Analyst"]:::senior
        FA["Financial Analyst"]:::ic
        FINA["Finance Associate"]:::ic
        CFO --> VPFIN --> PFA --> DIRFIN --> FINMGR --> SRFA --> FA --> FINA
        VPFIN --> DIRFPA --> SRFA
        VPFIN --> DIRTRSY --> FINCTRL
    end
    COO --> CFO

    %% ── LEGAL / GRC ──────────────────────────────────────────
    subgraph LEG["⚖️ Legal / GRC"]
        direction TB
        GC["GC-Legal"]:::csuite
        CCO_C["Chief Compliance Officer"]:::vp
        VPLR["VP of Legal & Risk"]:::vp
        PCA["Principal Compliance Architect"]:::principal
        DIRCOM["Director of Compliance"]:::director
        COMMGR["Compliance Manager"]:::manager
        RISKA["Risk Analyst"]:::senior
        COMA["Compliance Analyst"]:::ic
        GC --> CCO_C --> VPLR --> PCA --> DIRCOM --> COMMGR --> RISKA --> COMA
    end
    COO --> GC

    %% ── GTM / REVENUE ────────────────────────────────────────
    subgraph GTM["🚀 GTM / Revenue"]
        direction TB
        CRO["CRO-GTM"]:::csuite
        VPSAL["VP of Sales"]:::vp
        VPMKT["VP of Marketing"]:::vp
        RSD["Regional Sales Director"]:::director
        SA_GTM["Solutions Architect"]:::manager
        FDE["Forward Deployed Engineer"]:::manager
        AE["Account Executive"]:::senior
        CSM_A["Customer Success Manager"]:::senior
        SDR["SDR"]:::ic
        BDR["BDR"]:::ic
        MM["Marketing Manager"]:::director
        CONT["Content Strategist"]:::senior
        GROW["Growth Analyst"]:::ic
        CRO --> VPSAL --> RSD --> SA_GTM --> FDE --> AE --> CSM_A --> SDR
        CSM_A --> BDR
        CRO --> VPMKT --> MM --> CONT --> GROW
    end
    COO --> CRO

    %% ── INVESTMENTS ──────────────────────────────────────────
    subgraph INV["📈 Investments"]
        direction TB
        CIO["CIO-Investments"]:::csuite
        VPINV["VP of Investments"]:::vp
        PORT["Portfolio Manager"]:::manager
        SRQA["Sr Quant Analyst"]:::senior
        QA_I["Quant Analyst"]:::ic
        INVA["Investment Analyst"]:::ic
        DIRRI["Director of Research"]:::director
        SREAR["Sr Equity Research Analyst"]:::senior
        EAR["Equity Research Analyst"]:::ic
        RAI["Research Associate"]:::ic
        RSKM["Risk Manager"]:::manager
        SRRA["Sr Risk Analyst"]:::senior
        RA_I2["Risk Analyst"]:::ic
        CTRA["⚠️ Contrarian Analyst\nbear case on every BUY"]:::ic
        CIO --> VPINV --> PORT --> SRQA --> QA_I --> INVA
        VPINV --> DIRRI --> SREAR --> EAR --> RAI
        VPINV --> RSKM --> SRRA --> RA_I2
        RSKM --> CTRA
    end
    COO --> CIO

    %% ── DATA & ANALYTICS ─────────────────────────────────────
    subgraph DAT["🗄️ Data & Analytics"]
        direction TB
        CDO["CDO-Data"]:::csuite
        VPDAT["VP of Data"]:::vp
        PDA["Principal Data Architect"]:::principal
        DIRDE["Director of Data Engineering"]:::director
        SRDE["Sr Data Engineer"]:::senior
        DIRAN["Director of Analytics"]:::director
        SRDA["Sr Data Analyst"]:::senior
        DAA["Data Analyst"]:::ic
        DSC["Data Scientist"]:::senior
        CDO --> VPDAT --> PDA --> DIRDE --> SRDE
        VPDAT --> DIRAN --> SRDA --> DAA
        VPDAT --> DSC
    end
    COO --> CDO

    %% ── DEVOPS / PLATFORM ────────────────────────────────────
    subgraph DEV["⚙️ DevOps / Platform"]
        direction TB
        CPLATO["CPlatO-DevOps"]:::csuite
        VPPE["VP of Platform Engineering"]:::vp
        PPA["Principal Platform Architect"]:::principal
        DIRCI["Director of Cloud Infrastructure"]:::director
        SRDOE["Sr DevOps Engineer"]:::senior
        DOES["DevOps Engineer"]:::ic
        DIRSRE["Director of SRE"]:::director
        SREE["SRE Engineer"]:::ic
        DIRBOPS["Dir-BrowserOps\nPlaywright MCP · Domain Allowlist"]:::director
        DIRMCH["Dir-MCPHub\nMetaMCP · Tool ACLs · Namespaces"]:::director
        CPLATO --> VPPE --> PPA --> DIRCI --> SRDOE --> DOES
        VPPE --> DIRSRE --> SREE
        VPPE --> DIRBOPS
        VPPE --> DIRMCH
    end
    COO --> CPLATO

    %% ── AI & ML ──────────────────────────────────────────────
    subgraph AIM["🤖 AI & ML"]
        direction TB
        CAIO["CAIO-AI"]:::csuite
        VPAIE["VP of AI Engineering"]:::vp
        DIRML["Director of ML Engineering"]:::director
        DIRMLO["Director of MLOps"]:::director
        SRML["Sr ML Engineer"]:::senior
        MLE["ML Engineer"]:::ic
        MLO["MLOps Engineer"]:::ic
        DIRAIR["Director of AI Research"]:::director
        CAIO --> VPAIE --> DIRML --> SRML --> MLE
        VPAIE --> DIRMLO --> MLO
        VPAIE --> DIRAIR
    end
    COO --> CAIO

    %% ── CX & DESIGN ──────────────────────────────────────────
    subgraph DES["🎨 CX & Design"]
        direction TB
        CCO_D["CCO-Design"]:::csuite
        VPCX["VP of Customer Experience"]:::vp
        DIRUX["Director of UX Design"]:::director
        SRUXD["Sr UX Designer"]:::senior
        UXDG["UX Designer"]:::ic
        DIRUR["Director of User Research"]:::director
        UXRES["UX Researcher"]:::ic
        DIRCS["Director of Customer Support"]:::director
        CSS["Customer Support Specialist"]:::ic
        CCO_D --> VPCX --> DIRUX --> SRUXD --> UXDG
        VPCX --> DIRUR --> UXRES
        VPCX --> DIRCS --> CSS
    end
    COO --> CCO_D

    %% ── STRATEGY ─────────────────────────────────────────────
    subgraph STR["🔭 Strategy"]
        direction TB
        CSO["CSO-Strategy"]:::csuite
        VPSTR["VP of Strategy"]:::vp
        DIRCS2["Director of Corporate Strategy"]:::director
        DIRCI2["Director of Competitive Intelligence"]:::director
        DIRMR["Director of Market Research"]:::director
        CSO --> VPSTR --> DIRCS2
        VPSTR --> DIRCI2
        VPSTR --> DIRMR
    end
    COO --> CSO

    %% ── RESEARCH & INNOVATION ────────────────────────────────
    subgraph RES["🔬 Research & Innovation"]
        direction TB
        CIRO["CIRO-Research"]:::csuite
        VPRES["VP of Research"]:::vp
        PR["Principal Researcher"]:::principal
        DIRTR["Director of Tech Research"]:::director
        SRTR["Sr Tech Researcher"]:::senior
        DIRMR2["Director of Market Research"]:::director
        DIRSR["Director of Scientific Research"]:::director
        RSCI["Research Scientist"]:::senior
        DIRAR["Director of AI Research"]:::director
        HIL["Head of Innovation Lab"]:::director
        IE["Innovation Engineer"]:::senior
        RA_R["Research Associate"]:::ic
        CIRO --> VPRES --> PR --> DIRTR --> SRTR --> RA_R
        PR --> DIRMR2 --> RA_R
        PR --> DIRSR --> RSCI --> RA_R
        PR --> DIRAR --> RA_R
        VPRES --> HIL --> IE
    end
    COO --> CIRO

    %% ── PROMPT ENGINEERING ───────────────────────────────────
    subgraph PRM["✍️ Prompt Engineering"]
        direction TB
        CPRO["CPrO-Prompting"]:::csuite
        VPPE2["VP of Prompt Engineering"]:::vp
        PPE["Principal Prompt Engineer"]:::principal
        DIRPR["Director of Prompt Research"]:::director
        DIRPO["Director of Prompt Ops"]:::director
        DIRPQ["Director of Prompt QA"]:::director
        PRMGR["Prompt Engineering Manager"]:::manager
        SRPE["Sr Prompt Engineer"]:::senior
        PRENG["Prompt Engineer"]:::ic
        AIS["AI Integration Specialist"]:::ic
        UPO["User Prompt Optimizer"]:::ic
        CPRO --> VPPE2 --> PPE --> DIRPR
        PPE --> DIRPO
        PPE --> DIRPQ --> PRMGR --> SRPE --> PRENG --> AIS --> UPO
        VPPE2 --> CUST["Custodian\nPrompt hygiene · Cache mgmt\nModel-tier optimization · Memory audit"]:::ic
    end
    COO --> CPRO

    %% ── INTERNAL AUDIT (INDEPENDENT) ─────────────────────────
    subgraph AUD["🔍 Internal Audit"]
        direction TB
        CAE["CAE-Audit"]:::audit
        DIRIA["Director of Internal Audit"]:::audit
        SAM["Sr Audit Manager"]:::audit
        AM["Audit Manager"]:::audit
        SRAUD["Sr Auditor"]:::audit
        AUDR["Auditor"]:::audit
        AUDA["Audit Associate"]:::audit
        CAE --> DIRIA --> SAM --> AM --> SRAUD --> AUDR --> AUDA
    end
    COO --> CAE
    CAE -->|"Reports independently"| CEO

    %% ── GAMING INTELLIGENCE ──────────────────────────────
    subgraph GAM["🎮 Gaming Intelligence"]
        direction TB
        DIRGAM["Dir-Gaming\nDept Head · Skill Integration\nKiriko intent router"]:::gaming
        PATCH["Patch-Analyst\nPatch notes · Update cards\nHaiku-class"]:::senior
        COACH["Meta-Coach\nTier lists · Coaching · Loadouts\nSonnet-class"]:::senior
        GRES["Game-Researcher\nMechanics · Esports · Lore\nHaiku-class"]:::ic
        DIRGAM --> PATCH
        DIRGAM --> COACH
        DIRGAM --> GRES
    end
    LO --> DIRGAM

    %% ── CHIEF OF STAFF (AUTONOMOUS COORDINATOR) ──────────
    COS["🗂️ Chief-of-Staff\nCEO proxy · Company rhythm\nAutonomous decision authority"]:::coo
    LO --> COS
    COS --> COO

    %% ── HR / PEOPLE ──────────────────────────────────────
    subgraph HRP["👥 HR / People"]
        direction TB
        CHRO["CHRO"]:::csuite
        VPPPL["VP of People"]:::vp
        DIRTA["Director of Talent Acquisition"]:::director
        DIRHRBP["Director of HR Business Partners"]:::director
        DIRTR2["Director of Total Rewards"]:::director
        SREC["Sr Recruiter"]:::senior
        HRBP["HR Business Partner"]:::ic
        CHRO --> VPPPL --> DIRTA --> SREC
        VPPPL --> DIRHRBP --> HRBP
        VPPPL --> DIRTR2
    end
    COO --> CHRO

    %% ── COMMUNICATIONS ───────────────────────────────────
    subgraph COM["📣 Communications"]
        direction TB
        VPCOM["VP of Communications"]:::vp
        DIRPR["Director of PR"]:::director
        DIRI["Director of Internal Comms"]:::director
        COMSP["Communications Specialist"]:::ic
        VPCOM --> DIRPR --> COMSP
        VPCOM --> DIRI --> COMSP
    end
    COO --> VPCOM

    %% ── PMO / PROGRAMS ───────────────────────────────────
    subgraph PMO["📋 PMO"]
        direction TB
        VPPMO["VP of PMO"]:::vp
        SRPGM["Sr Program Manager"]:::senior
        PGM["Program Manager"]:::ic
        VPPMO --> SRPGM --> PGM
    end
    COS --> VPPMO

    %% ── HEALTHCARE / NURSING ─────────────────────────────
    subgraph HC["🏥 Healthcare / Nursing"]
        direction TB
        CNO_H["CNO\nChief Nursing Officer"]:::csuite
        CHRG["Charge-Nurse\n0–1 patient · unit supervisor"]:::manager
        RSRC["Resource-Nurse\nFloat pool · any unit"]:::senior
        ICURN["ICU-RN\n1:2 ratio"]:::ic
        MSRN["Med-Surg-RN\n1:4 ratio"]:::ic
        ERRN["ER-RN\n1:3 · trauma 1:1"]:::ic
        TELRN["Tele-RN\n1:3 ratio"]:::ic
        LDRN["LD-RN\n1:2 active · 1:1 delivery"]:::ic
        PEDRN["Peds-RN\n1:3–4 ratio"]:::ic
        PACURN["PACU-RN\n1:2 Phase I"]:::ic
        CNO_H --> CHRG
        CNO_H --> RSRC
        CNO_H --> ICURN
        CNO_H --> MSRN
        CNO_H --> ERRN
        CNO_H --> TELRN
        CNO_H --> LDRN
        CNO_H --> PEDRN
        CNO_H --> PACURN
    end
    LO --> CNO_H
```

---

## 2. Technical Execution Pipeline

```mermaid
flowchart LR
    classDef input fill:#d4af37,stroke:#996515,color:#000,font-weight:bold
    classDef tech fill:#92400e,stroke:#fbbf24,color:#fff,font-weight:bold
    classDef gate fill:#065f46,stroke:#6ee7b7,color:#fff
    classDef done fill:#1e40af,stroke:#93c5fd,color:#fff
    classDef trigger fill:#7f1d1d,stroke:#fca5a5,color:#fff

    IN(["CEO Task"]):::input --> TRIAGE{"Spans 2+ files\nor non-trivial?"}

    TRIAGE -->|YES| ORC["🔀 orchestrator\nCoordinates the full task"]:::tech
    TRIAGE -->|NO| DIRECT["Direct execution\nby Lead Orchestrator"]:::done

    ORC --> SCO["🔍 scout\nReads codebase\nMaps files · patterns · deps"]:::tech
    SCO --> ARC["📐 architect\nStep-by-step plan\nFile-level precision"]:::tech
    ARC --> BLD["🔨 builder\nExecutes plan\nMinimal edits only"]:::tech
    BLD --> VAL["✅ validator\nVerifies changes\nRuns tests · scans regressions"]:::gate

    VAL -->|FAIL| BLD
    VAL -->|PASS| DONE(["Task Complete\nReport to CEO"]):::done

    SPIN(["Same file 3x edits\nor stuck spinning"]):::trigger --> BST["⚡ boost\nDiagnoses trap\nPrescribes one next action"]:::tech
    BST --> ORC
```

---

## 3. Routing Decision Tree

```mermaid
flowchart TD
    classDef input fill:#d4af37,stroke:#996515,color:#000,font-weight:bold
    classDef route fill:#1e40af,stroke:#93c5fd,color:#fff
    classDef gate fill:#065f46,stroke:#6ee7b7,color:#fff
    classDef stop fill:#7f1d1d,stroke:#fca5a5,color:#fff
    classDef local fill:#4a1942,stroke:#d8b4fe,color:#fff
    classDef decision fill:#1e3a5f,stroke:#7dd3fc,color:#fff

    IN(["CEO Input"]):::input --> KW{"Keyword\nClassification"}:::decision

    KW -->|"build · implement · refactor · deploy"| FEAT["FEATURE / CODE\nCPO → CTO → CISO"]:::route
    KW -->|"research · analysis · benchmark"| RES["RESEARCH\nCIRO → relevant dept"]:::route
    KW -->|"vulnerability · breach · SOC2 · GDPR"| SEC["SECURITY / COMPLIANCE\nCISO or GC-Legal"]:::route
    KW -->|"GTM · launch · pricing · positioning"| GTM_R["GTM / STRATEGY\nCPO + CRO-GTM → CFO"]:::route
    KW -->|"portfolio · stock · equity · treasury"| INV_R["INVESTMENTS\nCIO-Investments → CFO"]:::route
    KW -->|"data model · warehouse · ETL · dashboard"| DAT_R["DATA / ANALYTICS\nCDO-Data → CISO"]:::route
    KW -->|"Kubernetes · VPC · CI/CD · Terraform"| DEV_R["INFRA / DEVOPS\nCPlatO-DevOps → CISO"]:::route
    KW -->|"browser · playwright · MCP hub · vision agent · screenshot"| BRW_R["BROWSER / MCP\nDir-BrowserOps or Dir-MCPHub"]:::route
    KW -->|"LLM · agent · RAG · fine-tune"| AI_R["AI / ML\nCAIO-AI → AI Council"]:::route
    KW -->|"prompt · system prompt · guardrail"| PRM_R["PROMPT ENGINEERING\nCPrO → Dir-PromptQA"]:::route
    KW -->|"UX · UI · design · NPS · CSAT"| UX_R["UX / DESIGN / CX\nCCO-Design → CPO"]:::route
    KW -->|"patch · nerf · buff · meta · tier list · loadout · esports · ranked"| GAM_R["GAMING\nDir-Gaming → Patch-Analyst\nor Meta-Coach or Game-Researcher"]:::route
    KW -->|"hiring · recruiting · people ops · culture · onboarding · performance"| HR_R["HR / PEOPLE\nCHRO → VP-People"]:::route
    KW -->|"PR · press release · internal comms · announcement · brand messaging"| COM_R["COMMUNICATIONS\nVP-Communications → Dir-PR or Dir-Internal-Comms"]:::route
    KW -->|"program management · cross-dept coordination · initiative tracking"| PMO_R["PMO\nChief-of-Staff → VP-PMO"]:::route
    KW -->|"format · summarize · classify · draft"| T0["TIER 0 — SIMPLE\nLocal-Model-Router\nOllama saves tokens"]:::local
    KW -->|unclear| Q{"One clarifying\nquestion"}:::decision
    Q -->|still unclear| STOP(["STOP\nEscalate to CEO"]):::stop

    FEAT --> TIER{"Risk Tier?"}:::decision
    TIER -->|"0-1  internal · reversible"| MPLAN{"MasterPlanner\ngate needed?"}:::decision
    TIER -->|"2  customer-facing · prod"| CEO_A(["PAUSE\nCEO approval required"]):::stop
    TIER -->|"3  cross-domain · existential"| STOP2(["STOP ALL AUTOMATION\nCEO + Council now"]):::stop

    MPLAN -->|"NO  simple · 1 file · 1 agent"| AUTO["Auto-route to dept chain"]:::gate
    MPLAN -->|"YES  multi-file · multi-agent\nor formal deliverable"| MP["🗺️ MasterPlanner\nProduces plan · STOPS\nWaits for CEO confirm"]:::gate
    MP -->|"CEO confirms"| AUTO
    MP -->|"CEO cancels"| STOP3(["Re-intake from Step 0"]):::stop
```

---

## 4. Risk Tier Classification

```mermaid
flowchart TD
    classDef t0 fill:#065f46,stroke:#6ee7b7,color:#fff
    classDef t1 fill:#854d0e,stroke:#fde047,color:#fff
    classDef t2 fill:#9a3412,stroke:#fb923c,color:#fff
    classDef t3 fill:#7f1d1d,stroke:#fca5a5,color:#fff,font-weight:bold
    classDef q fill:#1e3a5f,stroke:#7dd3fc,color:#fff

    START{"Classify\nthe Task"}:::q

    START --> Q1{"Touches customer\nor regulated data?"}:::q
    Q1 -->|NO| Q2{"Affects\nproduction?"}:::q
    Q1 -->|YES| T2

    Q2 -->|NO| Q3{"Cross-domain\nno clear owner?"}:::q
    Q2 -->|YES| T2

    Q3 -->|NO| Q4{"Internal only?\nReversible?\nNo legal or financial impact?"}:::q
    Q3 -->|YES| T3

    Q4 -->|YES| T0["🟢 TIER 0 — Simple\nCAE not involved\nAuto-route · Local model ok"]:::t0
    Q4 -->|NO| T1["🟡 TIER 1 — Moderate\nCAE informed via reports\nAuto-route to dept chain"]:::t1

    T2["🟠 TIER 2 — High / Material\nCAE reviews controls\nCEO approval REQUIRED"]:::t2
    T3["🔴 TIER 3 — Strategic\nSTOP ALL AUTOMATION\nCEO + Council immediately\nCAE investigates"]:::t3
```

---

## 5. Governance & Compliance

```mermaid
graph LR
    classDef framework fill:#1e3a5f,stroke:#7dd3fc,color:#fff
    classDef all fill:#7c3aed,stroke:#c4b5fd,color:#fff,font-weight:bold

    ALL["All Agents Inherit\nAll 6 Frameworks"]:::all

    ALL --> COSO["COSO\nInternal controls\nRisk management\nSeg. of duties"]:::framework
    ALL --> SOC2["SOC 2\nSecurity · Availability\nConfidentiality · Privacy\nProcessing Integrity"]:::framework
    ALL --> NIST["NIST CSF\nIdentify → Protect\nDetect → Respond\nRecover"]:::framework
    ALL --> SOX["SOX\nAudit trails\nFinancial integrity\nNo undocumented decisions"]:::framework
    ALL --> COBIT["COBIT\nIT governance\naligned to\nbusiness goals"]:::framework
    ALL --> CIS["CIS\nLeast privilege\nSecure defaults\nNo unnecessary exposure"]:::framework
```

---

## 5b. Documentation Layer — Governance Files

```mermaid
graph TD
    classDef master fill:#7c3aed,stroke:#c4b5fd,color:#fff,font-weight:bold
    classDef audit fill:#7f1d1d,stroke:#fca5a5,color:#fff,font-weight:bold
    classDef ops fill:#1e3a5f,stroke:#93c5fd,color:#fff
    classDef sec fill:#065f46,stroke:#6ee7b7,color:#fff
    classDef standard fill:#1e40af,stroke:#93c5fd,color:#fff
    classDef nav fill:#92400e,stroke:#fbbf24,color:#fff,font-weight:bold

    CLAUDE["📋 CLAUDE.md\nMaster Control Register\nOrg chart · Routing · Rules · Version\nOwner: Lead Orchestrator + CEO"]:::master

    INDEX["🧭 INDEX.md\nFast-Lookup Navigation Hub\nDocument map · Routing quick-ref\nAgent quick-ref · Authority hierarchy\nOwner: Lead Orchestrator"]:::nav

    CHANGELOG["📜 CHANGELOG.md\nMaster Audit Trail\nEvery change ever made\nOwner: CAE-Audit"]:::audit

    CHG_MGMT["⚙️ CHANGE_MANAGEMENT.md\nPropagation Rules · SoD Matrix\nChangelog format · Versioning\nOwner: CAE-Audit"]:::ops

    DATA_CLASS["🔒 DATA_CLASSIFICATION.md\nT1-T4 Data Tiers\nAgent handling rules · Incident response\nOwner: CISO + CDO-Data"]:::sec

    SYS_MAP["🗺️ SYSTEM_MAP.md\nVisual Flowcharts (Mermaid)\nAll agents · Chains · Routing\nOwner: Lead Orchestrator"]:::ops

    AGENT_STD["📐 AGENT_STANDARDS.md\nDoc standard for all 173 agents\nRequired sections by level · Template\nAudit checklist\nOwner: Lead Orchestrator + CAE-Audit"]:::standard

    DEPT_WF["🔄 DEPARTMENT_WORKFLOWS.md\nIntake · Flow · Output · Handoff\nSLAs · Escalation gates per dept\nAudit-readable operational map\nOwner: COO + Lead Orchestrator"]:::standard

    AUDIT_F["🚨 AUDIT_FINDINGS.md\nOpen + Resolved findings\nCAE-Audit maintained\nOwner: CAE-Audit"]:::audit

    ORG["🏗️ ORG_CHARTS.md\nDetailed dept-level org charts\n17+ departments · Full career ladders\nOwner: Lead Orchestrator"]:::ops

    CLAUDE -->|"start here"| INDEX
    CLAUDE --> CHANGELOG
    CLAUDE --> CHG_MGMT
    CLAUDE --> DATA_CLASS
    CLAUDE --> SYS_MAP
    CLAUDE --> AGENT_STD
    CLAUDE --> DEPT_WF
    CLAUDE --> ORG
    CHANGELOG --> AUDIT_F
    INDEX -.->|"navigates to"| SYS_MAP
    INDEX -.->|"navigates to"| AGENT_STD
    INDEX -.->|"navigates to"| ORG
```

---

## 6. Versioning Convention

```mermaid
flowchart LR
    classDef major fill:#7f1d1d,stroke:#fca5a5,color:#fff,font-weight:bold
    classDef minor fill:#1e40af,stroke:#93c5fd,color:#fff
    classDef patch fill:#065f46,stroke:#6ee7b7,color:#fff
    classDef q fill:#1e3a5f,stroke:#7dd3fc,color:#fff

    CHANGE(["A change occurs"]) --> TYPE{"What type\nof change?"}:::q

    TYPE -->|"Full OS rebuild\nwholesale governance replacement"| MAJ["MAJOR bump\n1.x.x → 2.0.0"]:::major
    TYPE -->|"New dept · new C-suite · new council\ngovernance overhaul · new framework"| MIN["MINOR bump\n1.6.x → 1.7.0"]:::minor
    TYPE -->|"Bug fix · audit remediation\ntypo · propagation fix · chain correction"| PAT["PATCH bump\n1.7.0 → 1.7.1"]:::patch

    MAJ --> LOG(["Update CLAUDE.md header\nLog in CHANGELOG.md\nUpdate SYSTEM_MAP.md header"])
    MIN --> LOG
    PAT --> LOG
```

---

## 7. SESH Data Flow — Infrastructure + Execution Architecture

```mermaid
flowchart TD
    classDef ceo fill:#d4af37,stroke:#996515,color:#000,font-weight:bold
    classDef lo fill:#7c3aed,stroke:#c4b5fd,color:#fff,font-weight:bold
    classDef infra fill:#92400e,stroke:#fbbf24,color:#fff,font-weight:bold
    classDef csuite fill:#1e40af,stroke:#93c5fd,color:#fff,font-weight:bold
    classDef sesh fill:#065f46,stroke:#6ee7b7,color:#fff,font-weight:bold
    classDef worker fill:#0369a1,stroke:#bae6fd,color:#fff
    classDef subworker fill:#bae6fd,stroke:#0284c7,color:#000
    classDef bg fill:#7f1d1d,stroke:#fca5a5,color:#fff,font-weight:bold
    classDef bgworker fill:#991b1b,stroke:#fca5a5,color:#fff
    classDef notes fill:#4a1d96,stroke:#c4b5fd,color:#fff,font-weight:bold
    classDef store fill:#1f2937,stroke:#6b7280,color:#fff

    CEO["👤 CEO"]:::ceo
    LO["🧠 Lead Orchestrator\nIntake · Tier · Route"]:::lo
    CEO -->|input| LO

    %% ── INFRA LAYER ─────────────────────────────────────────
    subgraph INFRA["🔧 Infrastructure Layer"]
        direction LR
        LIB["📚 Librarian\nvector_router.py"]:::infra
        STORE["🗄️ Library\nvector_db + agents/"]:::store
        COMP["🗜️ Compressor\nprompt_cache.py"]:::infra
        IDX["📑 INDEX\nINDEX.md"]:::infra
        LIB <-->|semantic lookup| STORE
        COMP -.->|reads| STORE
    end

    %% ── COO + CPO ───────────────────────────────────────────
    COO["🏢 COO"]:::csuite
    CPO["📦 CPO"]:::csuite
    LO --> COO
    LO --> CPO
    COO <-->|communicate| CPO
    COO <-->|agent lookup proxy| LIB
    CPO -->|compress + cache prompts| COMP
    CPO -->|load context| IDX

    %% ── SESH ────────────────────────────────────────────────
    SESH["⚡ SESH\n1 → N Active C-Suite\nloaded from INDEX"]:::sesh
    IDX -->|instantiates| SESH

    %% ── WORKERS ─────────────────────────────────────────────
    subgraph WORK["👥 Dept Chains (per C-Suite member)"]
        direction LR
        W1["Chain A\nVP→Dir→Mgr→IC"]:::worker
        W2["Chain B\nVP→Dir→Mgr→IC"]:::worker
        W3["Chain C\nVP→Dir→Mgr→IC"]:::worker
    end
    SESH -->|spawns| WORK

    %% ── SUB-AGENTS ──────────────────────────────────────────
    subgraph SUBS["🔩 Sub-Agents (0–5 per worker)"]
        direction LR
        SW1["0–5 sub-agents"]:::subworker
        SW2["0–5 sub-agents"]:::subworker
    end
    WORK -->|spawns 0–5| SUBS

    %% ── RESULTS UP ──────────────────────────────────────────
    SUBS -->|results up| WORK
    WORK -->|results up| SESH
    SESH -->|synthesized output| LO
    LO -->|final response| CEO

    %% ── BACKGROUND PARALLEL ─────────────────────────────────
    subgraph BG["🔄 Background / Parallel"]
        direction LR
        CAO["🔍 CAE-Audit\nChief Audit Officer"]:::bg
        CCU["🧹 Custodian\nChief Custodian Officer"]:::bg
        IA["Audit sub-agents ×N"]:::bgworker
        CUA["Custodian sub-agents ×N"]:::bgworker
        CAO --> IA
        CCU --> CUA
    end
    SESH -.->|audit signals| CAO
    WORK -.->|audit trail| CAO
    WORK -.->|prompt hygiene| CCU

    %% ── CHIEF NOTES OFFICER ─────────────────────────────────
    CNO["📝 Chief Notes Officer\nHaiku · passive · always-on"]:::notes
    LO -.->|notes| CNO
    SESH -.->|notes| CNO
    WORK -.->|notes| CNO
    SUBS -.->|notes| CNO
    BG -.->|flags| CNO
```

---

## 8. Model Selection — Decision Tree

> Runs before every agent invocation. Goal: use the cheapest model that can do the job well.

```mermaid
flowchart TD
    classDef q fill:#1e3a5f,stroke:#7dd3fc,color:#fff
    classDef haiku fill:#065f46,stroke:#6ee7b7,color:#fff
    classDef sonnet fill:#1e40af,stroke:#93c5fd,color:#fff,font-weight:bold
    classDef opus fill:#7f1d1d,stroke:#fca5a5,color:#fff,font-weight:bold
    classDef ollama fill:#4a1942,stroke:#d8b4fe,color:#fff
    classDef rule fill:#92400e,stroke:#fbbf24,color:#fff

    START(["Task arrives\nfor agent invocation"])

    START --> PL{"prefer_local\nmode OR Tier 0?"}:::q
    PL -->|YES| OLL{"Needs\ntool calling?"}:::q
    PL -->|NO| TIER{"Task\ncomplexity?"}:::q

    OLL -->|NO tools needed| OLL_NT["Ollama — text only\ngemma3:1b  (trivial)\ngemma3:4b  (simple)\ndeepseek-r1 (reasoning)\nmistral:7b  (general)"]:::ollama
    OLL -->|tools needed| OLL_T["Ollama — tool-capable\nllama3.2:3b  (Tier 0–1)\nllama3.1:latest  (Tier 1–2)\nqwen2.5-coder:7b  (code)\ndeepseek-coder-v2:16b  (complex code)"]:::ollama

    TIER -->|"Trivial\nformat · classify · translate\nspell-check"| H0["Haiku\nTier 0"]:::haiku
    TIER -->|"Simple\nexplain · summarize\nextract · Q&A"| H1["Haiku\nTier 1"]:::haiku
    TIER -->|"Standard\nanalyze · implement\nresearch · debug"| S2["Sonnet\nTier 2"]:::sonnet
    TIER -->|"Complex\narchitecture · multi-file\nsecurity review"| S3["Sonnet\nTier 3"]:::sonnet
    TIER -->|"Critical\ngovernance · legal\ncompliance · incidents"| O4["Opus\nTier 4"]:::opus

    H0 --> RULE["Rule: Always pass model= to Agent tool\nNever let agents default to Sonnet\nwhen Haiku is sufficient"]:::rule
    H1 --> RULE
    S2 --> RULE
    S3 --> RULE
    O4 --> RULE
```

---

## 9. Governance Gate Flow — Step 0 Blocking Logic

> Every non-Tier-0 task runs this before any department agent is invoked.

```mermaid
flowchart TD
    classDef input fill:#d4af37,stroke:#996515,color:#000,font-weight:bold
    classDef gate fill:#065f46,stroke:#6ee7b7,color:#fff
    classDef block fill:#7f1d1d,stroke:#fca5a5,color:#fff,font-weight:bold
    classDef pass fill:#1e40af,stroke:#93c5fd,color:#fff
    classDef q fill:#1e3a5f,stroke:#7dd3fc,color:#fff

    IN(["Non-Tier-0 Task"]):::input

    IN --> G1{"Spans 2+\ndepartments?"}:::q
    G1 -->|YES| COO_G["COO — decompose first\nBlocking gate"]:::block
    G1 -->|NO| G2{"New AI agent\nuse case or workflow?"}:::q
    COO_G -->|"Decomposed into dept tasks"| G2

    G2 -->|YES| AIC_G["AI & Automation Council\napproval required\nBlocking gate"]:::block
    G2 -->|NO| G3{"Tier 2+ task?"}:::q
    AIC_G -->|"Council PASS"| G3

    G3 -->|YES| CISO_G["CISO formal invocation\nPASS / CONDITIONAL / FAIL verdict\nBlocking gate"]:::block
    G3 -->|NO| G4{"New open-source\ntool or library?"}:::q
    CISO_G -->|"CISO PASS or CONDITIONAL"| G4

    G4 -->|YES| GCL_G["GC-Legal license review\nBlocking for deployment\n(not exploration)"]:::block
    G4 -->|NO| G5{"New MCP server\nor external service?"}:::q
    GCL_G -->|"License cleared"| G5

    G5 -->|YES| CISO_G2["CISO review\nblocks activation\n(config write = Tier 1 ok)"]:::block
    G5 -->|NO| G6{"Structural agent\nchange? (Five-File Rule)"}:::q
    CISO_G2 -->|"Activation cleared"| G6

    G6 -->|YES| FF["Five-File Rule check\nagent · parent · CLAUDE.md\nCHANGELOG.md · SYSTEM_MAP.md\nAll 5 required"]:::block
    G6 -->|NO| EXEC["Proceed to\ndomain routing"]:::pass
    FF -->|"All 5 updated"| EXEC

    CISO_G -->|"CISO FAIL"| STOP(["STOP\nEscalate to CEO"]):::block
```

---

## Update Log

| Version | Date | Change |
|---------|------|--------|
| 1.7.0 | 2026-03-19 | Initial creation. 8 diagrams covering authority, pipeline, routing, risk tiers, dept overview, all 14 dept chains, versioning, compliance. |
| 1.8.0 | 2026-03-19 | Full rebuild. Added color-coded classDef styling to all diagrams. Replaced individual dept chain diagrams with unified Family Tree (all 100+ agents in one graph). Improved node shapes, edge labels, and layout. |
| 1.8.1 | 2026-03-19 | Governance doc layer expanded. AGENT_STANDARDS.md and DEPARTMENT_WORKFLOWS.md added to Documentation Layer diagram. ~42 thin agents upgraded across Security, Finance, Legal, Compliance, Audit, Product, GTM, Investments, Data, Strategy, and Design departments. |
| 1.10.0 | 2026-03-25 | Gaming Intelligence department added. Dir-Gaming + Patch-Analyst + Meta-Coach + Game-Researcher added to Family Tree. Gaming domain added to Routing Decision Tree. |
| 1.11.1 | 2026-03-27 | Custodian added to Prompt Engineering subgraph (Family Tree diagram). |
| 1.13.0 | 2026-03-28 | Chief-Notes-Officer added to Family Tree. New Section 7: SESH Data Flow diagram — Librarian/Library/Compressor/INDEX infra layer, COO↔CPO↔Librarian/Compressor access pattern, SESH instantiation from INDEX, workers/sub-agents, background CAE-Audit+Custodian, CNO note tap. |
| 1.13.1 | 2026-03-28 | Section 5b: INDEX.md added to Documentation Layer diagram (was missing despite being the primary nav hub); ORG_CHARTS.md added; agent count corrected to 173; navigation edges added. Section 3: MasterPlanner gate added to routing decision tree (multi-file/multi-agent path now shows STOP→plan→CEO confirm loop). New Section 8: Model Selection Decision Tree (Haiku/Sonnet/Opus/Ollama with tier mapping and tool-support branching). New Section 9: Governance Gate Flow (Step 0 full blocking logic as a visual flowchart — COO→AI Council→CISO→GC-Legal→CISO MCP→Five-File Rule). |
