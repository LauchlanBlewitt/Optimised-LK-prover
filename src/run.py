"""
benchmarks/run.py
-----------------
Evaluates both provers against all benchmark files and prints a results
table per source and tier. Run from inside the prover/ directory:

    python benchmarks/run.py
"""

import os
import sys
import time
import csv
import signal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from parser import parse_formula
from prover import Prover
from improved_prover import ImprovedProver
from tptp_loader import load_tptp_dir, tptp_problems_dir

SOURCES = ["generated", "classical", "stress"]
TIERS   = ["propositional", "easy", "medium", "hard"]
BENCH_DIR = os.path.dirname(__file__)

# Maximum seconds allowed per formula per prover (None = no limit)
FORMULA_TIMEOUT = 30


# ── File reader ──────────────────────────────────────────────────────────────

def load_benchmark(path: str) -> list[tuple[str, object, str]]:
    entries = []
    comment = ""
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith(";"):
                comment = line[1:].strip()
                continue
            parts = line.split(None, 1)
            if len(parts) == 2:
                label, src = parts
                try:
                    entries.append((label, parse_formula(src), comment))
                except SyntaxError as e:
                    print(f"  [skip] {e}")
    return entries


# ── Timeout helper ───────────────────────────────────────────────────────────

class _Timeout(Exception):
    pass

def _prove_with_timeout(prover, formula, timeout_secs):
    """
    Run prover.prove(formula) with a hard wall-clock timeout.
    Returns (result, proof) on success, or (None, None) if time expires.
    Uses SIGALRM (macOS/Linux only).
    """
    if timeout_secs is None:
        return prover.prove(formula)

    def _handler(signum, frame):
        raise _Timeout()

    old = signal.signal(signal.SIGALRM, _handler)
    signal.alarm(timeout_secs)
    try:
        result = prover.prove(formula)
    except _Timeout:
        result = (None, None)
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)
    return result


# ── Tier evaluator ───────────────────────────────────────────────────────────

def evaluate(entries, baseline, improved, label: str = ""):
    b_solved = b_correct = b_time = 0
    i_solved = i_correct = i_time = 0
    n_provable = sum(1 for l, _, _ in entries if l == "provable")
    n_unprovable = len(entries) - n_provable

    b_prov_correct = b_unprov_correct = 0
    i_prov_correct = i_unprov_correct = 0

    i_better = b_better = both_correct = both_wrong = 0
    i_better_prov = i_better_unprov = 0
    b_better_prov = b_better_unprov = 0

    total = len(entries)
    tag = label.strip() or "evaluating"

    for idx, (lbl, formula, _) in enumerate(entries, 1):
        # live progress bar
        width = 30
        filled = int(width * idx / total)
        bar = '█' * filled + '░' * (width - filled)
        b_acc = f"{100*b_correct/idx:4.0f}%" if idx > 1 else "  -- "
        i_acc = f"{100*i_correct/idx:4.0f}%" if idx > 1 else "  -- "
        sys.stderr.write(
            f"\r  {tag:<24} [{bar}] {idx:>3}/{total}  "
            f"B:{b_acc}  I:{i_acc}  "
        )
        sys.stderr.flush()

        expected = (lbl == "provable")

        t0 = time.perf_counter()
        bp, _ = _prove_with_timeout(baseline, formula, FORMULA_TIMEOUT)
        b_time += time.perf_counter() - t0
        if bp is None:  # timed out → treat as unprovable
            bp = False

        t0 = time.perf_counter()
        ip, _ = _prove_with_timeout(improved, formula, FORMULA_TIMEOUT)
        i_time += time.perf_counter() - t0
        if ip is None:
            ip = False

        b_correct += bp == expected
        i_correct += ip == expected

        if expected:
            b_prov_correct += bp == expected
            i_prov_correct += ip == expected
        else:
            b_unprov_correct += bp == expected
            i_unprov_correct += ip == expected

        b_ok = (bp == expected)
        i_ok = (ip == expected)
        if i_ok and not b_ok:
            i_better += 1
            if expected:
                i_better_prov += 1
            else:
                i_better_unprov += 1
        elif b_ok and not i_ok:
            b_better += 1
            if expected:
                b_better_prov += 1
            else:
                b_better_unprov += 1
        elif b_ok and i_ok:
            both_correct += 1
        else:
            both_wrong += 1

        if bp and expected: b_solved += 1
        if ip and expected: i_solved += 1

    # finish progress line
    sys.stderr.write('\n')
    sys.stderr.flush()

    return {
        "n":          len(entries),
        "n_provable": n_provable,
        "n_unprovable": n_unprovable,
        "b_solved":   b_solved,   "b_correct": b_correct,   "b_time": b_time,
        "i_solved":   i_solved,   "i_correct": i_correct,   "i_time": i_time,
        "b_prov_correct": b_prov_correct,
        "b_unprov_correct": b_unprov_correct,
        "i_prov_correct": i_prov_correct,
        "i_unprov_correct": i_unprov_correct,
        "i_better": i_better,
        "b_better": b_better,
        "both_correct": both_correct,
        "both_wrong": both_wrong,
        "i_better_prov": i_better_prov,
        "i_better_unprov": i_better_unprov,
        "b_better_prov": b_better_prov,
        "b_better_unprov": b_better_unprov,
    }


