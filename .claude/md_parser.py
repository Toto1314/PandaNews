#!/usr/bin/env python3
"""
md_parser.py — Tree-sitter powered markdown parser for the AI OS.

Parses .md files (agent files, CLAUDE.md, SYSTEM_MAP.md, etc.) into structured
Python objects: frontmatter, headings, sections, tables, code blocks, and TOC.

Import API:
    from md_parser import MarkdownParser, MarkdownIndex, ParsedDoc

CLI:
    python md_parser.py parse   <file>
    python md_parser.py toc     <file>
    python md_parser.py section <file> <heading>
    python md_parser.py tables  <file>
    python md_parser.py code    <file> [--lang <lang>]
    python md_parser.py index   <dir>
    python md_parser.py search  <dir> <query>
    python md_parser.py agents
"""
from __future__ import annotations

import json
import logging
import re
import sys
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import tree_sitter_markdown
from tree_sitter import Language, Node, Parser, Tree

try:
    import yaml as _yaml
    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False

CLAUDE_DIR = Path.home() / ".claude"
AGENTS_DIR = CLAUDE_DIR / "agents"
LOG = logging.getLogger("md_parser")

_MD_LANGUAGE: Optional[Language] = None
_PARSER: Optional[Parser] = None

warnings.filterwarnings("ignore", category=FutureWarning, module="tree_sitter")


@dataclass
class Heading:
    level: int
    text: str
    line: int
    node: object = field(default=None, repr=False)


@dataclass
class TocEntry:
    level: int
    text: str
    line: int
    children: list["TocEntry"] = field(default_factory=list)


@dataclass
class TableData:
    headers: list
    rows: list
    line: int


@dataclass
class CodeBlock:
    language: str
    content: str
    line: int


def _get_language() -> Language:
    global _MD_LANGUAGE
    if _MD_LANGUAGE is not None:
        return _MD_LANGUAGE
    try:
        _MD_LANGUAGE = Language(tree_sitter_markdown.language())
        return _MD_LANGUAGE
    except Exception as exc:
        raise RuntimeError(
            f"Failed to load tree-sitter-markdown grammar: {exc}\n"
            "Install with: pip install tree-sitter-markdown"
        ) from exc


def _get_parser() -> Parser:
    global _PARSER
    if _PARSER is not None:
        return _PARSER
    _PARSER = Parser(_get_language())
    return _PARSER


def _parse_yaml(text: str) -> dict:
    if _HAS_YAML:
        try:
            result = _yaml.safe_load(text)
            return result if isinstance(result, dict) else {}
        except Exception as exc:
            LOG.warning("YAML parse error: %s", exc)
            return {}
    # fallback: line-by-line key: value (from vector_router.py pattern)
    result = {}
    for line in text.splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            k = k.strip()
            v = v.strip()
            if k:
                # handle list values like: tools: [Read, Write]
                if v.startswith("[") and v.endswith("]"):
                    v = [i.strip() for i in v[1:-1].split(",") if i.strip()]
                result[k] = v
    return result


@dataclass
class ParsedDoc:
    path: Path
    source: str
    tree: object = field(default=None, repr=False)
    frontmatter: dict = field(default_factory=dict)
    headings: list = field(default_factory=list)
    sections: dict = field(default_factory=dict)
    tables: list = field(default_factory=list)
    code_blocks: list = field(default_factory=list)
    toc: list = field(default_factory=list)

    def get_section(self, heading: str) -> Optional[str]:
        heading_lower = heading.lower()
        for h in self.headings:
            if h.text.lower() == heading_lower:
                return self.sections.get(h.text)
        return None

    def get_table_by_line(self, line: int) -> Optional[TableData]:
        for t in self.tables:
            if abs(t.line - line) <= 2:
                return t
        return None

    def get_code_blocks_by_lang(self, lang: str) -> list:
        return [cb for cb in self.code_blocks if cb.language == lang]

    def find_heading(self, text: str) -> Optional[Heading]:
        text_lower = text.lower()
        for h in self.headings:
            if h.text.lower() == text_lower:
                return h
        for h in self.headings:
            if h.text.lower().startswith(text_lower):
                return h
        return None


