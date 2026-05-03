"""
tptp_loader.py
--------------
Loads TPTP .p problem files and converts them into (label, Formula, comment)
triples compatible with the evaluate() function in run.py.

Each TPTP file contains one or more fof(...) statements. We:
  1. Read the % Status header to determine expected result (provable/unprovable).
  2. Collect axiom/hypothesis formulas and the conjecture.
  3. Combine as: (ax1 & ax2 & ...) => conjecture, or just conjecture if no axioms.

Skips files that:
  - Have no conjecture
  - Contain equality (=) — our prover has no equality rules
  - Have status other than Theorem or Non-Theorem/CounterSatisfiable
"""

from __future__ import annotations
import os
import re
import sys
import glob
from formula import And, Implies
from tptp_parser import parse_tptp_formula

# ── Single-file loader ────────────────────────────────────────────────────────

# Roles treated as axioms
_AXIOM_ROLES = {'axiom', 'hypothesis', 'assumption', 'lemma', 'theorem'}

# fof(...) block: captures role and formula text
# We use a simple approach: find fof( then scan for matching closing ').'
_FOF_RE = re.compile(r'\bfof\s*\(', re.IGNORECASE)


def _extract_fof_blocks(text: str) -> list[tuple[str, str]]:
    """
    Returns list of (role, formula_text) for each fof(...). statement.
    Handles nested parentheses correctly.
    """
    results = []
    for m in _FOF_RE.finditer(text):
        start = m.end()  # position after 'fof('
        # find the comma separating name from role
        depth = 1
        i = start
        while i < len(text) and depth > 0:
            if text[i] == '(':
                depth += 1
            elif text[i] == ')':
                depth -= 1
            i += 1
        # text[start:i-1] is the full content of fof(...)
        content = text[start:i - 1].strip()

        # Split on commas at depth 0 to get: name, role, formula
        parts = []
        depth = 0
        current = []
        for ch in content:
            if ch == ',' and depth == 0:
                parts.append(''.join(current).strip())
                current = []
            else:
                if ch == '(':
                    depth += 1
                elif ch == ')':
                    depth -= 1
                current.append(ch)
        parts.append(''.join(current).strip())

        if len(parts) < 3:
            continue
        role = parts[1].strip().lower()
        formula_text = ','.join(parts[2:]).strip()  # rejoin in case formula had commas
        results.append((role, formula_text))
    return results


def load_tptp_file(path: str) -> tuple[str, object, str] | None:
    """
    Parse one TPTP .p file.
    Returns (label, formula, comment) or None if the file should be skipped.
      label   = 'provable' | 'unprovable'
      formula = Formula object
      comment = filename (for display)
    """
    try:
        with open(path, encoding='utf-8', errors='ignore') as f:
            text = f.read()
    except OSError:
        return None

    # Skip files that use equality =
    # (equality appears as '=' between terms, not inside strings)
    # A rough but effective filter: look for ' = ' or '!=' in formula positions
    if re.search(r'\s=\s|!=', text):
        return None

    # Determine expected result from % Status comment
    status_match = re.search(r'%\s*Status\s*:\s*(\w+)', text)
    if not status_match:
        return None
    status = status_match.group(1).lower()
    if status == 'theorem':
        label = 'provable'
    elif status in ('non-theorem', 'countersatisfiable', 'unsatisfiable', 'satisfiable'):
        # non-theorem / countersatisfiable → the conjecture is not provable
        # unsatisfiable / satisfiable without conjecture → skip
        label = 'unprovable'
    else:
        return None  # unknown / open / unknown

    blocks = _extract_fof_blocks(text)
    if not blocks:
        return None

    axioms = []
    conjecture = None
    for role, formula_text in blocks:
        try:
            formula = parse_tptp_formula(formula_text)
        except (SyntaxError, IndexError, KeyError):
            return None  # unparseable — skip whole file
        if role == 'conjecture':
            conjecture = formula
        elif role in _AXIOM_ROLES:
            axioms.append(formula)

    if conjecture is None:
        return None

    # Build combined formula
    if axioms:
        premise = axioms[0]
        for ax in axioms[1:]:
            premise = And(premise, ax)
        combined = Implies(premise, conjecture)
    else:
        combined = conjecture

    comment = os.path.basename(path)
    return label, combined, comment


# ── Directory loader ──────────────────────────────────────────────────────────

def _progress(done: int, total: int, loaded: int, skipped: int, width: int = 40) -> None:
    """Print an in-place progress bar to stderr."""
    frac = done / total if total else 0
    filled = int(width * frac)
    bar = '█' * filled + '░' * (width - filled)
    sys.stderr.write(
        f"\r  [{bar}] {done}/{total}  loaded={loaded}  skipped={skipped} "
    )
    sys.stderr.flush()


def load_tptp_dir(dir_path: str, limit: int = 100) -> list[tuple[str, object, str]]:
    """
    Load up to `limit` usable problems from a TPTP problems directory.
    Shows a live progress bar while scanning files.
    """
    all_files = sorted(glob.glob(os.path.join(dir_path, '*.p')))
    total = len(all_files)
    entries = []
    skipped = 0

    for i, path in enumerate(all_files, 1):
        _progress(i, total, len(entries), skipped)
        result = load_tptp_file(path)
        if result is None:
            skipped += 1
            continue
        entries.append(result)
        if len(entries) >= limit:
            _progress(i, total, len(entries), skipped)
            break

    # finish the bar and move to a new line
    _progress(total, total, len(entries), skipped)
    sys.stderr.write('\n')
    sys.stderr.flush()

    if skipped:
        print(f"  [tptp] skipped {skipped}/{total} files (equality / unparseable / unknown status)")
    return entries


# ── Auto-detect TPTP installation ─────────────────────────────────────────────

def find_tptp_root(base_dir: str) -> str | None:
    """
    Look for a TPTP-v*.*.* directory that contains a Problems/ subdirectory.
    Searches base_dir and one level deeper to handle nested extraction.
    """
    # direct children: base_dir/TPTP-v*/
    candidates = sorted(glob.glob(os.path.join(base_dir, 'TPTP-v*')))
    # one level deeper: base_dir/TPTP-v*/TPTP-v*/
    for c in list(candidates):
        candidates += sorted(glob.glob(os.path.join(c, 'TPTP-v*')))
    # return the deepest one that actually has a Problems/ dir
    for path in reversed(candidates):
        if os.path.isdir(os.path.join(path, 'Problems')):
            return path
    return None


def tptp_problems_dir(base_dir: str, domain: str = 'SYN') -> str | None:
    """
    Return the path to TPTP Problems/<domain>/ inside the auto-detected
    TPTP root, or None if the archive is not present.
    """
    root = find_tptp_root(base_dir)
    if root is None:
        return None
    path = os.path.join(root, 'Problems', domain)
    return path if os.path.isdir(path) else None
