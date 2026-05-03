"""
prover.py
---------
Implementation of Algorithm 2 from the textbook:
A naive backward proof search strategy for first-order logic using LK'.

The prover works on a PROOF TREE — a tree of sequents.
Each leaf is either:
  - CLOSED  : proved (branch is done)
  - OPEN    : not yet proved (needs more rules applied)

Algorithm 2 priority order:
  1. id / TopR / BotL     — close the branch immediately
  2. NotR, NotL, ImpliesR, OrR, AndL, ExistsL   — non-branching (1 sub-goal)
  3. AndR, OrL, ImpliesL  — branching (2 sub-goals)
  4. ForAllL / ExistsR    — quantifier with a known term
  5. ForAllR / ExistsL    — quantifier with a fresh constant
  6. stop (can't prove it)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from formula import ForAll, Exists, Formula, Var, Const
from rules import (
    Sequent, fresh_const, reset_fresh,
    is_closed,
    nonbranching_formulas, branching_formulas, quantifier_candidates,
    apply_rule,
    apply_ForAllR, apply_ExistsL,
)


# ---------------------------------------------------------------------------
# Proof tree
# ---------------------------------------------------------------------------

@dataclass
class ProofNode:
    """
    One node in the proof tree.

    sequent     : the sequent at this node
    rule_used   : name of the rule that was applied (None if leaf)
    children    : sub-goal nodes produced by the rule
    closed      : True if this branch is fully proved
    """
    sequent:   Sequent
    rule_used: Optional[str]        = None
    children:  list["ProofNode"]    = field(default_factory=list)
    closed:    bool                 = False

    def is_open(self) -> bool:
        return not self.closed and not self.children

    def __str__(self) -> str:
        return self._fmt(0)

    def _fmt(self, depth: int) -> str:
        indent = "  " * depth
        status = "✓" if self.closed else ("…" if self.children else "✗")
        rule   = f"  [{self.rule_used}]" if self.rule_used else ""
        lines  = [f"{indent}{status} {self.sequent}{rule}"]
        for child in self.children:
            lines.append(child._fmt(depth + 1))
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main prover
# ---------------------------------------------------------------------------

class Prover:
    """
    Naive backward proof search (Algorithm 2).

    Usage:
        p = Prover(max_depth=20)
        result, tree = p.prove(formula)
        print("Proved!" if result else "Could not prove.")
        print(tree)
    """

    def __init__(self, max_depth: int = 30, max_fresh: int = 5):
        """
        max_depth : maximum rule applications on a single branch
        max_fresh : how many fresh constants to try for quantifiers
        """
        self.max_depth = max_depth
        self.max_fresh = max_fresh

    # ---- public entry point -----------------------------------------------

    def prove(self, formula: Formula) -> tuple[bool, ProofNode]:
        """
        Try to prove `formula` (i.e. the sequent  ⊢ formula ).
        Returns (success, proof_tree).
        """
        reset_fresh()
        root = ProofNode(sequent=Sequent((), (formula,)))
        success = self._search(root, depth=0)
        return success, root

    def prove_sequent(self, seq: Sequent) -> tuple[bool, ProofNode]:
        """Prove an arbitrary sequent (useful for testing)."""
        reset_fresh()
        root = ProofNode(sequent=seq)
        success = self._search(root, depth=0)
        return success, root

    # ---- core recursive search --------------------------------------------

    def _search(self, node: ProofNode, depth: int) -> bool:
        """
        Try to close `node` (and all its descendants).
        Returns True if the whole subtree is closed.
        """
        seq = node.sequent

        # ── Step 1: already closed? ────────────────────────────────────────
        if is_closed(seq):
            node.closed    = True
            node.rule_used = "closed"
            return True

        # ── Depth limit ───────────────────────────────────────────────────
        if depth >= self.max_depth:
            return False

        # ── Step 2: non-branching rules ────────────────────────────────────
        for f, rule in nonbranching_formulas(seq):
            sub_goals = apply_rule(seq, rule, f)
            if sub_goals is None:
                continue
            return self._apply_and_recurse(node, rule, sub_goals, depth)

        # ── Step 3: branching rules ────────────────────────────────────────
        for f, rule in branching_formulas(seq):
            sub_goals = apply_rule(seq, rule, f)
            if sub_goals is None:
                continue
            return self._apply_and_recurse(node, rule, sub_goals, depth)

        # ── Step 4 & 5: quantifier rules ──────────────────────────────────
        for f, rule in quantifier_candidates(seq):

            if rule == "ForAllR":
                sub_goals = apply_ForAllR(seq, f)
                if sub_goals:
                    return self._apply_and_recurse(node, rule, sub_goals, depth)

            elif rule == "ForAllL":
                # Try every term already in the sequent first
                terms = list(seq.all_terms()) or [fresh_const()]
                for t in terms:
                    sub_goals = apply_rule(seq, "ForAllL", f, term=t)
                    if sub_goals:
                        result = self._apply_and_recurse(
                            node, f"ForAllL[{t}]", sub_goals, depth)
                        if result:
                            return True
                        # backtrack and try next term
                        node.children  = []
                        node.rule_used = None
                        node.closed    = False
                # Try a fresh constant as last resort
                fresh = fresh_const()
                sub_goals = apply_rule(seq, "ForAllL", f, term=fresh)
                if sub_goals:
                    result = self._apply_and_recurse(
                        node, f"ForAllL[{fresh}]", sub_goals, depth)
                    if result:
                        return True
                    node.children  = []
                    node.rule_used = None
                    node.closed    = False

            elif rule == "ExistsR":
                # Try every term already in the sequent first
                terms = list(seq.all_terms()) or [fresh_const()]
                for t in terms:
                    sub_goals = apply_rule(seq, "ExistsR", f, term=t)
                    if sub_goals:
                        result = self._apply_and_recurse(
                            node, f"ExistsR[{t}]", sub_goals, depth)
                        if result:
                            return True
                        node.children  = []
                        node.rule_used = None
                        node.closed    = False
                # Try fresh
                fresh = fresh_const()
                sub_goals = apply_rule(seq, "ExistsR", f, term=fresh)
                if sub_goals:
                    result = self._apply_and_recurse(
                        node, f"ExistsR[{fresh}]", sub_goals, depth)
                    if result:
                        return True
                    node.children  = []
                    node.rule_used = None
                    node.closed    = False

        # ── Step 6: give up ───────────────────────────────────────────────
        return False

    # ---- helper -----------------------------------------------------------

    def _apply_and_recurse(self, node: ProofNode, rule: str,
                           sub_goals: list[Sequent], depth: int) -> bool:
        """
        Attach sub_goals as children of node, then recursively prove each.
        Returns True only if ALL children are closed.
        """
        node.rule_used = rule
        node.children  = [ProofNode(sequent=sg) for sg in sub_goals]

        all_closed = all(
            self._search(child, depth + 1)
            for child in node.children
        )

        if all_closed:
            node.closed = True
        return all_closed


# ---------------------------------------------------------------------------
# Pretty result printer
# ---------------------------------------------------------------------------

def print_result(formula: Formula, proved: bool, tree: ProofNode):
    print(f"Formula : {formula}")
    print(f"Result  : {'✓ PROVED' if proved else '✗ Could not prove'}")
    print(f"Tree    :\n{tree}")
    print()


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from parser import parse_formula

    prover = Prover()

    tests = [
        # Should prove (tautologies)
        ("(=> (P x) (P x))",                          True),
        ("(or (P x) (not (P x)))",                    True),
        ("(=> (and (P x) (Q x)) (P x))",              True),
        ("(=> (P x) (or (P x) (Q x)))",               True),
        ("(forall ((x S)) (=> (P x) (P x)))",         True),
        ("(=> (forall ((x S)) (P x)) (P a))",         True),

        # Should NOT prove (not tautologies)
        ("(P x)",                                     False),
        ("(and (P x) (Q x))",                         False),
        ("(=> (P x) (Q x))",                          False),
    ]

    print("=" * 60)
    print("PROVER DEMO — Algorithm 2")
    print("=" * 60)
    print()

    passed = 0
    for src, expected in tests:
        f            = parse_formula(src)
        proved, tree = prover.prove(f)
        status       = "✓" if proved == expected else "✗ WRONG"
        print(f"[{status}] {src}")
        passed      += proved == expected

    print()
    print(f"Results: {passed}/{len(tests)} correct")
    print()

    # Show a full proof tree for a clear example
    print("=" * 60)
    print("Full proof tree: (=> (and (P x) (Q x)) (P x))")
    print("=" * 60)
    f = parse_formula("(=> (and (P x) (Q x)) (P x))")
    proved, tree = prover.prove(f)
    print_result(f, proved, tree)