# ── AST helpers ──────────────────────────────────────────────────────────────

def _iter_nodes(node: object):
    """Depth-first iteration over all nodes in a tree-sitter tree."""
    yield node
    for child in node.children:
        yield from _iter_nodes(child)


def _node_text(node: object) -> str:
    """Decode node bytes to str."""
    try:
        return node.text.decode("utf-8", errors="replace")
    except Exception:
        return ""


# ── Frontmatter ───────────────────────────────────────────────────────────────

def _extract_frontmatter(source: str) -> tuple:
    """Return (frontmatter_dict, body_start_line_index).
    body_start_line_index is the 0-indexed line AFTER the closing ---.
    Returns ({}, 0) if no frontmatter block is found.
    """
    # Strip BOM
    src = source.lstrip("\ufeff")
    if not src.startswith("---"):
        return {}, 0

    lines = src.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, 0

    # Find closing ---
    close_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            close_idx = i
            break

    if close_idx is None:
        return {}, 0

    fm_text = "\n".join(lines[1:close_idx])
    fm = _parse_yaml(fm_text)
    return fm, close_idx + 1


# ── Headings ──────────────────────────────────────────────────────────────────

def _extract_headings(tree: object, source: str) -> list:
    """Extract all headings from the tree. Falls back to regex if AST yields none."""
    headings = []

    try:
        for node in _iter_nodes(tree.root_node):
            if node.type == "atx_heading":
                level = 0
                text = ""
                for child in node.children:
                    t = child.type
                    if t.startswith("atx_h") and t.endswith("_marker"):
                        level = int(t[5])  # "atx_h2_marker" -> 2
                    elif t == "inline":
                        raw = _node_text(child).strip()
                        # strip bold/italic/code markers
                        text = re.sub(r"[*_`]", "", raw).strip()
                if level and text:
                    headings.append(Heading(
                        level=level,
                        text=text,
                        line=node.start_point[0] + 1,
                        node=node,
                    ))
            elif node.type == "setext_heading":
                level = 1
                text = ""
                for child in node.children:
                    if child.type == "setext_h1_underline":
                        level = 1
                    elif child.type == "setext_h2_underline":
                        level = 2
                    elif child.type == "paragraph":
                        text = re.sub(r"[*_`]", "", _node_text(child)).strip()
                if text:
                    headings.append(Heading(
                        level=level,
                        text=text,
                        line=node.start_point[0] + 1,
                        node=node,
                    ))
    except Exception as exc:
        LOG.warning("AST heading extraction failed (%s); using regex fallback", exc)

    if not headings:
        LOG.warning("No headings found via AST; using regex fallback")
        headings = _extract_headings_fallback(source)

    return sorted(headings, key=lambda h: h.line)


def _extract_headings_fallback(source: str) -> list:
    headings = []
    pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
    for i, line in enumerate(source.splitlines(), start=1):
        m = pattern.match(line)
        if m:
            headings.append(Heading(
                level=len(m.group(1)),
                text=re.sub(r"[*_`]", "", m.group(2)).strip(),
                line=i,
                node=None,
            ))
    return headings


# ── Sections ──────────────────────────────────────────────────────────────────

def _extract_sections(source: str, headings: list) -> dict:
    """Map heading text -> full section content (heading line + body)."""
    if not headings:
        return {}

    lines = source.splitlines()
    sections = {}

    for i, heading in enumerate(headings):
        start = heading.line - 1  # 0-indexed

        # Find end: next heading of same or higher level (lower number)
        end = len(lines)
        for j in range(i + 1, len(headings)):
            if headings[j].level <= heading.level:
                end = headings[j].line - 1
                break

        sections[heading.text] = "\n".join(lines[start:end])

    return sections


