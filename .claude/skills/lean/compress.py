#!/usr/bin/env python3
"""
compress.py — Bidirectional token compressor for the /lean skill.
Uses the LEAN_DICT substitution table to reduce token usage.

Usage:
    python compress.py "text to compress"
    echo "text to compress" | python compress.py
    python compress.py --decompress "impl cfg auth"
    python compress.py --stats-only "text to analyze"
"""

import sys
import re
import argparse

# ─────────────────────────────────────────────────────────────────────────────
# COMPRESSION DICTIONARY
# Ordered by length DESC so longer phrases match before substrings.
# Format: (full_form, compressed_form, category)
# ─────────────────────────────────────────────────────────────────────────────

PHRASES = [
    # Verbose phrases → short (highest savings, check FIRST)
    ("it is worth noting that", "note:", "phrase"),
    ("due to the fact that", "bc", "phrase"),
    ("please note that", "note:", "phrase"),
    ("it should be noted", "note:", "phrase"),
    ("keep in mind that", "note:", "phrase"),
    ("as mentioned above", "(see above)", "phrase"),
    ("as I mentioned", "(above)", "phrase"),
    ("at this point in time", "now", "phrase"),
    ("for the purpose of", "to", "phrase"),
    ("in the event that", "if", "phrase"),
    ("in order for", "for", "phrase"),
    ("in order to", "to", "phrase"),
    ("with regard to", "re:", "phrase"),
    ("with respect to", "re:", "phrase"),
    ("on the other hand", "but", "phrase"),
    ("as a result of", "so", "phrase"),
    ("a number of", "several", "phrase"),
    ("the fact that", "that", "phrase"),
    ("in addition to", "also", "phrase"),
    ("at the same time", "also", "phrase"),
    ("in terms of", "for", "phrase"),
    ("a lot of", "many", "phrase"),
    ("make sure that", "ensure", "phrase"),
    ("as well as", "&", "phrase"),
]

WORDS = [
    # Technical (highest per-word savings)
    ("implementation", "impl", "tech"),
    ("authentication", "auth", "tech"),
    ("authorization", "authz", "tech"),
    ("configuration", "cfg", "tech"),
    ("infrastructure", "infra", "tech"),
    ("orchestration", "orch", "tech"),
    ("specification", "spec", "tech"),
    ("initialization", "init", "tech"),
    ("synchronization", "sync", "tech"),
    ("documentation", "docs", "tech"),
    ("optimization", "opt", "tech"),
    ("notification", "notif", "tech"),
    ("architecture", "arch", "tech"),
    ("asynchronous", "async", "tech"),
    ("performance", "perf", "tech"),
    ("integration", "integ", "tech"),
    ("requirement", "reqmt", "tech"),
    ("dependency", "dep", "tech"),
    ("repository", "repo", "tech"),
    ("deployment", "deploy", "tech"),
    ("environment", "env", "tech"),
    ("development", "dev", "tech"),
    ("production", "prod", "tech"),
    ("application", "app", "tech"),
    ("information", "info", "tech"),
    ("parameter", "param", "tech"),
    ("interface", "iface", "tech"),
    ("component", "comp", "tech"),
    ("container", "ctr", "tech"),
    ("exception", "exc", "tech"),
    ("callback", "cb", "tech"),
    ("database", "db", "tech"),
    ("response", "resp", "tech"),
    ("function", "fn", "tech"),
    ("variable", "var", "tech"),
    ("boolean", "bool", "tech"),
    ("message", "msg", "tech"),
    ("process", "proc", "tech"),
    ("service", "svc", "tech"),
    ("version", "ver", "tech"),
    ("integer", "int", "tech"),
    ("request", "req", "tech"),
    ("object", "obj", "tech"),
    ("string", "str", "tech"),
    ("buffer", "buf", "tech"),
    ("module", "mod", "tech"),
    ("error", "err", "tech"),
    # Common English (medium savings)
    ("approximately", "~", "en"),
    ("additional", "addl", "en"),
    ("something", "smth", "en"),
    ("everything", "evth", "en"),
    ("available", "avail", "en"),
    ("necessary", "nec", "en"),
    ("different", "diff", "en"),
    ("probably", "prob", "en"),
    ("previous", "prev", "en"),
    ("original", "orig", "en"),
    ("between", "btn", "en"),
    ("without", "w/o", "en"),
    ("because", "bc", "en"),
    ("maximum", "max", "en"),
    ("minimum", "min", "en"),
    ("nothing", "nth", "en"),
    ("through", "thru", "en"),
    ("current", "curr", "en"),
    ("similar", "sim", "en"),
    ("already", "alr", "en"),
    ("within", "w/in", "en"),
    ("though", "tho", "en"),
    ("always", "alw", "en"),
    ("before", "b4", "en"),
    ("reference", "ref", "en"),
    ("about", "abt", "en"),
]