# ── Report ───────────────────────────────────────────────────────────────────

def _fmt_ms(seconds: float) -> str:
    return f"{seconds * 1000:,.1f} ms"


def _fmt_ms_num(seconds: float) -> str:
    return f"{seconds * 1000:,.1f}"


def _fmt_pct(part: int, whole: int) -> str:
    return f"{(100 * part / whole):5.1f}%" if whole else "  n/a"


def _zero_totals() -> dict:
    return {
        "n":0, "n_provable":0, "n_unprovable":0,
        "b_solved":0, "b_correct":0, "b_time":0,
        "i_solved":0, "i_correct":0, "i_time":0,
        "b_prov_correct":0, "b_unprov_correct":0,
        "i_prov_correct":0, "i_unprov_correct":0,
        "i_better":0, "b_better":0, "both_correct":0, "both_wrong":0,
        "i_better_prov":0, "i_better_unprov":0,
        "b_better_prov":0, "b_better_unprov":0,
    }


def _sum_rows(rows: list[tuple[str, dict]]) -> dict:
    totals = _zero_totals()
    for _, r in rows:
        for k in totals:
            totals[k] += r[k]
    return totals


def write_csv(rows: list[tuple[str, dict]], per_source: dict[str, list[tuple[str, dict]]], out_path: str) -> None:
    fields = [
        "scope", "label", "source", "tier",
        "n", "n_provable", "n_unprovable",
        "b_solved", "b_correct", "b_acc_pct", "b_prov_acc_pct", "b_unprov_acc_pct", "b_time_ms",
        "i_solved", "i_correct", "i_acc_pct", "i_prov_acc_pct", "i_unprov_acc_pct", "i_time_ms",
        "i_better", "b_better", "both_correct", "both_wrong",
        "i_better_prov", "b_better_prov", "i_better_unprov", "b_better_unprov",
    ]

    def row_for(scope: str, label: str, r: dict, source: str = "", tier: str = "") -> dict:
        return {
            "scope": scope,
            "label": label,
            "source": source,
            "tier": tier,
            "n": r["n"],
            "n_provable": r["n_provable"],
            "n_unprovable": r["n_unprovable"],
            "b_solved": r["b_solved"],
            "b_correct": r["b_correct"],
            "b_acc_pct": f"{100 * r['b_correct'] / r['n']:.1f}" if r["n"] else "",
            "b_prov_acc_pct": f"{100 * r['b_prov_correct'] / r['n_provable']:.1f}" if r["n_provable"] else "",
            "b_unprov_acc_pct": f"{100 * r['b_unprov_correct'] / r['n_unprovable']:.1f}" if r["n_unprovable"] else "",
            "b_time_ms": f"{r['b_time'] * 1000:.3f}",
            "i_solved": r["i_solved"],
            "i_correct": r["i_correct"],
            "i_acc_pct": f"{100 * r['i_correct'] / r['n']:.1f}" if r["n"] else "",
            "i_prov_acc_pct": f"{100 * r['i_prov_correct'] / r['n_provable']:.1f}" if r["n_provable"] else "",
            "i_unprov_acc_pct": f"{100 * r['i_unprov_correct'] / r['n_unprovable']:.1f}" if r["n_unprovable"] else "",
            "i_time_ms": f"{r['i_time'] * 1000:.3f}",
            "i_better": r["i_better"],
            "b_better": r["b_better"],
            "both_correct": r["both_correct"],
            "both_wrong": r["both_wrong"],
            "i_better_prov": r["i_better_prov"],
            "b_better_prov": r["b_better_prov"],
            "i_better_unprov": r["i_better_unprov"],
            "b_better_unprov": r["b_better_unprov"],
        }

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()

        for label, r in rows:
            clean = label.strip()
            source, tier = clean.split("/", 1) if "/" in clean else ("", "")
            writer.writerow(row_for("tier", clean, r, source, tier))

        for source, source_rows in per_source.items():
            if not source_rows:
                continue
            writer.writerow(row_for("source_total", source, _sum_rows(source_rows), source=source))

        writer.writerow(row_for("grand_total", "TOTAL", _sum_rows(rows)))