# ── Tables ────────────────────────────────────────────────────────────────────

def _extract_tables(tree: object, source: str) -> list:
    """Extract GFM tables. Falls back to line-based detection."""
    tables = []

    try:
        for node in _iter_nodes(tree.root_node):
            if node.type == "pipe_table":
                rows_nodes = [c for c in node.children
                              if c.type in ("pipe_table_header", "pipe_table_row")]
                if not rows_nodes:
                    continue

                # parse cells from a row node
                def parse_row(row_node):
                    return [
                        re.sub(r"[*_`]", "", _node_text(c)).strip()
                        for c in row_node.children
                        if c.type == "pipe_table_cell"
                    ]

                header_cells = parse_row(rows_nodes[0])
                data_rows = []
                for row_node in rows_nodes[1:]:
                    cells = parse_row(row_node)
                    if cells and not all(re.match(r"^[-: ]+$", c) for c in cells):
                        data_rows.append(dict(zip(header_cells, cells)))

                tables.append(TableData(
                    headers=header_cells,
                    rows=data_rows,
                    line=node.start_point[0] + 1,
                ))
    except Exception as exc:
        LOG.warning("AST table extraction failed (%s); using regex fallback", exc)

    if not tables:
        tables = _extract_tables_fallback(source)

    return tables


def _extract_tables_fallback(source: str) -> list:
    tables = []
    lines = source.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("|") and line.count("|") >= 2:
            # potential table start
            table_lines = []
            j = i
            while j < len(lines) and lines[j].strip().startswith("|"):
                table_lines.append(lines[j])
                j += 1

            # need at least header + delimiter + 1 data row
            if len(table_lines) >= 2:
                def split_row(r):
                    parts = r.strip().strip("|").split("|")
                    return [p.strip() for p in parts]

                header_cells = split_row(table_lines[0])
                data_rows = []
                for row_line in table_lines[1:]:
                    cells = split_row(row_line)
                    # skip delimiter rows
                    if all(re.match(r"^[-: ]+$", c) for c in cells if c):
                        continue
                    if cells:
                        data_rows.append(dict(zip(header_cells, cells)))

                if header_cells:
                    tables.append(TableData(
                        headers=header_cells,
                        rows=data_rows,
                        line=i + 1,
                    ))
            i = j
        else:
            i += 1
    return tables


# ── Code blocks ───────────────────────────────────────────────────────────────

def _extract_code_blocks(tree: object, source: str) -> list:
    """Extract fenced code blocks. Falls back to regex."""
    blocks = []

    try:
        for node in _iter_nodes(tree.root_node):
            if node.type == "fenced_code_block":
                lang = ""
                content = ""
                for child in node.children:
                    if child.type == "info_string":
                        lang = _node_text(child).strip()
                    elif child.type == "code_fence_content":
                        content = _node_text(child)
                        # strip exactly one leading + trailing newline
                        content = content.lstrip("\n").rstrip("\n")
                blocks.append(CodeBlock(
                    language=lang,
                    content=content,
                    line=node.start_point[0] + 1,
                ))
            elif node.type == "indented_code_block":
                content = _node_text(node).strip()
                blocks.append(CodeBlock(language="", content=content,
                                        line=node.start_point[0] + 1))
    except Exception as exc:
        LOG.warning("AST code block extraction failed (%s); using regex fallback", exc)

    if not blocks:
        blocks = _extract_code_blocks_fallback(source)

    return blocks


def _extract_code_blocks_fallback(source: str) -> list:
    blocks = []
    lines = source.splitlines()
    i = 0
    fence_pattern = re.compile(r"^(`{3,}|~{3,})(\w*)(.*)$")
    while i < len(lines):
        m = fence_pattern.match(lines[i])
        if m:
            fence_char = m.group(1)[0]
            lang = m.group(2).strip()
            start_line = i + 1
            fence_len = len(m.group(1))
            i += 1
            content_lines = []
            while i < len(lines):
                close = re.match(rf"^{re.escape(fence_char)}{{{fence_len},}}$",
                                 lines[i].strip())
                if close:
                    i += 1
                    break
                content_lines.append(lines[i])
                i += 1
            blocks.append(CodeBlock(
                language=lang,
                content="\n".join(content_lines),
                line=start_line,
            ))
        else:
            i += 1
    return blocks


