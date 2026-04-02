#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
"""
AI OS Integration Registry Viewer
Backstage-style catalog for all MCPs, APIs, Skills, and web allowlist entries.

Usage:
  python registry.py                    # full catalog
  python registry.py --type mcp        # MCPs only
  python registry.py --type api        # APIs only
  python registry.py --type skill      # Skills only
  python registry.py --type web        # Web allowlist only
  python registry.py --search langsmith # search by name/tag/description
  python registry.py --status active   # filter by status
  python registry.py --summary         # one-line summary per section
"""

import sys
import yaml
from pathlib import Path

REGISTRY_PATH = Path(__file__).parent / "registry.yaml"

# ANSI colors
RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
RED    = "\033[31m"
CYAN   = "\033[36m"
BLUE   = "\033[34m"
GRAY   = "\033[90m"

STATUS_COLOR = {
    "active":    GREEN,
    "available": YELLOW,
    "inactive":  GRAY,
    "blocked":   RED,
    "planned":   CYAN,
    "manual":    BLUE,
}

def status_badge(status: str) -> str:
    color = STATUS_COLOR.get(status, GRAY)
    return f"{color}[{status.upper()}]{RESET}"

def tag_str(tags: list) -> str:
    if not tags:
        return ""
    return GRAY + "  " + " ".join(f"#{t}" for t in tags) + RESET

def separator(char="─", width=60) -> str:
    return GRAY + char * width + RESET

def print_mcp(mcp: dict):
    print(f"\n  {BOLD}{mcp['name']}{RESET}  {status_badge(mcp['status'])}")
    print(f"  {mcp['description']}")
    if mcp.get("credentials"):
        print(f"  {DIM}credentials: {mcp['credentials']}{RESET}")
    if mcp.get("agents_using"):
        agents = ", ".join(mcp["agents_using"])
        print(f"  {DIM}agents: {agents}{RESET}")
    if mcp.get("tools"):
        tools = ", ".join(mcp["tools"])
        print(f"  {DIM}tools: {tools}{RESET}")
    print(tag_str(mcp.get("tags", [])))

def print_api(api: dict):
    print(f"\n  {BOLD}{api['name']}{RESET}  {status_badge(api['status'])}")
    print(f"  {api['description']}")
    creds = api.get("credentials", {})
    if isinstance(creds, dict):
        if creds.get("env_var"):
            print(f"  {DIM}env: {creds['env_var']}{RESET}")
        if creds.get("location"):
            print(f"  {DIM}location: {creds['location']}{RESET}")
        if creds.get("note"):
            print(f"  {YELLOW}⚠ {creds['note']}{RESET}")
    if api.get("data_leaves_machine"):
        data_sent = api.get("data_sent", "unspecified")
        print(f"  {YELLOW}⬆ sends to cloud: {data_sent}{RESET}")
    if api.get("agents_using"):
        agents = ", ".join(str(a) for a in api["agents_using"])
        print(f"  {DIM}agents: {agents}{RESET}")
    print(tag_str(api.get("tags", [])))

def print_skill(skill: dict):
    count = skill.get("usage_count", 0)
    count_str = f"{GREEN}{count}x{RESET}" if count > 5 else (f"{YELLOW}{count}x{RESET}" if count > 0 else f"{GRAY}0x{RESET}")
    print(f"\n  {BOLD}{skill['name']}{RESET}  {count_str}  {DIM}{skill.get('trigger', '')}{RESET}")
    print(f"  {skill['description']}")
    print(tag_str(skill.get("tags", [])))

def print_web(domain: dict):
    print(f"\n  {BOLD}{domain['domain']}{RESET}")
    print(f"  {domain['purpose']}")
    print(tag_str(domain.get("tags", [])))