# Filler openings to strip from the start of text
FILLER_OPENINGS = [
    r"^Great question[!.]\s*",
    r"^Certainly[!.]\s*",
    r"^Of course[!.]\s*",
    r"^Sure[!.]\s*",
    r"^Happy to help[!.]\s*",
    r"^I['']d be happy to\s+",
    r"^I['']ll help you with that[.!]\s*",
    r"^Let me help you with\s+",
    r"^I would like to\s+",
]

# Filler endings to strip from the end of text
FILLER_ENDINGS = [
    r"\s*Let me know if you need anything else[.!]*$",
    r"\s*Feel free to ask[.!]*$",
    r"\s*Hope that helps[!.]*$",
    r"\s*Is there anything else I can (assist|help) (with|you with)[?]*$",
    r"\s*Don't hesitate to (ask|reach out)[.!]*$",
]


def estimate_tokens(text: str) -> int:
    """Rough BPE token estimate: ~4 chars/token for prose, 3 for technical."""
    # Use 3.5 as a blended estimate (mix of prose + technical)
    return max(1, round(len(text) / 3.5))


def compress(text: str, verbose: bool = False) -> tuple[str, dict]:
    """
    Compress text using phrase + word substitutions.
    Returns: (compressed_text, stats_dict)
    """
    original = text
    result = text

    # 1. Strip filler openings
    for pattern in FILLER_OPENINGS:
        result = re.sub(pattern, "", result, flags=re.IGNORECASE)

    # 2. Strip filler endings
    for pattern in FILLER_ENDINGS:
        result = re.sub(pattern, "", result, flags=re.IGNORECASE)

    result = result.strip()

    # 3. Apply phrase substitutions (case-insensitive, preserve surrounding space)
    phrase_hits = 0
    for full, short, _ in PHRASES:
        new = re.sub(re.escape(full), short, result, flags=re.IGNORECASE)
        if new != result:
            phrase_hits += 1
            result = new

    # 4. Apply word substitutions (whole-word match only, preserve case for acronyms)
    word_hits = 0
    for full, short, _ in WORDS:
        # Match whole word, case-insensitive
        pattern = r'\b' + re.escape(full) + r'\b'
        new = re.sub(pattern, short, result, flags=re.IGNORECASE)
        if new != result:
            word_hits += 1
            result = new

    orig_tokens = estimate_tokens(original)
    comp_tokens = estimate_tokens(result)
    savings_pct = round((1 - comp_tokens / orig_tokens) * 100, 1) if orig_tokens > 0 else 0

    stats = {
        "original_chars": len(original),
        "compressed_chars": len(result),
        "original_tokens_est": orig_tokens,
        "compressed_tokens_est": comp_tokens,
        "savings_pct": savings_pct,
        "phrase_hits": phrase_hits,
        "word_hits": word_hits,
    }

    return result, stats


# ─────────────────────────────────────────────────────────────────────────────
# TELEGRAPH MODE
# Drops filler words entirely instead of substituting them.
# Articles (a/an/the), sentence-start fillers, and optional copula transforms.
# ─────────────────────────────────────────────────────────────────────────────

# Always-safe drops: articles
TELEGRAPH_ARTICLES = ["the", "a", "an"]

# Sentence/line-start filler patterns to drop
TELEGRAPH_START_DROPS = [
    r'^(it is|it\'s)\s+',
    r'^(there is|there are|there\'s)\s+',
    r'^(this is|this was)\s+',
    r'^(they are|they\'re)\s+',
]

# Copula transforms: " is " / " are " → ": "
TELEGRAPH_COPULAS = [
    (r'\s+is\s+', ': '),
    (r'\s+are\s+', ': '),
    (r'\s+was\s+', ': '),
    (r'\s+were\s+', ': '),
]