# ── TOC ───────────────────────────────────────────────────────────────────────

def _build_toc(headings: list) -> list:
    stack: list = []
    result: list = []

    for h in headings:
        entry = TocEntry(level=h.level, text=h.text, line=h.line)
        # pop until we find a parent (lower level number = higher in hierarchy)
        while stack and stack[-1].level >= h.level:
            stack.pop()
        if not stack:
            result.append(entry)
        else:
            stack[-1].children.append(entry)
        stack.append(entry)

    return result


# ── MarkdownParser ────────────────────────────────────────────────────────────

class MarkdownParser:
    """Parse individual markdown files into ParsedDoc objects."""

    def __init__(self):
        # Each instance gets its own Parser (tree-sitter Parser is NOT thread-safe)
        self._parser = Parser(_get_language())

    def parse(self, text) -> object:
        """Parse raw markdown text (str or bytes) and return a tree-sitter Tree."""
        if isinstance(text, str):
            text = text.encode("utf-8")
        return self._parser.parse(text)

    def parse_file(self, path) -> ParsedDoc:
        """Parse a file at `path` and return a fully populated ParsedDoc."""
        path = Path(path)
        try:
            source = path.read_text(encoding="utf-8", errors="replace")
        except FileNotFoundError:
            raise

        return self._build_doc(path, source)

    def parse_string(self, text: str, path: Optional[Path] = None) -> ParsedDoc:
        """Parse raw markdown string content. path defaults to Path('<string>')."""
        if path is None:
            path = Path("<string>")
        return self._build_doc(path, text)

    def _build_doc(self, path: Path, source: str) -> ParsedDoc:
        try:
            tree = self.parse(source)
            fm, _body_start = _extract_frontmatter(source)
            headings = _extract_headings(tree, source)
            sections = _extract_sections(source, headings)
            tables = _extract_tables(tree, source)
            code_blocks = _extract_code_blocks(tree, source)
            toc = _build_toc(headings)
            return ParsedDoc(
                path=path,
                source=source,
                tree=tree,
                frontmatter=fm,
                headings=headings,
                sections=sections,
                tables=tables,
                code_blocks=code_blocks,
                toc=toc,
            )
        except Exception as exc:
            LOG.warning("Failed to fully parse %s: %s", path, exc)
            return ParsedDoc(path=path, source=source)


