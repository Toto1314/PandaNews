#!/usr/bin/env python3
"""
AI OS Skill Tree — Inverted Skyrim-style agent tree renderer
Reads agent .md files dynamically from ~/.claude/agents/
IC agents at top (entry), C-suite at bottom (capstone)
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime

# Force UTF-8 output on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ── Paths ────────────────────────────────────────────────────
AGENTS_DIR = Path.home() / ".claude" / "agents"
SKILL_DIR  = Path.home() / ".claude" / "skills" / "skill-tree"
STATE_FILE = SKILL_DIR / "state.json"

# ── ANSI Colors ──────────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
GOLD   = "\033[93m"
CYAN   = "\033[96m"
GREEN  = "\033[92m"
RED    = "\033[91m"
GRAY   = "\033[90m"

# ── Department display metadata ──────────────────────────────
DEPT_META = {
    "security":    ("🔐", "Security"),
    "engineering": ("💻", "Engineering"),
    "product":     ("📦", "Product"),
    "finance":     ("💰", "Finance"),
    "legal":       ("⚖️",  "Legal / GRC"),
    "gtm":         ("🚀", "GTM / Revenue"),
    "investments": ("📈", "Investments"),
    "data":        ("🗄️",  "Data & Analytics"),
    "devops":      ("⚙️",  "DevOps / Platform"),
    "ai-ml":       ("🤖", "AI / ML"),
    "design":      ("🎨", "Design / CX"),
    "strategy":    ("♟️",  "Strategy"),
    "prompt-eng":  ("✍️",  "Prompt Engineering"),
    "research":    ("🔬", "Research"),
    "gaming":      ("🎮", "Gaming"),
    "hr":          ("👥", "HR / People"),
    "comms":       ("📢", "Communications"),
    "pmo":         ("📋", "PMO"),
    "audit":       ("🔍", "Internal Audit"),
    "governance":  ("🛡️",  "Governance"),
    "c-suite":     ("👔", "C-Suite"),
    "pipeline":    ("⚡", "Pipeline"),
}

# ── Level detection from filename ───────────────────────────
def get_level(stem: str) -> int:
    s = stem.lower()
    # C-suite capstones
    if re.search(r'^(ciso|cto|cpo|cfo|coo|cdo|cio|cro|caio|ciro|cpro|cplato|chro|cso|cco|gc-legal|cae-audit|chief-of-staff)$', s):
        return 7
    if s.startswith("vp-") or s.startswith("vp "):
        return 6
    if "principal" in s:
        return 5
    if s.startswith("dir-") or "director" in s:
        return 4
    if s.startswith("sr-") or "senior" in s:
        return 3
    # Mid-level: named roles without qualifiers
    if any(x in s for x in ["manager", "engineer", "analyst", "architect", "specialist",
                              "researcher", "scientist", "strategist", "controller", "partner",
                              "executive", "recruiter", "designer", "auditor"]):
        return 2
    # Entry
    if any(x in s for x in ["associate", "sdr", "bdr", "junior"]):
        return 1
    return 3  # default to mid

LEVEL_LABELS = {1: "Entry", 2: "Mid", 3: "Senior", 4: "Director",
                5: "Principal", 6: "VP", 7: "C-Suite"}

def level_label(level: int) -> str:
    return LEVEL_LABELS.get(level, "")

# ── Agent display name from file ─────────────────────────────
def get_display_name(filepath: Path) -> str:
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
        # Frontmatter name field
        m = re.search(r'^name:\s*(.+)$', content[:600], re.MULTILINE)
        if m:
            return m.group(1).strip().strip('"')
        # First H1
        m = re.search(r'^#\s+(.+)$', content[:1200], re.MULTILINE)
        if m:
            raw = m.group(1)
            # Strip markdown bold/italic and trim
            raw = re.sub(r'[*_`]', '', raw).strip()
            # Strip non-ASCII (emoji in H1)
            clean = ''.join(c for c in raw if ord(c) < 128).strip()
            return clean if len(clean) > 2 else filepath.stem
    except Exception:
        pass
    return filepath.stem

# ── Load / save state ────────────────────────────────────────
def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"activated": [], "achievements": [], "sessions": 0, "last_session": None}

def save_state(state: dict):
    SKILL_DIR.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

# ── Scan agents directory ────────────────────────────────────
def scan_agents() -> dict:
    """Returns {dept: [(level, stem, display_name), ...]} sorted IC→C-suite"""
    tree = {}
    if not AGENTS_DIR.exists():
        print(f"{RED}Agents directory not found: {AGENTS_DIR}{RESET}")
        return tree

    for dept_dir in sorted(AGENTS_DIR.iterdir()):
        if not dept_dir.is_dir() or dept_dir.name.startswith("."):
            continue
        dept = dept_dir.name
        agents = []
        for f in sorted(dept_dir.glob("*.md")):
            level = get_level(f.stem)
            display = get_display_name(f)
            agents.append((level, f.stem, display))
        agents.sort(key=lambda x: (x[0], x[1]))  # sort by level then name
        if agents:
            tree[dept] = agents

    return tree

# ── Achievement engine ───────────────────────────────────────
GLOBAL_ACHIEVEMENTS = {
    "first_contact":    ("First Contact",        "Activated your first agent"),
    "batch_10":         ("Batch Commander",       "10+ agents active — crosses Tier 2 batch escalation threshold"),
    "batch_50":         ("Half Stack",            "50+ agents active"),
    "century":          ("Centurion",             "100 agents activated"),
    "pipeline_master":  ("⚡ Pipeline Master",    "Full scout → architect → builder → validator chain active"),
    "csuite_assembled": ("👔 C-Suite Assembled",  "All C-suite executives active"),
}

def check_achievements(state: dict, tree: dict) -> list:
    activated = set(state.get("activated", []))
    earned    = set(state.get("achievements", []))
    new = []

    def earn(ach_id, name, desc):
        if ach_id not in earned:
            new.append((ach_id, name, desc))

    if activated:
        earn("first_contact", "First Contact", "Activated your first agent")

    if len(activated) >= 10:
        earn("batch_10", "Batch Commander", "10+ agents active")

    if len(activated) >= 50:
        earn("batch_50", "Half Stack", "50+ agents active")

    if len(activated) >= 100:
        earn("century", "Centurion", "100 agents activated")

    # Pipeline master
    pipeline = {a[1] for a in tree.get("pipeline", [])}
    if pipeline and pipeline.issubset(activated):
        earn("pipeline_master", "⚡ Pipeline Master", "Full pipeline chain active")

    # C-suite assembled
    csuite = {a[1] for a in tree.get("c-suite", [])}
    if csuite and csuite.issubset(activated):
        earn("csuite_assembled", "👔 C-Suite Assembled", "All C-suite executives active")

    # Full branch per department
    for dept, agents in tree.items():
        stems = {a[1] for a in agents}
        if len(stems) >= 2 and stems.issubset(activated):
            emoji, dname = DEPT_META.get(dept, ("🏆", dept.title()))
            earn(f"full_{dept}", f"{emoji} Full Branch: {dname}", f"All {len(stems)} agents in {dname} activated")

    return new

# ── Progress bar ─────────────────────────────────────────────
def bar(count: int, total: int, width: int = 12) -> str:
    if total == 0:
        return GRAY + "░" * width + RESET
    filled = round(count / total * width)
    return GOLD + "█" * filled + RESET + GRAY + "░" * (width - filled) + RESET

# ── Commands ─────────────────────────────────────────────────

def cmd_view(_args):
    state = load_state()
    tree  = scan_agents()
    activated = set(state.get("activated", []))

    total_agents = sum(len(v) for v in tree.values())
    total_active = sum(1 for dept in tree.values() for a in dept if a[1] in activated)
    earned_count = len(state.get("achievements", []))

    W = 66
    print()
    print(GOLD + "╔" + "═" * (W - 2) + "╗" + RESET)

    title = "✦  AI OS SKILL TREE  ✦"
    pad = (W - 2 - len(title)) // 2
    print(GOLD + "║" + " " * pad + BOLD + title + RESET + GOLD +
          " " * (W - 2 - pad - len(title)) + "║" + RESET)

    stats = f"{len(tree)} branches · {total_agents} agents · {total_active} active · {earned_count} achievements"
    pad2 = (W - 2 - len(stats)) // 2
    print(GOLD + "║" + " " * pad2 + CYAN + stats + RESET + GOLD +
          " " * (W - 2 - pad2 - len(stats)) + "║" + RESET)

    print(GOLD + "╚" + "═" * (W - 2) + "╝" + RESET)
    print()
    print(DIM + "  Inverted tree: IC agents at top · C-suite capstones at bottom" + RESET)
    print()

    for dept, agents in sorted(tree.items()):
        emoji, dname = DEPT_META.get(dept, ("📁", dept.title()))
        dept_active = sum(1 for a in agents if a[1] in activated)
        dept_total  = len(agents)
        pct = int(dept_active / dept_total * 100) if dept_total else 0

        # Department header
        sep = "─" * 4
        label = f" {emoji} {BOLD}{dname}{RESET} "
        print(CYAN + sep + label + CYAN + "─" * max(0, 46 - len(dname)) + RESET)

        for i, (level, stem, display) in enumerate(agents):
            is_active   = stem in activated
            is_last     = (i == len(agents) - 1)
            is_capstone = (level >= 7)

            connector = "└── " if is_last else "├── "
            star      = (GOLD + "★" + RESET) if is_active else (GRAY + "☆" + RESET)
            name_str  = (GREEN + BOLD + display + RESET) if is_active else (GRAY + display + RESET)
            lvl_tag   = DIM + f" [{level_label(level)}]" + RESET
            cap_tag   = (GOLD + BOLD + "  ◄ CAPSTONE" + RESET) if is_capstone else ""

            print(f"  {connector}{star}  {name_str}{lvl_tag}{cap_tag}")

        # Branch progress
        b = bar(dept_active, dept_total)
        print(f"  {b}  {CYAN}{dept_active}/{dept_total}{RESET} ({pct}%)")
        print()

    # Overall footer
    overall = bar(total_active, total_agents, 20)
    overall_pct = int(total_active / total_agents * 100) if total_agents else 0
    print(GOLD + "─" * (W - 2) + RESET)
    print(f"  Overall  {overall}  {CYAN}{total_active}/{total_agents}{RESET}  ({overall_pct}%)")

    if earned_count:
        print(f"  Achievements earned: {GOLD}{earned_count}{RESET}")
    print()


def cmd_activate(names: list):
    state = load_state()
    tree  = scan_agents()
    all_stems = {a[1] for dept in tree.values() for a in dept}

    activated    = set(state.get("activated", []))
    newly_active = []

    for name in names:
        matches = [s for s in all_stems if name.lower() in s.lower()]
        if not matches:
            print(f"{RED}  ✗  No agent matching '{name}'{RESET}")
            continue
        for m in sorted(matches):
            if m not in activated:
                activated.add(m)
                newly_active.append(m)
                level = get_level(m)
                print(f"  {GOLD}★{RESET}  {GREEN}{m}{RESET}  {DIM}[{level_label(level)}]{RESET}")
            else:
                print(f"  {GRAY}already active: {m}{RESET}")

    state["activated"] = sorted(activated)
    state["last_session"] = datetime.now().isoformat()
    state["sessions"] = state.get("sessions", 0) + (1 if newly_active else 0)

    # Award achievements
    new_ach = check_achievements(state, tree)
    for ach_id, ach_name, ach_desc in new_ach:
        if ach_id not in state.get("achievements", []):
            state.setdefault("achievements", []).append(ach_id)
            print(f"\n  {GOLD}🏆 ACHIEVEMENT UNLOCKED: {BOLD}{ach_name}{RESET}")
            print(f"     {DIM}{ach_desc}{RESET}")

    save_state(state)
    total = len(activated)
    print(f"\n  {CYAN}{len(newly_active)} newly activated · {total} total active{RESET}")


def cmd_achievements(_args=None):
    state = load_state()
    tree  = scan_agents()
    earned = set(state.get("achievements", []))

    # Build full achievement list
    defs = dict(GLOBAL_ACHIEVEMENTS)
    for dept, agents in tree.items():
        emoji, dname = DEPT_META.get(dept, ("🏆", dept.title()))
        defs[f"full_{dept}"] = (f"{emoji} Full Branch: {dname}", f"All {len(agents)} {dname} agents active")

    earned_count = sum(1 for k in defs if k in earned)
    total_count  = len(defs)

    print()
    print(GOLD + f"  🏆  ACHIEVEMENTS  {earned_count}/{total_count}" + RESET)
    print(GOLD + "  " + "═" * 50 + RESET)
    print()

    for ach_id, (name, desc) in defs.items():
        if ach_id in earned:
            print(f"  {GOLD}★  {BOLD}{name}{RESET}")
            print(f"     {GREEN}✓ Earned{RESET}  {DIM}{desc}{RESET}")
        else:
            print(f"  {GRAY}☆  {name}")
            print(f"     Locked — {desc}{RESET}")
        print()


def cmd_json(_args=None):
    state = load_state()
    tree  = scan_agents()
    activated = set(state.get("activated", []))

    output = {
        "version":   "1.13.1",
        "generated": datetime.now().isoformat(),
        "summary": {
            "total_agents":  sum(len(v) for v in tree.values()),
            "active_agents": sum(1 for dept in tree.values() for a in dept if a[1] in activated),
            "departments":   len(tree),
            "achievements":  state.get("achievements", []),
        },
        "tree": {}
    }

    for dept, agents in sorted(tree.items()):
        emoji, dname = DEPT_META.get(dept, ("📁", dept))
        output["tree"][dept] = {
            "name":   dname,
            "emoji":  emoji,
            "agents": [
                {
                    "id":          stem,
                    "display":     display,
                    "level":       level,
                    "level_label": level_label(level),
                    "active":      stem in activated,
                    "capstone":    level >= 7,
                    "port":        "locked" if level >= 7 else "private",
                }
                for level, stem, display in agents
            ]
        }

    print(json.dumps(output, indent=2, ensure_ascii=False))


def cmd_reset(_args=None):
    if STATE_FILE.exists():
        STATE_FILE.unlink()
        print(f"{RED}  State reset. All activations and achievements cleared.{RESET}")
    else:
        print("  Nothing to reset.")


# ── Entry point ──────────────────────────────────────────────
COMMANDS = {
    "view":         cmd_view,
    "activate":     cmd_activate,
    "achievements": cmd_achievements,
    "json":         cmd_json,
    "reset":        cmd_reset,
}

if __name__ == "__main__":
    args = sys.argv[1:]
    cmd  = args[0].lower() if args else "view"

    if cmd in COMMANDS:
        COMMANDS[cmd](args[1:])
    elif not args:
        cmd_view([])
    else:
        # Assume everything is an activate target
        cmd_activate(args)