def telegraph(text: str, copulas: bool = False) -> tuple[str, dict]:
    """
    Telegraph-style compression: drops filler words entirely.
    Runs per-line so sentence-start patterns apply to each line/bullet.
    Args:
        text: input text
        copulas: if True, also transform is/are/was/were → ':'
    Returns: (compressed_text, stats_dict)
    """
    original = text
    lines = text.split('\n')
    processed = []
    drop_count = 0

    for line in lines:
        result = line

        # 1. Sentence-start filler drops (per line)
        for pattern in TELEGRAPH_START_DROPS:
            new = re.sub(pattern, '', result, flags=re.IGNORECASE)
            if new != result:
                drop_count += 1
                result = new

        # 2. Article drops (whole word, anywhere in line)
        for word in TELEGRAPH_ARTICLES:
            pattern = r'\b' + re.escape(word) + r'\b\s*'
            new = re.sub(pattern, ' ', result, flags=re.IGNORECASE)
            if new != result:
                drop_count += len(re.findall(pattern, result, flags=re.IGNORECASE))
                result = new

        # 3. Optional copula transforms
        if copulas:
            for pattern, replacement in TELEGRAPH_COPULAS:
                result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

        # 4. Clean up: collapse multiple spaces, strip leading/trailing
        result = re.sub(r'  +', ' ', result).strip()
        # Fix ": :" artifacts
        result = re.sub(r':\s*:', ':', result)

        processed.append(result)

    compressed = '\n'.join(processed)

    orig_tokens = estimate_tokens(original)
    comp_tokens = estimate_tokens(compressed)
    savings_pct = round((1 - comp_tokens / orig_tokens) * 100, 1) if orig_tokens > 0 else 0

    stats = {
        "original_chars": len(original),
        "compressed_chars": len(compressed),
        "original_tokens_est": orig_tokens,
        "compressed_tokens_est": comp_tokens,
        "savings_pct": savings_pct,
        "drops": drop_count,
    }

    return compressed, stats


def decompress(text: str) -> str:
    """
    Expand compressed form back to full words.
    Uses reverse mapping — note: lossy for phrases (short → one possible full form).
    """
    result = text

    # Reverse word subs (skip phrases — too ambiguous to reverse)
    for full, short, _ in WORDS:
        pattern = r'\b' + re.escape(short) + r'\b'
        result = re.sub(pattern, full, result, flags=re.IGNORECASE)

    return result


def print_stats(original: str, compressed: str, stats: dict) -> None:
    bar_len = 30
    savings = stats["savings_pct"]
    filled = round(savings / 100 * bar_len)
    bar = "#" * filled + "-" * (bar_len - filled)

    print(f"\n{'-'*50}")
    print(f"ORIGINAL ({stats['original_chars']} chars | ~{stats['original_tokens_est']} tokens):")
    print(f"  {original[:200]}{'...' if len(original) > 200 else ''}")
    print()
    print(f"COMPRESSED ({stats['compressed_chars']} chars | ~{stats['compressed_tokens_est']} tokens):")
    print(f"  {compressed[:200]}{'...' if len(compressed) > 200 else ''}")
    print()
    print(f"SAVINGS: {savings}%  [{bar}]")
    if 'drops' in stats:
        print(f"  Word drops: {stats['drops']}")
    else:
        print(f"  Phrase substitutions: {stats['phrase_hits']}")
        print(f"  Word substitutions:   {stats['word_hits']}")
    print(f"{'-'*50}\n")


def main():
    parser = argparse.ArgumentParser(description="Lean mode token compressor")
    parser.add_argument("text", nargs="?", help="Text to compress (or reads stdin)")
    parser.add_argument("--decompress", "-d", action="store_true",
                        help="Decompress compressed text back to full words")
    parser.add_argument("--stats-only", "-s", action="store_true",
                        help="Show stats without printing compressed text")
    parser.add_argument("--quiet", "-q", action="store_true",
                        help="Output only compressed text, no stats")
    parser.add_argument("--telegraph", "-t", action="store_true",
                        help="Telegraph mode: drop articles & filler words instead of substituting")
    parser.add_argument("--copulas", "-c", action="store_true",
                        help="With --telegraph: also transform is/are/was/were → ':'")
    args = parser.parse_args()

    # Get input text
    if args.text:
        text = args.text
    elif not sys.stdin.isatty():
        text = sys.stdin.read().strip()
    else:
        parser.print_help()
        sys.exit(1)

    if args.decompress:
        result = decompress(text)
        print(result)
        return

    if args.telegraph:
        compressed, stats = telegraph(text, copulas=args.copulas)
        label = "TELEGRAPH"
    else:
        compressed, stats = compress(text)
        label = "COMPRESSED"

    if args.quiet:
        print(compressed)
    elif args.stats_only:
        print_stats(text, compressed, stats)
    else:
        print(f"[{label}]")
        print(compressed)
        if not args.quiet:
            print_stats(text, compressed, stats)


if __name__ == "__main__":
    main()