class MarkdownIndex:
    """Batch-parse a directory of markdown files."""

    def __init__(self, root):
        self.root = Path(root)
        self._docs: dict = {}

    def build(self, max_workers: int = 4) -> "MarkdownIndex":
        """Parse all *.md files under self.root in parallel."""
        files = list(self.root.rglob("*.md"))
        LOG.info("Indexing %d markdown files under %s", len(files), self.root)

        def _parse_one(p: Path) -> tuple:
            # Each thread gets its own MarkdownParser (thread safety)
            mp = MarkdownParser()
            return p, mp.parse_file(p)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(_parse_one, f): f for f in files}
            for future in as_completed(futures):
                try:
                    path, doc = future.result()
                    self._docs[path] = doc
                except Exception as exc:
                    LOG.warning("Failed to parse %s: %s", futures[future], exc)

        LOG.info("Indexed %d files", len(self._docs))
        return self

    def search(self, query: str) -> list:
        """Search all indexed docs for query string. Returns (path, heading, line).

        Searches both section body text and frontmatter values.
        """
        query_lower = query.lower()
        results = []
        for doc in self._docs.values():
            # Search section bodies
            for heading in doc.headings:
                section_text = doc.sections.get(heading.text, "")
                if query_lower in section_text.lower():
                    results.append((doc.path, heading.text, heading.line))
            # Search frontmatter values
            fm_text = " ".join(str(v) for v in doc.frontmatter.values()).lower()
            if query_lower in fm_text:
                results.append((doc.path, "<frontmatter>", 0))
        results.sort(key=lambda r: (str(r[0]), r[2]))
        return results

    def get_agent_map(self) -> dict:
        """Return {agent_name: ParsedDoc} keyed by frontmatter 'name' field."""
        return {
            doc.frontmatter.get("name", doc.path.stem): doc
            for doc in self._docs.values()
            if doc.frontmatter
        }

    def export_json(self, output) -> None:
        """Write the full index as JSON to output path."""
        output = Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)

        data = []
        for doc in self._docs.values():
            data.append({
                "path": str(doc.path),
                "frontmatter": doc.frontmatter,
                "headings": [
                    {"level": h.level, "text": h.text, "line": h.line}
                    for h in doc.headings
                ],
                "sections": doc.sections,
                "tables": [
                    {"headers": t.headers, "rows": t.rows, "line": t.line}
                    for t in doc.tables
                ],
                "code_blocks": [
                    {"language": cb.language, "content": cb.content, "line": cb.line}
                    for cb in doc.code_blocks
                ],
                "toc": _toc_to_dict(doc.toc),
            })

        output.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        LOG.info("Exported index to %s", output)


# ── JSON helpers ──────────────────────────────────────────────────────────────

def _toc_to_dict(entries: list) -> list:
    return [
        {
            "level": e.level,
            "text": e.text,
            "line": e.line,
            "children": _toc_to_dict(e.children),
        }
        for e in entries
    ]


__all__ = [
    "MarkdownParser",
    "MarkdownIndex",
    "ParsedDoc",
    "Heading",
    "TocEntry",
    "TableData",
    "CodeBlock",
]

# ── Integration note (for vector_router.py migration) ────────────────────────
# vector_router.py's _parse_frontmatter() can be replaced with:
#
#   from md_parser import MarkdownParser
#   _mp = MarkdownParser()
#
#   def _parse_frontmatter(text: str) -> dict:
#       doc = _mp.parse_string(text)
#       return doc.frontmatter
#
# This is a drop-in replacement that handles YAML lists, nested values,
# and encoding edge cases that the current regex-based approach cannot.


# ── Agent validator ───────────────────────────────────────────────────────────

_REQUIRED_FM_FIELDS = {"name", "version", "description", "model", "tools"}
_REQUIRED_SECTIONS_ALL = {
    "Negative Constraints",
    "Escalation Rules",
    "Output Format",
}
_REQUIRED_SECTIONS_CSUITE = {
    "Mandatory Trigger Rules",
    "Role in One Sentence",
}

