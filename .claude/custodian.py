"""
Custodian — AI OS Maintenance & Optimization Engine
====================================================
Sits between the Librarians (vector_router) and the Bridge (prompt_cache).
Keeps agent prompts lean, storage clean, and memory current.

Architecture position: Clerk → Bridge ← [Custodian] → Librarians
                                             ↓
                                         Memory System

CLI usage:
    python custodian.py report              # Full maintenance report (default)
    python custodian.py plan                # Generate cleaning plan for CPrO/Dir-PromptQA review
    python custodian.py cycle               # Same as plan (dry-run, requires approval)
    python custodian.py cycle --live        # Execute approved cleaning plan (CPrO sign-off required)
    python custodian.py analyze             # Rank all agents by bloat score
    python custodian.py analyze <AgentName> # Analyze one specific agent
    python custodian.py sections <Name>     # Per-section token breakdown for an agent
    python custodian.py graph               # Print org graph (Reports-to / Manages)
    python custodian.py graph --format json # Org graph as JSON
    python custodian.py cache               # Audit prompt cache (dry run)
    python custodian.py cache --live        # Clean stale/orphaned cache entries
    python custodian.py memory              # Audit memory files
    python custodian.py patterns            # Show usage patterns from run log
    python custodian.py warm                # Warm prompt cache for all agents
    python custodian.py changelog           # Preview changelog compaction (dry run)
    python custodian.py changelog --live    # Compact CHANGELOG.md → cold storage zip
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

# yaml is stdlib-compatible; used for frontmatter parsing
try:
    import yaml as _yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False

# ── Tree-sitter initialization (graceful degradation to regex) ─────────────────

_TS_AVAILABLE = False
_ts_parser: Optional[Any] = None

try:
    import tree_sitter_markdown as tsm  # type: ignore
    from tree_sitter import Language, Parser as _TSParser  # type: ignore
    _ts_lang = Language(tsm.language())
    _ts_parser = _TSParser(_ts_lang)
    _TS_AVAILABLE = True
except Exception:
    pass  # Regex fallback activates automatically


# ── Paths ──────────────────────────────────────────────────────────────────────

CLAUDE_DIR = Path.home() / ".claude"
AGENTS_DIR = CLAUDE_DIR / "agents"
PROMPT_CACHE_DIR = CLAUDE_DIR / "prompt_cache"
MEMORY_DIR = CLAUDE_DIR / "projects" / "C--Users-atank" / "memory"
RUN_LOG = CLAUDE_DIR / "run_log.jsonl"
REPORT_PATH = CLAUDE_DIR / "custodian_report.md"
COLD_STORAGE_DIR = CLAUDE_DIR / "cold_storage"
CHANGELOG_PATH = CLAUDE_DIR / "CHANGELOG.md"

# Entries older than this are compacted to cold storage
CHANGELOG_RETAIN_DAYS = 60

# ── Model token budgets (target max for each model tier) ───────────────────────

MODEL_BUDGETS: dict[str, int] = {
    "haiku": 600,
    "claude-haiku-4-5-20251001": 600,
    "sonnet": 2000,
    "claude-sonnet-4-6": 2000,
    "opus": 4500,
    "claude-opus-4-6": 4500,
}

# Governs which model budget key to normalize to
MODEL_TIER_MAP: dict[str, str] = {
    "claude-haiku-4-5-20251001": "haiku",
    "claude-sonnet-4-6": "sonnet",
    "claude-opus-4-6": "opus",
}

# ── Governance boilerplate that CLAUDE.md already provides ─────────────────────

INHERITED_PATTERNS = [
    r"COSO\s*[·|·]\s*SOC\s*2",
    r"NIST\s*CSF",
    r"SOX\s*[·|·]\s*COBIT",
    r"scout before you touch",
    r"minimal changes only",
    r"one task at a time",
    r"RACI\s+(Framework|roles)",
]

# Sections every agent should have (positive signal)
REQUIRED_SECTIONS = {
    "negative constraints",
    "escalation rules",
    "output format",
}

# Sections that are compressible candidates
COMPRESSIBLE_SECTIONS = {
    "background",
    "about",
    "notes",
    "overview",
    "context",
    "additional context",
}


# ── Data classes ───────────────────────────────────────────────────────────────

@dataclass
class AgentSection:
    """A single section from an agent markdown file (tree-sitter parsed)."""
    title: str            # Header text stripped of # marks
    level: int            # Heading depth: 1=h1, 2=h2, 3=h3, ...
    content: str          # Full section body including nested content
    token_count: int      # Estimated tokens for this section
    has_code_blocks: bool # True if this section contains fenced code blocks
    line_start: int       # 0-indexed line number where heading appears


@dataclass
class AgentAST:
    """Fully parsed representation of an agent markdown file."""
    name: str
    version: str
    model: str
    description: str
    tools: list[str]
    frontmatter_raw: dict           # Full parsed YAML dict
    sections: list[AgentSection]   # All sections at all depths (flat list)
    reports_to: list[str]          # Parsed from **Reports to:** / **Reports To:** line
    manages: list[str]             # Parsed from **Manages:** line
    parse_error: Optional[str]     # None if clean; error message if parse failed


@dataclass
class AgentAnalysis:
    name: str
    file_path: Path
    model: str
    model_tier: str          # normalized: haiku | sonnet | opus
    estimated_tokens: int
    budget: int
    over_budget: bool
    bloat_score: float       # 0.0 = lean, 1.0 = very bloated
    issues: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    missing_sections: list[str] = field(default_factory=list)


@dataclass
class UsagePattern:
    agent: str
    invocation_count: int
    avg_tier: float
    last_used: str
    models_used: Counter = field(default_factory=Counter)


@dataclass
class CacheAudit:
    valid: int
    stale: list[str]
    orphaned: list[str]

    @property
    def total_issues(self) -> int:
        return len(self.stale) + len(self.orphaned)


# ── Token estimation ────────────────────────────────────────────────────────────

def _estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token (conservative for English prose)."""
    return max(1, len(text) // 4)


# ── Tree-sitter parsing layer ──────────────────────────────────────────────────

def _ts_heading_level(heading_node: Any) -> int:
    """Extract heading level (1–6) from an atx_heading or setext_heading node."""
    for child in heading_node.children:
        t = child.type
        if t in ("atx_h1_marker", "setext_h1_underline"):
            return 1
        if t in ("atx_h2_marker", "setext_h2_underline"):
            return 2
        if t == "atx_h3_marker":
            return 3
        if t == "atx_h4_marker":
            return 4
        if t == "atx_h5_marker":
            return 5
        if t == "atx_h6_marker":
            return 6
    return 2  # safe default


def _ts_heading_text(heading_node: Any, body_bytes: bytes) -> str:
    """Extract plain text content from an atx_heading or setext_heading node."""
    # Prefer the inline child (most accurate)
    for child in heading_node.children:
        if child.type == "inline":
            return body_bytes[child.start_byte:child.end_byte].decode(
                "utf-8", errors="replace"
            ).strip()
    # Fallback: strip # marks from raw heading text
    raw = body_bytes[heading_node.start_byte:heading_node.end_byte].decode(
        "utf-8", errors="replace"
    )
    return raw.lstrip("#").strip()


def _ts_has_code(node: Any) -> bool:
    """Return True if node or any descendant is a fenced_code_block."""
    for child in node.children:
        if child.type == "fenced_code_block":
            return True
        if _ts_has_code(child):
            return True
    return False


def _ts_collect_sections(node: Any, body_bytes: bytes, out: list[AgentSection]) -> None:
    """
    Recursively walk a tree-sitter node and collect AgentSection entries.

    Tree-sitter-markdown nests sections: a parent section contains its
    heading, direct content, AND child sections as node children. Walking
    recursively gives a flat list of all sections at all depths — which is
    exactly what the compliance checker and org graph builder need.
    """
    for child in node.children:
        if child.type != "section":
            continue

        heading_node = next(
            (c for c in child.children
             if c.type in ("atx_heading", "setext_heading")),
            None,
        )
        if heading_node:
            level = _ts_heading_level(heading_node)
            title = _ts_heading_text(heading_node, body_bytes)
            content = body_bytes[child.start_byte:child.end_byte].decode(
                "utf-8", errors="replace"
            )
            out.append(AgentSection(
                title=title,
                level=level,
                content=content,
                token_count=_estimate_tokens(content),
                has_code_blocks=_ts_has_code(child),
                line_start=child.start_point[0],
            ))

        # Always recurse — nested sections live as children of this section
        _ts_collect_sections(child, body_bytes, out)


def _fallback_sections(body: str) -> list[AgentSection]:
    """
    Regex-based section extractor used when tree-sitter is unavailable.

    NOTE: This method CAN match headers inside fenced code blocks —
    that is the known limitation motivating the tree-sitter integration.
    It is retained as a fallback only.
    """
    sections: list[AgentSection] = []
    for m in re.finditer(r"^(#{1,6}) (.+)$", body, re.MULTILINE):
        level = len(m.group(1))
        title = m.group(2).strip()
        line_start = body[: m.start()].count("\n")
        sections.append(AgentSection(
            title=title,
            level=level,
            content="",     # no slice in fallback — token_count will be 0
            token_count=0,
            has_code_blocks=False,
            line_start=line_start,
        ))
    return sections


def _parse_org_field(body: str, field_name: str) -> list[str]:
    """
    Parse an org-chart field from agent body text.

    Handles variants:
      **Reports to:** Agent1 → Agent2 → Agent3
      **Reports To:** Dir-X · VP-Y
      **Manages:** Agent1, Agent2, Agent3
    """
    pattern = (
        r"(?:\*\*)?(?:" + re.escape(field_name) + r")(?:\*\*)?[:\s]*(?:\*\*)?(.+)"
    )
    match = re.search(pattern, body[:2000], re.IGNORECASE)
    if not match:
        return []
    raw = match.group(1).strip()
    # Split on structural separators (→ · , / | and)
    parts = re.split(r"[→·,/|]|\band\b", raw)
    cleaned = []
    for p in parts:
        p = p.strip().strip("*_`").strip()
        # Exclude obviously non-name fragments
        if p and len(p) > 1 and not p.startswith("#"):
            cleaned.append(p)
    return cleaned


def _parse_frontmatter(content: str) -> tuple[dict, str]:
    """
    Extract and parse YAML frontmatter.
    Returns (fm_dict, body_without_frontmatter).
    """
    fm_dict: dict = {}
    body = content

    fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if fm_match:
        raw_yaml = fm_match.group(1)
        if _YAML_AVAILABLE:
            try:
                fm_dict = _yaml.safe_load(raw_yaml) or {}
            except Exception:
                fm_dict = _parse_frontmatter_regex(raw_yaml)
        else:
            fm_dict = _parse_frontmatter_regex(raw_yaml)
        body = content[fm_match.end():]

    return fm_dict, body


def _parse_frontmatter_regex(raw: str) -> dict:
    """Lightweight YAML field extraction for when PyYAML is unavailable."""
    result: dict = {}
    for line in raw.splitlines():
        m = re.match(r"^(\w[\w-]*):\s*(.+)$", line.strip())
        if m:
            result[m.group(1)] = m.group(2).strip()
    return result


def ts_parse_agent(file_path: Path) -> AgentAST:
    """
    Parse an agent .md file into a structured AgentAST.

    Parsing layers (in priority order):
      1. YAML frontmatter  → PyYAML safe_load (falls back to regex extraction)
      2. Markdown body     → tree-sitter-markdown AST (falls back to regex)
      3. Org fields        → regex scan of first 2000 chars of body

    The tree-sitter layer ensures section headers inside fenced code blocks
    are NOT counted as real sections — fixing the compliance false-positive
    that the previous regex approach had.
    """
    content = file_path.read_text(encoding="utf-8", errors="replace")

    # ── 1. Frontmatter ────────────────────────────────────────────────────────
    fm_dict, body = _parse_frontmatter(content)

    # ── 2. Section extraction ─────────────────────────────────────────────────
    sections: list[AgentSection] = []
    parse_error: Optional[str] = None

    if _TS_AVAILABLE and _ts_parser is not None:
        try:
            body_bytes = body.encode("utf-8")
            tree = _ts_parser.parse(body_bytes)
            _ts_collect_sections(tree.root_node, body_bytes, sections)
        except Exception as exc:
            parse_error = f"tree-sitter parse error: {exc}"
            sections = _fallback_sections(body)
    else:
        sections = _fallback_sections(body)

    # ── 3. Org chart fields ───────────────────────────────────────────────────
    reports_to = _parse_org_field(body, "Reports to")
    if not reports_to:
        reports_to = _parse_org_field(body, "Reports To")
    manages = _parse_org_field(body, "Manages")

    # ── 4. Normalise tool list ────────────────────────────────────────────────
    raw_tools = fm_dict.get("tools") or []
    if isinstance(raw_tools, str):
        raw_tools = [raw_tools]
    tools = [str(t).strip() for t in raw_tools if t]

    return AgentAST(
        name=str(fm_dict.get("name") or file_path.stem),
        version=str(fm_dict.get("version") or "?"),
        model=str(fm_dict.get("model") or "claude-sonnet-4-6"),
        description=str(fm_dict.get("description") or ""),
        tools=tools,
        frontmatter_raw=fm_dict,
        sections=sections,
        reports_to=reports_to,
        manages=manages,
        parse_error=parse_error,
    )


# ── Org graph ──────────────────────────────────────────────────────────────────

def build_org_graph(agents_dir: Path = AGENTS_DIR) -> dict[str, dict]:
    """
    Parse all agent files and build a hierarchical org graph.

    Returns:
        {agent_name: {
            "reports_to": [...],
            "manages": [...],
            "model": str,
            "version": str,
            "file": str,   # relative path from agents_dir
        }}
    """
    graph: dict[str, dict] = {}
    for agent_file in sorted(agents_dir.rglob("*.md")):
        if agent_file.name.startswith("_") or agent_file.name == "README.md":
            continue
        try:
            ast = ts_parse_agent(agent_file)
            if ast.name and ast.name != "?":
                graph[ast.name] = {
                    "reports_to": ast.reports_to,
                    "manages": ast.manages,
                    "model": ast.model,
                    "version": ast.version,
                    "file": str(agent_file.relative_to(agents_dir)),
                }
        except Exception:
            pass
    return graph


# ── Section token breakdown ────────────────────────────────────────────────────

def section_token_breakdown(target: str) -> list[tuple[str, int]]:
    """
    Return per-section token breakdown for an agent, sorted by token count desc.
    target: agent name (e.g. 'CPO') or absolute file path.
    Returns [(section_title, token_count), ...]
    """
    matches = list(AGENTS_DIR.rglob(f"{target}.md"))
    if not matches:
        p = Path(target)
        if p.exists():
            matches = [p]
    if not matches:
        return []

    ast = ts_parse_agent(matches[0])
    if not ast.sections:
        return []

    breakdown = [(s.title, s.token_count) for s in ast.sections]
    return sorted(breakdown, key=lambda x: x[1], reverse=True)


# ── Legacy regex helpers (kept for compatibility, used only in fallbacks) ───────

def _strip_frontmatter(content: str) -> str:
    """Remove YAML frontmatter block from markdown content."""
    return re.sub(r"^---\s*\n.*?\n---\s*\n", "", content, count=1, flags=re.DOTALL)


def _extract_frontmatter_field(content: str, field: str) -> Optional[str]:
    """Extract a single field value from YAML frontmatter."""
    match = re.search(rf"^{re.escape(field)}:\s*(.+)$", content[:500], re.MULTILINE)
    return match.group(1).strip() if match else None


def _normalize_model(model_id: str) -> str:
    """Normalize a model ID to its tier name."""
    model_id = model_id.lower().strip()
    if model_id in MODEL_TIER_MAP:
        return MODEL_TIER_MAP[model_id]
    for key in ("haiku", "sonnet", "opus"):
        if key in model_id:
            return key
    return "sonnet"  # safe default


def _count_bullets(body: str) -> int:
    return len(re.findall(r"^[-*+]\s", body, re.MULTILINE))


# ── Core: Agent Analysis ───────────────────────────────────────────────────────

def analyze_agent(file_path: Path) -> AgentAnalysis:
    """
    Analyze a single agent .md file for bloat, compliance gaps, and optimization.

    Uses ts_parse_agent() as the parsing backbone — tree-sitter when available,
    regex fallback otherwise.  The key improvement over the pure-regex approach:
    section headers inside fenced code blocks are NOT counted as real sections,
    eliminating false-negative compliance reports.
    """
    # ── Parse ────────────────────────────────────────────────────────────────
    ast = ts_parse_agent(file_path)
    content = file_path.read_text(encoding="utf-8", errors="replace")
    _, body = _parse_frontmatter(content)

    # ── Budget ───────────────────────────────────────────────────────────────
    model_tier = _normalize_model(ast.model)
    budget = MODEL_BUDGETS.get(model_tier, 2000)
    # Token estimate on the body only (frontmatter adds overhead but is excluded
    # from the prompt in most agent invocations)
    estimated_tokens = _estimate_tokens(body)
    over_budget = estimated_tokens > budget

    issues: list[str] = []
    suggestions: list[str] = []
    bloat = 0.0

    # ── Token budget check ───────────────────────────────────────────────────
    if over_budget:
        ratio = estimated_tokens / budget
        over_pct = int((ratio - 1) * 100)
        issues.append(
            f"Over {model_tier} budget: ~{estimated_tokens} tokens vs {budget} target (+{over_pct}%)"
        )
        bloat += min(0.4, 0.1 * ratio)
        if model_tier == "haiku":
            suggestions.append(
                "Haiku: keep only role, core actions, output format, and hard constraints. Strip all narrative."
            )
        else:
            suggestions.append(
                f"Compress to under {budget} tokens — remove repeated context and inline boilerplate"
            )
        # Identify the top token hogs when tree-sitter sections are available
        if ast.sections and _TS_AVAILABLE:
            top = sorted(ast.sections, key=lambda s: s.token_count, reverse=True)[:3]
            breakdown = ", ".join(f"'{s.title}' ({s.token_count}tk)" for s in top if s.token_count > 0)
            if breakdown:
                suggestions.append(f"Largest sections: {breakdown}")

    # ── Inherited boilerplate check ──────────────────────────────────────────
    boilerplate_hits = sum(
        len(re.findall(p, body, re.IGNORECASE)) for p in INHERITED_PATTERNS
    )
    if boilerplate_hits >= 3:
        issues.append(
            f"High inherited boilerplate density ({boilerplate_hits} hits) — already covered by CLAUDE.md"
        )
        bloat += 0.2
        suggestions.append(
            "Remove governance boilerplate that all agents inherit from CLAUDE.md (COSO, SOX, NIST, etc.)"
        )

    # ── Duplicate sentence check ─────────────────────────────────────────────
    sentences = [s.strip() for s in re.split(r"[.!?\n]", body) if len(s.strip()) > 30]
    dupes = [s for s, c in Counter(sentences).items() if c > 1]
    if dupes:
        issues.append(f"{len(dupes)} repeated sentences — content duplication detected")
        bloat += min(0.25, 0.05 * len(dupes))
        suggestions.append(f"Deduplicate: remove {len(dupes)} repeated sentence(s)")

    # ── Section count check ──────────────────────────────────────────────────
    # Use lowercased titles from the parsed AST (code-block headers excluded)
    headers_lower = [s.title.lower() for s in ast.sections]
    if len(headers_lower) > 14:
        issues.append(
            f"High section count ({len(headers_lower)}) — consider consolidating thin sections"
        )
        bloat += 0.1
        suggestions.append("Merge sections with < 3 bullets into their parent section")

    # ── Missing required sections (AST-accurate, code blocks excluded) ───────
    missing = [s for s in REQUIRED_SECTIONS if not any(s in h for h in headers_lower)]

    # ── Compressible sections ────────────────────────────────────────────────
    compressible_found = [h for h in headers_lower if any(c in h for c in COMPRESSIBLE_SECTIONS)]
    if compressible_found and model_tier == "haiku":
        issues.append(
            f"Compressible sections in Haiku agent: {', '.join(compressible_found)}"
        )
        bloat += 0.15
        suggestions.append(
            f"Haiku agents should drop or inline these sections: {', '.join(compressible_found)}"
        )

    # ── Version field check ──────────────────────────────────────────────────
    if ast.version == "?":
        issues.append("Missing version field in frontmatter — AGENT_STANDARDS non-compliant")
        bloat += 0.05

    return AgentAnalysis(
        name=ast.name,
        file_path=file_path,
        model=ast.model,
        model_tier=model_tier,
        estimated_tokens=estimated_tokens,
        budget=budget,
        over_budget=over_budget,
        bloat_score=min(bloat, 1.0),
        issues=issues,
        suggestions=suggestions,
        missing_sections=missing,
    )


def scan_all_agents(agents_dir: Path = AGENTS_DIR) -> list[AgentAnalysis]:
    """Scan and analyze all agent .md files, sorted by bloat score descending."""
    results = []
    for md_file in agents_dir.rglob("*.md"):
        if md_file.name.startswith("_") or md_file.name == "README.md":
            continue
        try:
            results.append(analyze_agent(md_file))
        except Exception as e:
            print(f"  [WARN] Could not analyze {md_file.name}: {e}", file=sys.stderr)
    return sorted(results, key=lambda a: a.bloat_score, reverse=True)


# ── Core: Usage Patterns ───────────────────────────────────────────────────────

def analyze_run_patterns(days: int = 14) -> dict[str, UsagePattern]:
    """
    Read run_log.jsonl and return usage patterns per agent.
    Expected log fields: timestamp, agent, tier, model (others ignored).
    """
    if not RUN_LOG.exists():
        return {}

    cutoff = datetime.now() - timedelta(days=days)
    bucket: dict[str, dict] = defaultdict(
        lambda: {"count": 0, "tiers": [], "dates": [], "models": Counter()}
    )

    with open(RUN_LOG, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            ts_str = entry.get("timestamp") or entry.get("ts") or ""
            try:
                ts = datetime.fromisoformat(ts_str[:19])
                if ts < cutoff:
                    continue
            except (ValueError, TypeError):
                pass  # include entries without parseable timestamp

            agent = entry.get("agent") or entry.get("agent_name") or "unknown"
            tier = entry.get("tier", 1)
            model = entry.get("model", "unknown")

            bucket[agent]["count"] += 1
            bucket[agent]["tiers"].append(tier)
            bucket[agent]["dates"].append(ts_str)
            bucket[agent]["models"][model] += 1

    return {
        agent: UsagePattern(
            agent=agent,
            invocation_count=data["count"],
            avg_tier=sum(data["tiers"]) / len(data["tiers"]) if data["tiers"] else 1.0,
            last_used=max(data["dates"]) if data["dates"] else "",
            models_used=data["models"],
        )
        for agent, data in bucket.items()
    }


# ── Core: Cache Management ─────────────────────────────────────────────────────

def audit_cache(cache_dir: Path = PROMPT_CACHE_DIR) -> CacheAudit:
    """Audit the prompt cache — identify stale and orphaned entries."""
    if not cache_dir.exists():
        return CacheAudit(valid=0, stale=[], orphaned=[])

    stale: list[str] = []
    orphaned: list[str] = []
    valid = 0

    for cache_file in cache_dir.glob("*.cache.json"):
        try:
            data = json.loads(cache_file.read_text(encoding="utf-8"))
            source_path = Path(data.get("source_path", ""))
            stored_hash = data.get("source_hash", "")

            if not source_path.exists():
                orphaned.append(cache_file.name)
                continue

            current_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
            if current_hash != stored_hash:
                stale.append(cache_file.name)
            else:
                valid += 1
        except Exception:
            orphaned.append(cache_file.name)

    return CacheAudit(valid=valid, stale=stale, orphaned=orphaned)


def clean_cache(dry_run: bool = True, cache_dir: Path = PROMPT_CACHE_DIR) -> dict:
    """Remove stale and orphaned cache entries. Returns summary."""
    ca = audit_cache(cache_dir)
    removed: list[str] = []

    for entry in ca.stale + ca.orphaned:
        cache_file = cache_dir / entry
        if not dry_run:
            cache_file.unlink(missing_ok=True)
        removed.append(entry)

    return {
        "removed": removed,
        "valid_remaining": ca.valid,
        "dry_run": dry_run,
    }


def warm_cache(agents_dir: Path = AGENTS_DIR) -> int:
    """
    Pre-warm the prompt cache for all agent files by importing prompt_cache.
    Returns the number of agents warmed.
    """
    try:
        sys.path.insert(0, str(CLAUDE_DIR))
        import prompt_cache  # type: ignore
        count = prompt_cache.warm(str(agents_dir))
        return count
    except ImportError:
        print("[WARN] prompt_cache module not found — skipping warm", file=sys.stderr)
        return 0


# ── Core: Memory Management ────────────────────────────────────────────────────

def audit_memory(memory_dir: Path = MEMORY_DIR) -> list[dict]:
    """
    Audit memory files for staleness, size anomalies, and format compliance.
    Returns list of findings dicts.
    """
    findings: list[dict] = []

    if not memory_dir.exists():
        return findings

    for mem_file in sorted(memory_dir.glob("*.md")):
        if mem_file.name == "MEMORY.md":
            continue

        try:
            content = mem_file.read_text(encoding="utf-8", errors="replace")
            stat = mem_file.stat()
            age_days = (datetime.now().timestamp() - stat.st_mtime) / 86400

            issues: list[str] = []

            if not content.startswith("---"):
                issues.append("Missing frontmatter — non-compliant memory format")

            if age_days > 45:
                issues.append(
                    f"Stale: not modified in {int(age_days)} days — verify still current"
                )

            if len(content) > 4000:
                issues.append(
                    f"Large ({len(content)} chars) — consider splitting into focused sub-memories"
                )

            memory_index = memory_dir / "MEMORY.md"
            if memory_index.exists():
                index_content = memory_index.read_text(encoding="utf-8", errors="replace")
                if mem_file.name not in index_content:
                    issues.append("Not referenced in MEMORY.md index — orphaned memory file")

            if issues:
                findings.append({
                    "file": mem_file.name,
                    "age_days": round(age_days, 1),
                    "size_chars": len(content),
                    "issues": issues,
                })

        except Exception as e:
            findings.append({
                "file": mem_file.name,
                "age_days": -1,
                "size_chars": -1,
                "issues": [f"Could not read file: {e}"],
            })

    return findings


# ── Reporting ──────────────────────────────────────────────────────────────────

def full_report(days: int = 14) -> str:
    """Generate a comprehensive Custodian maintenance report."""
    ts_status = "tree-sitter" if _TS_AVAILABLE else "regex fallback"
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines: list[str] = [
        "# Custodian Maintenance Report",
        f"**Generated:** {now} | **Pattern window:** {days} days | **Parser:** {ts_status}",
        "",
    ]

    # ── Usage patterns ────────────────────────────────────────────────────────
    patterns = analyze_run_patterns(days=days)
    if patterns:
        lines.append("## Usage Patterns (Top 10 agents)")
        top = sorted(patterns.values(), key=lambda p: p.invocation_count, reverse=True)[:10]
        for p in top:
            dominant_model = p.models_used.most_common(1)[0][0] if p.models_used else "?"
            lines.append(
                f"- **{p.agent}**: {p.invocation_count} calls | "
                f"avg tier {p.avg_tier:.1f} | model: {dominant_model}"
            )
        lines.append("")
    else:
        lines.append("## Usage Patterns\n_No run log found or no entries in window._\n")

    # ── Agent analysis ────────────────────────────────────────────────────────
    analyses = scan_all_agents()
    needs_attention = [a for a in analyses if a.bloat_score > 0.2 or a.missing_sections]

    lines.append("## Agent Bloat Analysis")
    lines.append(
        f"**Total agents scanned:** {len(analyses)} | **Need attention:** {len(needs_attention)}"
    )
    lines.append("")

    by_tier: dict[str, list[AgentAnalysis]] = defaultdict(list)
    for a in analyses:
        by_tier[a.model_tier].append(a)

    for tier in ("haiku", "sonnet", "opus"):
        agents_in_tier = by_tier.get(tier, [])
        if not agents_in_tier:
            continue
        over = [a for a in agents_in_tier if a.over_budget]
        lines.append(
            f"**{tier.capitalize()}** ({len(agents_in_tier)} agents): "
            f"{len(over)} over budget"
        )

    lines.append("")

    if needs_attention:
        lines.append("### Top Issues (sorted by bloat score)")
        for a in needs_attention[:15]:
            lines.append(f"\n#### {a.name}")
            lines.append(
                f"Model: `{a.model_tier}` | "
                f"Tokens: ~{a.estimated_tokens} / {a.budget} budget | "
                f"Bloat score: {a.bloat_score:.2f}"
            )
            for issue in a.issues:
                lines.append(f"- ⚠️  {issue}")
            for sug in a.suggestions:
                lines.append(f"- 💡 {sug}")
            if a.missing_sections:
                lines.append(f"- ❌ Missing required sections: {', '.join(a.missing_sections)}")
    else:
        lines.append("_All agents within budget and compliant._")

    lines.append("")

    # ── Cache audit ───────────────────────────────────────────────────────────
    ca = audit_cache()
    lines.append("## Prompt Cache")
    lines.append(f"- Valid: {ca.valid}")
    lines.append(f"- Stale: {len(ca.stale)}")
    lines.append(f"- Orphaned: {len(ca.orphaned)}")
    if ca.stale:
        lines.append(
            f"\nStale entries: {', '.join(ca.stale[:5])}"
            + (" ..." if len(ca.stale) > 5 else "")
        )
    if ca.orphaned:
        lines.append(
            f"Orphaned entries: {', '.join(ca.orphaned[:5])}"
            + (" ..." if len(ca.orphaned) > 5 else "")
        )
    lines.append("")

    # ── Memory audit ──────────────────────────────────────────────────────────
    mem_findings = audit_memory()
    lines.append("## Memory Audit")
    if mem_findings:
        for f in mem_findings:
            lines.append(f"\n### {f['file']} (age: {f['age_days']}d, {f['size_chars']} chars)")
            for issue in f["issues"]:
                lines.append(f"- {issue}")
    else:
        lines.append("_All memory files nominal._")

    lines.append("")
    lines.append("---")
    lines.append(f"_Report generated by Custodian v2.0.0 | Parser: {ts_status}_")

    return "\n".join(lines)


# ── Maintenance Cycle ──────────────────────────────────────────────────────────

def generate_cleaning_plan(days: int = 14) -> str:
    """
    Generate a structured cleaning plan for CPrO / Dir-PromptQA review.
    Custodian ALWAYS produces this plan first. Execution only happens after approval.
    """
    analyses = scan_all_agents()
    needs_attention = [a for a in analyses if a.bloat_score > 0.2 or a.missing_sections]
    ca = audit_cache()
    mem_findings = audit_memory()
    patterns = analyze_run_patterns(days=days)

    high_freq = {
        p.agent
        for p in sorted(
            patterns.values(), key=lambda p: p.invocation_count, reverse=True
        )[:20]
    }

    ts_note = "" if _TS_AVAILABLE else " _(regex fallback — install tree-sitter-markdown for code-block-accurate compliance detection)_"
    lines = [
        "# Custodian Cleaning Plan",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}{ts_note}",
        "**Status:** PENDING CPrO / Dir-PromptQA APPROVAL",
        "**Required:** Explicit approval before any changes are applied.",
        "",
        "---",
        "",
        "## Proposed Actions",
        "",
    ]

    # ── Agent compressions ────────────────────────────────────────────────────
    lines.append("### 1. Agent Prompt Compressions")
    compressible = [a for a in needs_attention if a.over_budget]
    if compressible:
        for a in compressible[:10]:
            priority = "HIGH (high-freq)" if a.name in high_freq else "MEDIUM"
            lines.append(
                f"- **{a.name}** | {a.model_tier} | ~{a.estimated_tokens}→{a.budget} tokens | Priority: {priority}"
            )
            for sug in a.suggestions[:2]:
                lines.append(f"  - {sug}")
    else:
        lines.append("_No agents currently over budget._")

    lines.append("")

    # ── Model tier mismatches ─────────────────────────────────────────────────
    mismatches = [a for a in analyses if a.model_tier == "haiku" and a.estimated_tokens > 1500]
    if mismatches:
        lines.append("### 2. Model Tier Corrections (Haiku agents doing Sonnet-level work)")
        for a in mismatches[:5]:
            lines.append(
                f"- **{a.name}** | ~{a.estimated_tokens} tokens | Recommend: bump to `sonnet`"
            )
        lines.append("")

    # ── Missing required sections ─────────────────────────────────────────────
    missing_secs = [a for a in analyses if a.missing_sections]
    if missing_secs:
        lines.append("### 3. Compliance Gaps (Missing Required Sections)")
        for a in missing_secs[:5]:
            lines.append(f"- **{a.name}** — missing: {', '.join(a.missing_sections)}")
        lines.append("")

    # ── Cache cleanup ─────────────────────────────────────────────────────────
    lines.append("### 4. Prompt Cache Cleanup")
    if ca.total_issues > 0:
        lines.append(f"- Remove {len(ca.stale)} stale entries (source file changed)")
        lines.append(f"- Remove {len(ca.orphaned)} orphaned entries (source file deleted)")
        lines.append(f"- {ca.valid} valid entries will be preserved")
    else:
        lines.append("_Cache is clean — no action needed._")
    lines.append("")

    # ── Memory hygiene ────────────────────────────────────────────────────────
    lines.append("### 5. Memory Hygiene")
    if mem_findings:
        for f in mem_findings:
            lines.append(f"- **{f['file']}** — {'; '.join(f['issues'])}")
    else:
        lines.append("_All memory files nominal._")
    lines.append("")

    # ── Summary ───────────────────────────────────────────────────────────────
    total_actions = (
        len(compressible) + len(mismatches) + len(missing_secs)
        + ca.total_issues + len(mem_findings)
    )
    lines += [
        "---",
        "",
        "## Summary",
        "| Category | Actions |",
        "|---|---|",
        f"| Agent compressions | {len(compressible)} |",
        f"| Model tier corrections | {len(mismatches)} |",
        f"| Compliance gap fixes | {len(missing_secs)} |",
        f"| Cache entries to remove | {ca.total_issues} |",
        f"| Memory file issues | {len(mem_findings)} |",
        f"| **Total actions** | **{total_actions}** |",
        "",
        "---",
        "",
        "## Approval Required",
        "This plan must be reviewed and approved by **CPrO-Prompting** or **Dir-PromptQA** before execution.",
        "To approve: `python custodian.py cycle --live`",
        "To approve specific agents only: `python custodian.py analyze <AgentName>` then edit manually.",
        "",
        "_Custodian does not self-authorize execution. Plan → Review → Approve → Execute._",
    ]

    return "\n".join(lines)


def maintenance_cycle(dry_run: bool = True) -> None:
    """Run full maintenance: analyze, audit, and optionally clean."""
    mode_label = "DRY RUN (cleaning plan)" if dry_run else "LIVE (CPrO-approved)"
    ts_label = "tree-sitter" if _TS_AVAILABLE else "regex"
    print(f"🔧 Custodian — Maintenance cycle ({mode_label}) | parser: {ts_label}")
    print()

    patterns = analyze_run_patterns()
    print(f"  📊 Usage patterns: {len(patterns)} agents tracked")

    analyses = scan_all_agents()
    needs_attention = [a for a in analyses if a.bloat_score > 0.2 or a.missing_sections]
    over_budget = [a for a in analyses if a.over_budget]
    print(
        f"  🔍 Agents: {len(analyses)} scanned | "
        f"{len(over_budget)} over budget | {len(needs_attention)} need attention"
    )

    cache_result = clean_cache(dry_run=dry_run)
    action = "Would remove" if dry_run else "Removed"
    print(
        f"  💾 Cache: {action} {len(cache_result['removed'])} stale/orphaned | "
        f"{cache_result['valid_remaining']} valid"
    )

    mem_findings = audit_memory()
    print(f"  🧠 Memory: {len(mem_findings)} file(s) with issues")

    report = full_report()
    if not dry_run:
        REPORT_PATH.write_text(report, encoding="utf-8")
        print(f"\n  📄 Report saved → {REPORT_PATH}")
    else:
        print(f"\n  📄 Report preview (run with --live to save):\n")
        print(
            report[:2000]
            + (
                "\n  [... truncated — run 'report' command for full output]"
                if len(report) > 2000
                else ""
            )
        )

    print()
    if needs_attention:
        print("  ⚠️  Top 3 agents needing attention:")
        for a in needs_attention[:3]:
            print(
                f"     {a.name:<40} bloat={a.bloat_score:.2f}  "
                f"tokens=~{a.estimated_tokens}/{a.budget}  ({a.model_tier})"
            )

    print()
    print("🔧 Custodian — Cycle complete")


# ── Changelog Cold Storage ─────────────────────────────────────────────────────

def _parse_changelog_entries(content: str) -> list[dict]:
    """
    Parse CHANGELOG.md into a list of entry dicts.
    Each entry: {header, date, body, age_days}
    """
    entries: list[dict] = []
    blocks = re.split(r"(?=^## )", content, flags=re.MULTILINE)

    for block in blocks:
        block = block.strip()
        if not block or not block.startswith("## "):
            continue

        header_match = re.match(r"^## (.+)$", block, re.MULTILINE)
        if not header_match:
            continue

        header = header_match.group(1)
        date_match = re.search(r"(\d{4}-\d{2}-\d{2})", header)
        entry_date = None
        age_days = 0
        if date_match:
            try:
                entry_date = datetime.strptime(date_match.group(1), "%Y-%m-%d")
                age_days = (datetime.now() - entry_date).days
            except ValueError:
                pass

        entries.append({
            "header": header,
            "date": date_match.group(1) if date_match else None,
            "age_days": age_days,
            "body": block,
        })

    return entries


def compact_changelog(
    changelog_path: Path = CHANGELOG_PATH,
    cold_storage_dir: Path = COLD_STORAGE_DIR,
    retain_days: int = CHANGELOG_RETAIN_DAYS,
    dry_run: bool = True,
) -> dict:
    """
    Compact CHANGELOG.md:
    - Entries older than retain_days are moved to a dated zip in cold storage.
    - Each zip contains the raw entries as a .md file + a JSON metadata index.
    - Active CHANGELOG.md retains only recent entries + a pointer to cold storage.

    Returns a summary dict.
    """
    if not changelog_path.exists():
        return {"error": f"CHANGELOG not found at {changelog_path}"}

    content = changelog_path.read_text(encoding="utf-8", errors="replace")

    header_end = content.find("\n## ")
    if header_end == -1:
        return {"error": "No entries found in CHANGELOG.md"}

    file_header = content[:header_end].rstrip()
    entries = _parse_changelog_entries(content[header_end:])

    recent = [e for e in entries if e["age_days"] <= retain_days]
    cold = [e for e in entries if e["age_days"] > retain_days]

    summary = {
        "total_entries": len(entries),
        "recent_entries": len(recent),
        "cold_entries": len(cold),
        "retain_days": retain_days,
        "dry_run": dry_run,
        "zip_path": None,
    }

    if not cold:
        summary["message"] = (
            f"Nothing to compact — all {len(entries)} entries are within {retain_days} days"
        )
        return summary

    if dry_run:
        summary["message"] = (
            f"Would compact {len(cold)} entries (oldest: {cold[-1].get('date', '?')}) "
            f"→ cold storage zip. {len(recent)} entries would remain active."
        )
        return summary

    cold_storage_dir.mkdir(parents=True, exist_ok=True)

    dates = [e["date"] for e in cold if e["date"]]
    date_range = (
        f"{min(dates)}_to_{max(dates)}" if dates else datetime.now().strftime("%Y-%m-%d")
    )
    zip_name = f"CHANGELOG_{date_range}.zip"
    zip_path = cold_storage_dir / zip_name

    cold_md_lines = [
        "# CHANGELOG — Cold Storage Archive",
        f"**Date Range:** {min(dates) if dates else '?'} to {max(dates) if dates else '?'}",
        f"**Entries:** {len(cold)}",
        f"**Archived:** {datetime.now().isoformat()}",
        f"**Retain threshold was:** {retain_days} days",
        "",
        "---",
        "",
    ]
    for e in cold:
        cold_md_lines.append(e["body"])
        cold_md_lines.append("")

    cold_md = "\n".join(cold_md_lines)

    metadata = {
        "archive": zip_name,
        "archived_at": datetime.now().isoformat(),
        "retain_days": retain_days,
        "entry_count": len(cold),
        "date_range": {
            "from": min(dates) if dates else None,
            "to": max(dates) if dates else None,
        },
        "entries": [
            {"header": e["header"], "date": e["date"], "age_days": e["age_days"]}
            for e in cold
        ],
    }

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"CHANGELOG_{date_range}.md", cold_md)
        zf.writestr("metadata.json", json.dumps(metadata, indent=2))

    pointer_block = (
        f"\n## Cold Storage Pointer\n\n"
        f"Entries older than {retain_days} days have been archived.\n"
        f"**Archive:** `cold_storage/{zip_name}`\n"
        f"**Entries archived:** {len(cold)}\n"
        f"**Date range:** {min(dates) if dates else '?'} → {max(dates) if dates else '?'}\n"
        f"**Archived at:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        f"**Lookup:** `python custodian.py changelog --search <keyword>`\n"
    )

    recent_body = "\n\n".join(e["body"] for e in recent)
    new_content = file_header + "\n\n---\n" + pointer_block + "\n---\n\n" + recent_body
    changelog_path.write_text(new_content, encoding="utf-8")

    summary["zip_path"] = str(zip_path)
    summary["message"] = (
        f"Compacted {len(cold)} entries → {zip_path.name} "
        f"({zip_path.stat().st_size // 1024}KB). "
        f"{len(recent)} entries remain active."
    )
    return summary


