"""
AI OS Vector Router
===================
Semantic agent lookup backed by ChromaDB + all-MiniLM-L6-v2 (auto-downloaded ~90 MB).

Usage
-----
    from vector_router import query_agents, build_index

    # First run (or after agent changes):
    build_index()

    # Every query:
    results = query_agents("I need to analyze competitive threats")
    for r in results:
        print(r["agent"], r["department"], r["score"])

CLI
---
    python vector_router.py build
    python vector_router.py query "I need a security review"
    python vector_router.py query "analyze stock performance" --n 3
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

# ── Paths ─────────────────────────────────────────────────────────────────────
AGENTS_DIR = Path.home() / ".claude" / "agents"
DB_DIR = Path.home() / ".claude" / "vector_db"
COLLECTION_NAME = "ai_os_agents"

# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Extract YAML frontmatter and body from an agent .md file."""
    meta: dict = {}
    body = text

    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            fm_block = text[3:end].strip()
            body = text[end + 3:].strip()
            for line in fm_block.splitlines():
                if ":" in line:
                    key, _, val = line.partition(":")
                    meta[key.strip()] = val.strip()
    return meta, body


def _extract_invoke_section(body: str) -> str:
    """Pull the 'Invoke when' / 'When to use' paragraph from the agent body."""
    patterns = [
        r"(?i)invoke\s+when[:\s]+(.*?)(?=\n#|\n\n|\Z)",
        r"(?i)when\s+to\s+(use|invoke)[:\s]+(.*?)(?=\n#|\n\n|\Z)",
        r"(?i)use\s+this\s+agent\s+when[:\s]+(.*?)(?=\n#|\n\n|\Z)",
    ]
    for pat in patterns:
        m = re.search(pat, body, re.DOTALL)
        if m:
            return re.sub(r"\s+", " ", m.group(1)).strip()[:400]
    return ""


def _build_document(meta: dict, body: str) -> str:
    """Combine description + invoke-when into a single embeddable string."""
    desc = meta.get("description", "")
    invoke = _extract_invoke_section(body)
    parts = [p for p in [desc, invoke] if p]
    return " | ".join(parts)


def _get_department(file_path: Path) -> str:
    """Infer department from the folder name."""
    parts = file_path.parts
    agents_idx = next((i for i, p in enumerate(parts) if p == "agents"), None)
    if agents_idx is not None and agents_idx + 1 < len(parts):
        dept = parts[agents_idx + 1]
        return dept if dept != file_path.name else "unknown"
    return "unknown"


def _get_client() -> chromadb.PersistentClient:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(DB_DIR))


# ── Public API ────────────────────────────────────────────────────────────────

def build_index(verbose: bool = True) -> int:
    """
    Scan all agent .md files under AGENTS_DIR, embed them, and (re)build the
    ChromaDB collection. Returns the number of agents indexed.
    """
    client = _get_client()
    ef = DefaultEmbeddingFunction()

    # Wipe and recreate the collection for a clean rebuild
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(COLLECTION_NAME, embedding_function=ef)

    agent_files = list(AGENTS_DIR.rglob("*.md"))
    if not agent_files:
        print(f"[vector_router] No agent files found under {AGENTS_DIR}")
        return 0

    documents, metadatas, ids = [], [], []

    for fp in agent_files:
        try:
            raw = fp.read_text(encoding="utf-8")
        except Exception:
            continue

        meta, body = _parse_frontmatter(raw)
        agent_name = meta.get("name") or fp.stem
        doc = _build_document(meta, body)

        if not doc.strip():
            continue  # skip empty docs

        dept = _get_department(fp)
        agent_id = re.sub(r"[^a-zA-Z0-9_-]", "_", agent_name)

        documents.append(doc)
        metadatas.append({
            "agent_name": agent_name,
            "department": dept,
            "file_path": str(fp),
            "model": meta.get("model", ""),
            "version": meta.get("version", ""),
        })
        ids.append(agent_id)

    if documents:
        BATCH = 500
        total = len(documents)
        for i in range(0, total, BATCH):
            collection.add(
                documents=documents[i:i + BATCH],
                metadatas=metadatas[i:i + BATCH],
                ids=ids[i:i + BATCH],
            )
            if verbose:
                done = min(i + BATCH, total)
                print(f"[vector_router] Indexed {done}/{total}...", end="\r", flush=True)

    if verbose:
        print(f"[vector_router] Indexed {len(documents)} agents -> {DB_DIR}    ")

    return len(documents)


def query_agents(
    query: str,
    n: int = 5,
    department_filter: Optional[str] = None,
) -> list[dict]:
    """
    Semantic search over indexed agents.

    Returns a list of dicts:
        {
          "agent":      str,   # agent name
          "department": str,
          "score":      float, # cosine distance (lower = more similar)
          "file_path":  str,
          "model":      str,
          "excerpt":    str,   # first 200 chars of indexed document
        }
    """
    client = _get_client()
    ef = DefaultEmbeddingFunction()

    try:
        collection = client.get_collection(COLLECTION_NAME, embedding_function=ef)
    except Exception:
        raise RuntimeError(
            "Vector index not found. Run build_index() first:\n"
            "  python ~/.claude/vector_router.py build"
        )

    where = {"department": department_filter} if department_filter else None

    actual_n = min(n, collection.count())
    if actual_n < n:
        print(f"[vector_router] Note: requested {n} results but only {actual_n} agents indexed.")

    results = collection.query(
        query_texts=[query],
        n_results=actual_n,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    output = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        output.append({
            "agent":      meta.get("agent_name", ""),
            "department": meta.get("department", ""),
            "score":      round(dist, 4),
            "file_path":  meta.get("file_path", ""),
            "model":      meta.get("model", ""),
            "excerpt":    doc[:200],
        })

    return output


def rebuild_index() -> int:
    """Alias for build_index — drop-in for scheduled or post-agent-change calls."""
    return build_index(verbose=True)


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    args = sys.argv[1:]

    if not args or args[0] == "build":
        count = build_index()
        print(f"Done. {count} agents indexed.")

    elif args[0] == "query":
        if len(args) < 2:
            print("Usage: python vector_router.py query <text> [--n N] [--dept DEPT]")
            sys.exit(1)

        query_text = args[1]
        n = 5
        dept = None

        for i, a in enumerate(args[2:], 2):
            if a == "--n" and i + 1 < len(args):
                n = int(args[i + 1])
            if a == "--dept" and i + 1 < len(args):
                dept = args[i + 1]

        hits = query_agents(query_text, n=n, department_filter=dept)
        print(f"\nTop {len(hits)} agents for: \"{query_text}\"\n")
        print(f"{'Agent':<35} {'Dept':<15} {'Score':<8} Model")
        print("-" * 75)
        for h in hits:
            print(f"{h['agent']:<35} {h['department']:<15} {h['score']:<8} {h['model']}")
        print()

    else:
        print("Commands: build | query <text> [--n N] [--dept DEPT]")
        sys.exit(1)