def _validate_agent(doc: ParsedDoc) -> list:
    """Return list of findings for an agent .md file. Empty list = PASS."""
    findings = []

    # Skip non-agent files (no frontmatter)
    if not doc.frontmatter:
        return []

    # 1. Frontmatter fields
    missing_fm = _REQUIRED_FM_FIELDS - set(doc.frontmatter.keys())
    for f in sorted(missing_fm):
        findings.append(f"Missing frontmatter field: {f}")

    # 2. description must be non-empty
    desc = str(doc.frontmatter.get("description", "")).strip()
    if not desc:
        findings.append("description field is empty")
    elif len(desc) < 20:
        findings.append(f"description too short ({len(desc)} chars) — must describe invoke conditions")

    # 3. version must be semver-like
    version = str(doc.frontmatter.get("version", "")).strip()
    if not re.match(r"^\d+\.\d+\.\d+$", version):
        findings.append(f"version '{version}' is not semver (expected X.Y.Z)")

    # 4. Required sections (all agents)
    heading_texts_lower = {h.text.lower() for h in doc.headings}
    def _has_section(required: str) -> bool:
        req = required.lower()
        return any(h.startswith(req) for h in heading_texts_lower)

    for section in _REQUIRED_SECTIONS_ALL:
        if not _has_section(section):
            findings.append(f"Missing required section: {section}")

    # 5. C-suite detection: agents in c-suite/ or governance/ directories
    name = doc.frontmatter.get("name", "")
    model = doc.frontmatter.get("model", "")
    dept = doc.path.parent.name if doc.path != Path("<string>") else ""
    is_senior = dept in ("c-suite", "governance")
    if is_senior:
        for section in _REQUIRED_SECTIONS_CSUITE:
            if not _has_section(section):
                findings.append(f"Missing C-suite section: {section}")

    # 6. Negative Constraints must have ≥3 bullet points
    nc_h = doc.find_heading("Negative Constraints")
    nc_section = doc.sections.get(nc_h.text) if nc_h else None
    if nc_section:
        bullets = [l for l in nc_section.splitlines() if l.strip().startswith(("-", "*", "•"))]
        if len(bullets) < 3:
            findings.append(f"Negative Constraints has only {len(bullets)} bullet(s) — minimum 3 required")

    # 7. Output Format must not contain placeholder text
    of_h = doc.find_heading("Output Format")
    of_section = doc.sections.get(of_h.text) if of_h else None
    if of_section and "[domain fields]" in of_section.lower():
        findings.append("Output Format contains unfilled placeholder '[domain fields]'")

    return findings


# ── CLI ───────────────────────────────────────────────────────────────────────

_USAGE = """
md_parser — Tree-sitter markdown parser for the AI OS

Usage:
  python md_parser.py parse   <file>              Print structured summary
  python md_parser.py toc     <file>              Print table of contents
  python md_parser.py section <file> <heading>    Extract a section by heading
  python md_parser.py tables  <file>              Print all tables as JSON
  python md_parser.py code    <file> [--lang L]   Print code blocks
  python md_parser.py index   <dir>               Index all .md files in dir
  python md_parser.py search  <dir> <query>       Search across all .md files
  python md_parser.py agents                      Index ~/.claude/agents
  python md_parser.py validate <file|dir>         Check agent files against AGENT_STANDARDS
""".strip()