def print_summary(data: dict):
    mcps     = data.get("mcps", [])
    apis     = data.get("apis", [])
    skills   = data.get("skills", [])
    web      = data.get("web_allowlist", [])

    active_mcps   = [m for m in mcps if m["status"] == "active"]
    avail_mcps    = [m for m in mcps if m["status"] == "available"]
    active_apis   = [a for a in apis if a["status"] == "active"]
    cloud_apis    = [a for a in apis if a.get("data_leaves_machine")]
    used_skills   = [s for s in skills if s.get("usage_count", 0) > 0]
    unused_skills = [s for s in skills if s.get("usage_count", 0) == 0]

    print(f"\n{BOLD}AI OS Integration Registry — Summary{RESET}")
    print(separator())
    print(f"  {BOLD}MCPs{RESET}      {GREEN}{len(active_mcps)} active{RESET}  {YELLOW}{len(avail_mcps)} available{RESET}  ({len(mcps)} total)")
    print(f"  {BOLD}APIs{RESET}      {GREEN}{len(active_apis)} active{RESET}  ({len(apis)} total)  {YELLOW}⬆ {len(cloud_apis)} send data to cloud{RESET}")
    print(f"  {BOLD}Skills{RESET}    {GREEN}{len(used_skills)} used{RESET}  {GRAY}{len(unused_skills)} never used{RESET}  ({len(skills)} total)")
    print(f"  {BOLD}Domains{RESET}   {len(web)} allowlisted")
    print(separator())

    print(f"\n  {BOLD}Active MCPs:{RESET}")
    for m in active_mcps:
        print(f"    {GREEN}●{RESET} {m['name']} — {m['description'][:60]}...")

    print(f"\n  {BOLD}Active APIs:{RESET}")
    for a in active_apis:
        cloud = f" {YELLOW}⬆ cloud{RESET}" if a.get("data_leaves_machine") else ""
        print(f"    {GREEN}●{RESET} {a['name']}{cloud} — {a['description'][:50]}...")

    print(f"\n  {BOLD}Most Used Skills:{RESET}")
    top = sorted(used_skills, key=lambda s: s.get("usage_count", 0), reverse=True)[:8]
    for s in top:
        bar_len = min(s["usage_count"], 15)
        bar = "█" * bar_len + "░" * (15 - bar_len)
        print(f"    {CYAN}{s['name']:<20}{RESET} {bar} {s['usage_count']}x")

    print(f"\n  {BOLD}Available MCPs (not yet activated):{RESET}")
    for m in avail_mcps:
        creds = m.get("credentials", "")
        print(f"    {YELLOW}○{RESET} {m['name']:<15} {GRAY}{creds[:60]}{RESET}")

    print()

def search_entries(data: dict, query: str) -> dict:
    q = query.lower()
    results = {}
    for section, entries in data.items():
        if section == "meta":
            continue
        matches = []
        for e in entries:
            text = f"{e.get('name','')} {e.get('description','')} {' '.join(e.get('tags',[]))}".lower()
            if q in text:
                matches.append(e)
        if matches:
            results[section] = matches
    return results

def filter_by_status(data: dict, status: str) -> dict:
    results = {}
    for section, entries in data.items():
        if section == "meta":
            continue
        matches = [e for e in entries if e.get("status", "").lower() == status.lower()]
        if matches:
            results[section] = matches
    return results

def print_section(section: str, entries: list):
    SECTION_LABELS = {
        "mcps": "MCP SERVERS",
        "apis": "EXTERNAL APIs",
        "skills": "SKILLS",
        "web_allowlist": "WEB ALLOWLIST",
    }
    SECTION_PRINTERS = {
        "mcps": print_mcp,
        "apis": print_api,
        "skills": print_skill,
        "web_allowlist": print_web,
    }
    label = SECTION_LABELS.get(section, section.upper())
    printer = SECTION_PRINTERS.get(section, lambda e: print(f"  {e}"))

    print(f"\n{BOLD}{CYAN}{label}{RESET}  {GRAY}({len(entries)} entries){RESET}")
    print(separator())
    for entry in entries:
        printer(entry)
    print()

def main():
    args = sys.argv[1:]

    if not REGISTRY_PATH.exists():
        print(f"{RED}Registry not found: {REGISTRY_PATH}{RESET}")
        sys.exit(1)

    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # parse flags
    type_filter   = None
    search_query  = None
    status_filter = None
    show_summary  = False

    i = 0
    while i < len(args):
        if args[i] == "--type" and i + 1 < len(args):
            type_filter = args[i + 1]; i += 2
        elif args[i] == "--search" and i + 1 < len(args):
            search_query = args[i + 1]; i += 2
        elif args[i] == "--status" and i + 1 < len(args):
            status_filter = args[i + 1]; i += 2
        elif args[i] == "--summary":
            show_summary = True; i += 1
        else:
            i += 1

    TYPE_MAP = {
        "mcp": "mcps",
        "api": "apis",
        "skill": "skills",
        "skills": "skills",
        "web": "web_allowlist",
    }

    meta = data.get("meta", {})
    print(f"\n{BOLD}AI OS Integration Registry{RESET}  {GRAY}v{meta.get('version','?')} · updated {meta.get('updated','?')}{RESET}")

    if show_summary:
        print_summary(data)
        return

    if search_query:
        results = search_entries(data, search_query)
        if not results:
            print(f"{YELLOW}No results for '{search_query}'{RESET}")
        else:
            for section, entries in results.items():
                print_section(section, entries)
        return

    if status_filter:
        results = filter_by_status(data, status_filter)
        if not results:
            print(f"{YELLOW}No entries with status '{status_filter}'{RESET}")
        else:
            for section, entries in results.items():
                print_section(section, entries)
        return

    if type_filter:
        key = TYPE_MAP.get(type_filter.lower())
        if not key or key not in data:
            print(f"{RED}Unknown type '{type_filter}'. Use: mcp, api, skill, web{RESET}")
            sys.exit(1)
        print_section(key, data[key])
        return

    # default: full catalog with summary header
    print_summary(data)
    for section in ["mcps", "apis", "skills", "web_allowlist"]:
        if section in data:
            print_section(section, data[section])

if __name__ == "__main__":
    main()