def search_cold_storage(keyword: str, cold_storage_dir: Path = COLD_STORAGE_DIR) -> list[dict]:
    """
    Search cold storage archives for a keyword.
    Reads metadata.json from each zip without extracting the full .md.
    Returns list of matching entry metadata dicts with archive source.
    """
    if not cold_storage_dir.exists():
        return []

    results: list[dict] = []
    kw_lower = keyword.lower()

    for zip_path in sorted(cold_storage_dir.glob("CHANGELOG_*.zip")):
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                if "metadata.json" in zf.namelist():
                    meta = json.loads(zf.read("metadata.json").decode("utf-8"))
                    for entry in meta.get("entries", []):
                        if kw_lower in entry.get("header", "").lower():
                            results.append({**entry, "archive": zip_path.name})
                md_files = [n for n in zf.namelist() if n.endswith(".md")]
                for md_file in md_files:
                    md_content = zf.read(md_file).decode("utf-8", errors="replace")
                    for block in re.split(r"(?=^## )", md_content, flags=re.MULTILINE):
                        if kw_lower in block.lower() and block.startswith("## "):
                            header = re.match(r"^## (.+)$", block, re.MULTILINE)
                            if header and not any(
                                r.get("header") == header.group(1) for r in results
                            ):
                                date_m = re.search(r"(\d{4}-\d{2}-\d{2})", header.group(1))
                                results.append({
                                    "header": header.group(1),
                                    "date": date_m.group(1) if date_m else None,
                                    "archive": zip_path.name,
                                    "match": "content",
                                })
        except Exception as e:
            print(f"  [WARN] Could not read {zip_path.name}: {e}", file=sys.stderr)

    return results