def _cli():
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

    # Force UTF-8 output on Windows so emoji/Unicode in headings don't crash print()
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    args = sys.argv[1:]
    if not args:
        print(_USAGE)
        sys.exit(0)

    cmd = args[0]

    try:
        if cmd == "parse":
            if len(args) < 2:
                print("Usage: md_parser.py parse <file>"); sys.exit(1)
            doc = MarkdownParser().parse_file(Path(args[1]))
            print(f"File     : {doc.path}")
            print(f"Frontmatter keys: {list(doc.frontmatter.keys())}")
            print(f"Headings : {len(doc.headings)}")
            print(f"Tables   : {len(doc.tables)}")
            print(f"Code blks: {len(doc.code_blocks)}")
            print(f"TOC depth: {max((h.level for h in doc.headings), default=0)}")
            if doc.frontmatter:
                print("\nFrontmatter:")
                for k, v in doc.frontmatter.items():
                    print(f"  {k}: {v}")

        elif cmd == "toc":
            if len(args) < 2:
                print("Usage: md_parser.py toc <file>"); sys.exit(1)
            doc = MarkdownParser().parse_file(Path(args[1]))
            if not doc.headings:
                print("No headings found.")
            for h in doc.headings:
                indent = "  " * (h.level - 1)
                print(f"{indent}H{h.level}: {h.text} (line {h.line})")

        elif cmd == "section":
            if len(args) < 3:
                print("Usage: md_parser.py section <file> <heading>"); sys.exit(1)
            doc = MarkdownParser().parse_file(Path(args[1]))
            heading = " ".join(args[2:])
            content = doc.get_section(heading)
            if content is None:
                print(f"Section not found: '{heading}'")
                print("Available headings:")
                for h in doc.headings:
                    print(f"  {h.text}")
            else:
                print(content)

        elif cmd == "tables":
            if len(args) < 2:
                print("Usage: md_parser.py tables <file>"); sys.exit(1)
            doc = MarkdownParser().parse_file(Path(args[1]))
            output = [
                {"headers": t.headers, "rows": t.rows, "line": t.line}
                for t in doc.tables
            ]
            print(json.dumps(output, indent=2, ensure_ascii=False))

        elif cmd == "code":
            if len(args) < 2:
                print("Usage: md_parser.py code <file> [--lang L]"); sys.exit(1)
            doc = MarkdownParser().parse_file(Path(args[1]))
            lang_filter = None
            if "--lang" in args:
                idx = args.index("--lang")
                if idx + 1 < len(args):
                    lang_filter = args[idx + 1]
            blocks = doc.get_code_blocks_by_lang(lang_filter) if lang_filter else doc.code_blocks
            if not blocks:
                print("No code blocks found.")
            for cb in blocks:
                print(f"\n--- [{cb.language or 'plain'}] line {cb.line} ---")
                print(cb.content)

        elif cmd == "index":
            if len(args) < 2:
                print("Usage: md_parser.py index <dir>"); sys.exit(1)
            idx = MarkdownIndex(Path(args[1])).build()
            total_headings = sum(len(d.headings) for d in idx._docs.values())
            total_tables = sum(len(d.tables) for d in idx._docs.values())
            total_code = sum(len(d.code_blocks) for d in idx._docs.values())
            print(f"Files    : {len(idx._docs)}")
            print(f"Headings : {total_headings}")
            print(f"Tables   : {total_tables}")
            print(f"Code blks: {total_code}")

        elif cmd == "search":
            if len(args) < 3:
                print("Usage: md_parser.py search <dir> <query>"); sys.exit(1)
            query = " ".join(args[2:])
            idx = MarkdownIndex(Path(args[1])).build()
            results = idx.search(query)
            if not results:
                print("No results found.")
            for path, heading, line in results:
                print(f"{path}:{line}  [{heading}]")

        elif cmd == "agents":
            idx = MarkdownIndex(AGENTS_DIR).build()
            agent_map = idx.get_agent_map()
            # Print: name | dept (from path) | version | model
            print(f"{'Agent':<40} {'Dept':<25} {'Version':<10} {'Model':<12}")
            print("-" * 90)
            for name in sorted(agent_map.keys()):
                doc = agent_map[name]
                # department = first subdir under agents/
                parts = doc.path.relative_to(AGENTS_DIR).parts
                dept = parts[0] if len(parts) > 1 else "-"
                version = doc.frontmatter.get("version", "-")
                model = doc.frontmatter.get("model", "-")
                print(f"{name:<40} {dept:<25} {version:<10} {model:<12}")
            print(f"\nTotal: {len(agent_map)} agents")

        elif cmd == "validate":
            if len(args) < 2:
                print("Usage: md_parser.py validate <file|dir>"); sys.exit(1)
            target = Path(args[1])
            files = list(target.rglob("*.md")) if target.is_dir() else [target]
            mp = MarkdownParser()
            total = passed = 0
            for f in sorted(files):
                findings = _validate_agent(mp.parse_file(f))
                total += 1
                if not findings:
                    passed += 1
                    print(f"  PASS  {f.name}")
                else:
                    print(f"  FAIL  {f.name}")
                    for issue in findings:
                        print(f"         • {issue}")
            print(f"\n{passed}/{total} passed")
            if passed < total:
                sys.exit(1)

        else:
            print(f"Unknown command: {cmd}\n")
            print(_USAGE)
            sys.exit(1)

    except FileNotFoundError as exc:
        print(f"Error: {exc}")
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as exc:
        LOG.exception("Unexpected error in CLI: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    _cli()