def print_table(rows, title):
    W = 92
    print()
    print(title)
    print("=" * W)
    hdr = (
        f"{'Source/Tier':<26} {'N':>3} {'P/U':>6} | "
        f"{'B:c p% u% ms':>21} | {'I:c p% u% ms':>21}"
    )
    print(hdr)
    print("-" * W)

    grand = _sum_rows(rows)
    for label, r in rows:
        b_prov_acc = _fmt_pct(r['b_prov_correct'], r['n_provable'])
        b_unprov_acc = _fmt_pct(r['b_unprov_correct'], r['n_unprovable'])
        i_prov_acc = _fmt_pct(r['i_prov_correct'], r['n_provable'])
        i_unprov_acc = _fmt_pct(r['i_unprov_correct'], r['n_unprovable'])
        print(
            f"{label:<26} {r['n']:>3} {r['n_provable']:>2}/{r['n_unprovable']:<3} | "
            f"{r['b_correct']:>3} {b_prov_acc:>5} {b_unprov_acc:>5} {_fmt_ms_num(r['b_time']):>6} | "
            f"{r['i_correct']:>3} {i_prov_acc:>5} {i_unprov_acc:>5} {_fmt_ms_num(r['i_time']):>6}"
        )

    print("-" * W)
    print(
        f"{'TOTAL':<26} {grand['n']:>3} {grand['n_provable']:>2}/{grand['n_unprovable']:<3} | "
        f"{grand['b_correct']:>3} {_fmt_pct(grand['b_prov_correct'], grand['n_provable']):>5} {_fmt_pct(grand['b_unprov_correct'], grand['n_unprovable']):>5} {_fmt_ms_num(grand['b_time']):>6} | "
        f"{grand['i_correct']:>3} {_fmt_pct(grand['i_prov_correct'], grand['n_provable']):>5} {_fmt_pct(grand['i_unprov_correct'], grand['n_unprovable']):>5} {_fmt_ms_num(grand['i_time']):>6}"
    )
    print("=" * W)
    print(
        f"Overall accuracy: Baseline {_fmt_pct(grand['b_correct'], grand['n'])} | "
        f"Improved {_fmt_pct(grand['i_correct'], grand['n'])}"
    )
    print(
        f"Overall time    : Baseline {_fmt_ms(grand['b_time'])} | "
        f"Improved {_fmt_ms(grand['i_time'])}"
    )
    print(
        "Legend: c=correct count, p%=provable acc, u%=unprovable acc, ms=runtime"
    )
    print(
        f"Compare (all): Improved better {grand['i_better']} | "
        f"Baseline better {grand['b_better']} | "
        f"Both correct {grand['both_correct']} | Both wrong {grand['both_wrong']}"
    )
    print(
        f"Compare (provable): Improved {grand['i_better_prov']} vs Baseline {grand['b_better_prov']}"
    )
    print(
        f"Compare (unprovable): Improved {grand['i_better_unprov']} vs Baseline {grand['b_better_unprov']}"
    )


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    baseline = Prover(max_depth=15)
    improved = ImprovedProver(max_depth=15)

    all_rows = []
    per_source = {}

    for source in SOURCES:
        per_source[source] = []
        for tier in TIERS:
            path = os.path.join(BENCH_DIR, source, f"{tier}.smt2")
            if not os.path.exists(path):
                continue
            entries = load_benchmark(path)
            if not entries:
                continue
            r = evaluate(entries, baseline, improved, f"{source}/{tier}")
            label = f"  {source}/{tier}"
            all_rows.append((label, r))
            per_source[source].append((label, r))

    print_table(all_rows, "FULL BENCHMARK RESULTS — Baseline vs Improved")
    csv_path = os.path.join(BENCH_DIR, "benchmark_results.csv")
    write_csv(all_rows, per_source, csv_path)
    print(f"CSV written: {csv_path}")

    # ── TPTP evaluation (auto-detected) ──────────────────────────────────────
    tptp_rows = []
    for domain in ["PRP", "SYN"]:
        domain_dir = tptp_problems_dir(os.path.dirname(__file__), domain)
        if domain_dir is None:
            continue
        print(f"\nLoading TPTP/{domain} from {domain_dir} ...")
        tptp_entries = load_tptp_dir(domain_dir, limit=100)
        if not tptp_entries:
            print(f"  [tptp] no usable problems found in {domain_dir}")
            continue
        r = evaluate(tptp_entries, baseline, improved, f"tptp/{domain}")
        label = f"  tptp/{domain}"
        tptp_rows.append((label, r))

    if tptp_rows:
        print_table(tptp_rows, "TPTP BENCHMARK RESULTS — Baseline vs Improved")
        tptp_csv = os.path.join(os.path.dirname(__file__), "tptp_results.csv")
        write_csv(tptp_rows, {}, tptp_csv)
        print(f"CSV written: {tptp_csv}")
    else:
        print("\n[tptp] No TPTP archive found — place TPTP-v*.*.* in the A1 directory to enable.")

    # Per-source subtotals
    print()
    for source, rows in per_source.items():
        if not rows:
            continue
        totals = _sum_rows(rows)
        pct_b = 100 * totals['b_correct'] / totals['n'] if totals['n'] else 0
        pct_i = 100 * totals['i_correct'] / totals['n'] if totals['n'] else 0
        pct_b_prov = 100 * totals['b_prov_correct'] / totals['n_provable'] if totals['n_provable'] else 0
        pct_i_prov = 100 * totals['i_prov_correct'] / totals['n_provable'] if totals['n_provable'] else 0
        pct_b_unprov = 100 * totals['b_unprov_correct'] / totals['n_unprovable'] if totals['n_unprovable'] else 0
        pct_i_unprov = 100 * totals['i_unprov_correct'] / totals['n_unprovable'] if totals['n_unprovable'] else 0
        print(f"[{source}]  {totals['n']} formulas  "
              f"baseline {totals['b_correct']}/{totals['n']} ({pct_b:.0f}%)  "
              f"improved {totals['i_correct']}/{totals['n']} ({pct_i:.0f}%)")
        print(f"          provable:   baseline {totals['b_prov_correct']}/{totals['n_provable']} ({pct_b_prov:.0f}%)"
              f" | improved {totals['i_prov_correct']}/{totals['n_provable']} ({pct_i_prov:.0f}%)")
        print(f"          unprovable: baseline {totals['b_unprov_correct']}/{totals['n_unprovable']} ({pct_b_unprov:.0f}%)"
              f" | improved {totals['i_unprov_correct']}/{totals['n_unprovable']} ({pct_i_unprov:.0f}%)")
        print(f"          compare:    improved better {totals['i_better']} | baseline better {totals['b_better']}"
              f" | both correct {totals['both_correct']} | both wrong {totals['both_wrong']}")
        print(f"                      provable wins: improved {totals['i_better_prov']} vs baseline {totals['b_better_prov']}")
        print(f"                      unprov wins:   improved {totals['i_better_unprov']} vs baseline {totals['b_better_unprov']}")