# ── CLI ────────────────────────────────────────────────────────────────────────

def main() -> None:
    # Windows: force UTF-8 stdout so emoji and special chars don't crash
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    args = sys.argv[1:]
    cmd = args[0] if args else "report"
    live = "--live" in args

    if cmd == "report":
        print(full_report())

    elif cmd == "plan":
        plan = generate_cleaning_plan()
        plan_path = CLAUDE_DIR / "custodian_plan.md"
        plan_path.write_text(plan, encoding="utf-8")
        print(plan)
        print(f"\n📋 Plan saved → {plan_path}")
        print("Send this plan to CPrO-Prompting or Dir-PromptQA for approval.")
        print("On approval, run: python custodian.py cycle --live")

    elif cmd == "cycle":
        if not live:
            plan = generate_cleaning_plan()
            plan_path = CLAUDE_DIR / "custodian_plan.md"
            plan_path.write_text(plan, encoding="utf-8")
            print(plan)
            print(f"\n📋 Plan saved → {plan_path}")
            print("\n⚠️  Custodian requires CPrO / Dir-PromptQA approval before executing.")
            print("On approval, run: python custodian.py cycle --live")
        else:
            maintenance_cycle(dry_run=False)

    elif cmd == "analyze":
        target = next((a for a in args[1:] if not a.startswith("-")), None)
        if target:
            matches = list(AGENTS_DIR.rglob(f"{target}.md"))
            if not matches:
                print(f"Agent not found: {target}")
                sys.exit(1)
            a = analyze_agent(matches[0])
            print(f"Agent:    {a.name}")
            print(f"Model:    {a.model} ({a.model_tier}) | Budget: {a.budget} tokens")
            print(f"Tokens:   ~{a.estimated_tokens} | Over budget: {a.over_budget}")
            print(f"Bloat:    {a.bloat_score:.2f}")
            if a.issues:
                print("\nIssues:")
                for issue in a.issues:
                    print(f"  ⚠️  {issue}")
            if a.suggestions:
                print("\nSuggestions:")
                for sug in a.suggestions:
                    print(f"  💡 {sug}")
            if a.missing_sections:
                print(f"\nMissing sections: {', '.join(a.missing_sections)}")
        else:
            print(f"{'Agent':<42} {'Bloat':>6}  {'Tokens':>8}  {'Budget':>7}  Model")
            print("-" * 80)
            for a in scan_all_agents():
                if a.bloat_score > 0.05:
                    over = "⚠️ " if a.over_budget else "  "
                    print(
                        f"{a.name:<42} {a.bloat_score:>6.2f}  "
                        f"~{a.estimated_tokens:>7}  {a.budget:>7}  {over}{a.model_tier}"
                    )

    elif cmd == "sections":
        target = next((a for a in args[1:] if not a.startswith("-")), None)
        if not target:
            print("Usage: python custodian.py sections <AgentName>")
            sys.exit(1)
        if not _TS_AVAILABLE:
            print(
                "[WARN] tree-sitter not available — section token counts will be 0 (regex fallback)."
            )
        breakdown = section_token_breakdown(target)
        if not breakdown:
            print(f"Agent not found: {target}")
            sys.exit(1)
        print(f"Section token breakdown — {target}")
        print(f"{'Section':<52} {'Tokens':>7}")
        print("-" * 62)
        total = 0
        for title, tokens in breakdown:
            print(f"{title:<52} {tokens:>7}")
            total += tokens
        print("-" * 62)
        print(f"{'TOTAL':<52} {total:>7}")

    elif cmd == "graph":
        fmt = next(
            (args[i + 1] for i, a in enumerate(args) if a == "--format" and i + 1 < len(args)),
            "text",
        )
        graph = build_org_graph()
        if fmt == "json":
            print(json.dumps(graph, indent=2))
        else:
            print(f"Org Graph — {len(graph)} agents")
            print(f"{'Agent':<45} {'Reports to':<38} {'Model'}")
            print("-" * 100)
            for name, data in sorted(graph.items()):
                reports = " → ".join(data["reports_to"]) if data["reports_to"] else "(root/CEO)"
                model_short = (
                    data["model"]
                    .replace("claude-", "")
                    .replace("-4-5-20251001", "")
                    .replace("-4-6", "")
                )
                # Truncate long reports_to chains
                if len(reports) > 37:
                    reports = reports[:34] + "..."
                print(f"{name:<45} {reports:<38} {model_short}")

    elif cmd == "cache":
        if live:
            result = clean_cache(dry_run=False)
            print(
                f"Cache cleaned: {len(result['removed'])} removed | "
                f"{result['valid_remaining']} valid"
            )
        else:
            ca = audit_cache()
            print(f"Valid:    {ca.valid}")
            print(f"Stale:    {len(ca.stale)}")
            print(f"Orphaned: {len(ca.orphaned)}")
            if ca.stale:
                print(f"\nStale entries ({len(ca.stale)}):")
                for e in ca.stale[:10]:
                    print(f"  {e}")
            if ca.orphaned:
                print(f"\nOrphaned entries ({len(ca.orphaned)}):")
                for e in ca.orphaned[:10]:
                    print(f"  {e}")
            if ca.total_issues > 0:
                print(f"\nRun with --live to clean {ca.total_issues} issue(s)")

    elif cmd == "memory":
        findings = audit_memory()
        if not findings:
            print("All memory files nominal.")
        else:
            for f in findings:
                print(f"\n{f['file']} (age: {f['age_days']}d, {f['size_chars']} chars)")
                for issue in f["issues"]:
                    print(f"  • {issue}")

    elif cmd == "patterns":
        days_arg = next(
            (args[i + 1] for i, a in enumerate(args) if a == "--days" and i + 1 < len(args)),
            "14",
        )
        try:
            days = int(days_arg)
        except ValueError:
            days = 14
        patterns = analyze_run_patterns(days=days)
        if not patterns:
            print(f"No run log found at {RUN_LOG}")
            sys.exit(0)
        print(f"{'Agent':<42} {'Calls':>6}  {'Avg Tier':>9}  Last Used")
        print("-" * 75)
        for p in sorted(patterns.values(), key=lambda p: p.invocation_count, reverse=True):
            print(
                f"{p.agent:<42} {p.invocation_count:>6}  "
                f"{p.avg_tier:>9.1f}  {p.last_used[:10]}"
            )

    elif cmd == "warm":
        count = warm_cache()
        print(f"Cache warmed: {count} agents")

    elif cmd == "changelog":
        search_kw = next(
            (args[i + 1] for i, a in enumerate(args) if a == "--search" and i + 1 < len(args)),
            None,
        )
        if search_kw:
            results = search_cold_storage(search_kw)
            if not results:
                print(f"No matches for '{search_kw}' in cold storage")
            else:
                print(f"Found {len(results)} match(es) for '{search_kw}':")
                for r in results:
                    print(f"  [{r['archive']}] {r.get('date', '?')} — {r['header']}")
        else:
            result = compact_changelog(dry_run=not live)
            print(result.get("message") or json.dumps(result, indent=2))
            if result.get("zip_path"):
                print(f"Archive: {result['zip_path']}")

    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
