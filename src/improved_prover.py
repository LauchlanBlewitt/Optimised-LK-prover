"""
improved_prover.py
------------------
An improved backward proof search over the naive Algorithm 2 baseline.

Three cumulative improvements:
    1. Loop detection     - track visited sequents to avoid infinite cycles
    2. Iterative deepening - search depth 1, 2, 3... instead of one fixed limit
    3. Smart term ordering - prefer terms that appear in quantified formula
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from formula import ForAll, Exists, Formula, Term, Var, Const
from rules import (
    Sequent, fresh_const, reset_fresh,
    is_closed,
    nonbranching_formulas, branching_formulas, quantifier_candidates,
    apply_rule, apply_ForAllR,
)
from prover import ProofNode


class ImprovedProver:
    """
    Improved backward proof search with three enhancements over the baseline.

    Usage:
        p = ImprovedProver()
        proved, tree = p.prove(formula)
    """

    def __init__(self, max_depth: int = 30):
        self.max_depth = max_depth

    # ── Public entry point ─────────────────────────────────────────────────

    def prove(self, formula: Formula) -> tuple[bool, ProofNode]:
        reset_fresh()
        root = ProofNode(sequent=Sequent((), (formula,)))

        # Improvement 2: iterative deepening — try increasing depth limits
        for depth_limit in range(1, self.max_depth + 1):
            reset_fresh()
            root = ProofNode(sequent=Sequent((), (formula,)))
            if self._search(root, depth=0, limit=depth_limit, visited=set()):
                return True, root

        return False, root

    def prove_sequent(self, seq: Sequent) -> tuple[bool, ProofNode]:
        reset_fresh()
        root = ProofNode(sequent=seq)
        for depth_limit in range(1, self.max_depth + 1):
            reset_fresh()
            root = ProofNode(sequent=seq)
            if self._search(root, depth=0, limit=depth_limit, visited=set()):
                return True, root
        return False, root

    # ── Core search ────────────────────────────────────────────────────────

    def _search(self, node: ProofNode, depth: int,
                limit: int, visited: set[Sequent]) -> bool:
        seq = node.sequent

        # Step 1: close immediately if possible
        if is_closed(seq):
            node.closed    = True
            node.rule_used = "closed"
            return True

        if depth >= limit:
            return False

        # Improvement 1: skip sequents we have already seen on this branch
        if seq in visited:
            return False
        visited = visited | {seq}  # non-destructive — safe for backtracking

        # Step 2: non-branching rules
        for f, rule in nonbranching_formulas(seq):
            sub_goals = apply_rule(seq, rule, f)
            if sub_goals is not None:
                return self._recurse(node, rule, sub_goals, depth, limit, visited)

        # Step 3: branching rules
        for f, rule in branching_formulas(seq):
            sub_goals = apply_rule(seq, rule, f)
            if sub_goals is not None:
                return self._recurse(node, rule, sub_goals, depth, limit, visited)

        # Step 4 & 5: quantifier rules
        for f, rule in quantifier_candidates(seq):

            if rule == "ForAllR":
                sub_goals = apply_ForAllR(seq, f)
                if sub_goals:
                    return self._recurse(node, rule, sub_goals, depth, limit, visited)

            elif rule == "ForAllL":
                for t in self._ranked_terms(seq, f):
                    sub_goals = apply_rule(seq, "ForAllL", f, term=t)
                    if sub_goals:
                        ok = self._recurse(node, f"ForAllL[{t}]",
                                           sub_goals, depth, limit, visited)
                        if ok:
                            return True
                        self._reset_node(node)

            elif rule == "ExistsR":
                for t in self._ranked_terms(seq, f):
                    sub_goals = apply_rule(seq, "ExistsR", f, term=t)
                    if sub_goals:
                        ok = self._recurse(node, f"ExistsR[{t}]",
                                           sub_goals, depth, limit, visited)
                        if ok:
                            return True
                        self._reset_node(node)

        return False

    # ── Improvement 3: smart term ordering ────────────────────────────────

    def _ranked_terms(self, seq: Sequent, quantifier: Formula) -> list[Term]:
        """
        Return terms to try for ForAllL / ExistsR, ranked by relevance.

        Terms that appear inside the quantified body are tried first —
        they are more likely to produce a closed branch. A fresh constant
        is always appended as a fallback.
        """
        body_terms  = quantifier.formula.free_vars()  # vars mentioned in body
        all_terms   = list(seq.all_terms())

        preferred   = [t for t in all_terms if t.name in body_terms]
        fallback    = [t for t in all_terms if t.name not in body_terms]
        fresh       = [fresh_const()]

        return preferred + fallback + fresh

    # ── Helpers ────────────────────────────────────────────────────────────

    def _recurse(self, node: ProofNode, rule: str, sub_goals: list[Sequent],
                 depth: int, limit: int, visited: set[Sequent]) -> bool:
        node.rule_used = rule
        node.children  = [ProofNode(sequent=sg) for sg in sub_goals]
        all_closed = all(
            self._search(child, depth + 1, limit, visited)
            for child in node.children
        )
        if all_closed:
            node.closed = True
        return all_closed

    def _reset_node(self, node: ProofNode) -> None:
        node.children  = []
        node.rule_used = None
        node.closed    = False


# ── Demo ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import time
    from parser import parse_formula
    from prover import Prover

    baseline = Prover()
    improved = ImprovedProver()

    tests = [
        "(=> (P x) (P x))",
        "(or (P x) (not (P x)))",
        "(=> (and (P x) (Q x)) (P x))",
        "(=> (P x) (or (P x) (Q x)))",
        "(forall ((x S)) (=> (P x) (P x)))",
        "(=> (forall ((x S)) (P x)) (P a))",
        # A harder formula: (A→B)→(¬B→¬A)  contrapositive
        "(=> (=> (P x) (Q x)) (=> (not (Q x)) (not (P x))))",
        # Double negation: ¬¬P → P
        "(=> (not (not (P x))) (P x))",
    ]

    print(f"{'Formula':<55} {'Baseline':>10} {'Improved':>10}")
    print("-" * 77)

    for src in tests:
        f = parse_formula(src)

        t0 = time.perf_counter()
        b_proved, _ = baseline.prove(f)
        b_time = time.perf_counter() - t0

        t0 = time.perf_counter()
        i_proved, _ = improved.prove(f)
        i_time = time.perf_counter() - t0

        b_str = f"{'✓' if b_proved else '✗'} {b_time*1000:.2f}ms"
        i_str = f"{'✓' if i_proved else '✗'} {i_time*1000:.2f}ms"
        print(f"{src:<55} {b_str:>10} {i_str:>10}")