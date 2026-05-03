"""
rules.py
--------
Backward application of sequent inference rules.

Sequent form: Γ ⊢ Δ
    - Γ (left): formulas treated as assumptions
    - Δ (right): formulas where at least one must be derivable

Sequent representation:
    Sequent(left: tuple[Formula,...], right: tuple[Formula,...])

Backward rule application:
    from one goal sequent, generate sub-goal sequents
    whose proofs imply a proof of the original goal.

Rule function shape:
    apply_XY(seq: Sequent, formula: Formula, side: str)
        -> list[Sequent] | None

    None      -> rule does not apply
    []        -> branch closes immediately (axiom/closure)
    [s1]      -> one-premise rule
    [s1, s2]  -> two-premise rule (branching)

Rule names used here:
    Closure: id, TopR, BotL
    Right: NotR, AndR, OrR, ImpliesR, ForAllR, ExistsR
    Left:  NotL, AndL, OrL, ImpliesL, ForAllL, ExistsL
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from formula import (
    Formula, Term,
    Top, Bottom, Atom, Not, And, Or, Implies, ForAll, Exists,
    Var, Const, Func,
)

# ---------------------------------------------------------------------------
# Sequent
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Sequent:
    """
    Γ ⊢ Δ
    left  = Γ (assumptions)
    right = Δ (goals)
    """
    left:  tuple[Formula, ...]
    right: tuple[Formula, ...]

    def __str__(self) -> str:
        lhs = ", ".join(str(f) for f in self.left)  or "·"
        rhs = ", ".join(str(f) for f in self.right) or "·"
        return f"{lhs} ⊢ {rhs}"

    # Small builder helpers

    def add_left(self, *fs: Formula) -> "Sequent":
        """Return a new sequent with extra formulas on the left."""
        return Sequent(self.left + fs, self.right)

    def add_right(self, *fs: Formula) -> "Sequent":
        """Return a new sequent with extra formulas on the right."""
        return Sequent(self.left, self.right + fs)

    def remove_left(self, f: Formula) -> "Sequent":
        lst = list(self.left)
        lst.remove(f)
        return Sequent(tuple(lst), self.right)

    def remove_right(self, f: Formula) -> "Sequent":
        lst = list(self.right)
        lst.remove(f)
        return Sequent(self.left, tuple(lst))

    def replace_left(self, old: Formula, *new: Formula) -> "Sequent":
        lst = list(self.left)
        idx = lst.index(old)
        lst[idx:idx+1] = list(new)
        return Sequent(tuple(lst), self.right)

    def replace_right(self, old: Formula, *new: Formula) -> "Sequent":
        lst = list(self.right)
        idx = lst.index(old)
        lst[idx:idx+1] = list(new)
        return Sequent(self.left, tuple(lst))

    def all_terms(self) -> set[Term]:
        """Collect all terms (Var/Const) appearing anywhere in the sequent."""
        result: set[Term] = set()
        for f in self.left + self.right:
            result |= _terms_in_formula(f)
        return result

    def all_term_names(self) -> set[str]:
        return {t.name for t in self.all_terms()}


def _terms_in_formula(f: Formula) -> set[Term]:
    """Collect all Var/Const leaves in a formula recursively."""
    if isinstance(f, (Top, Bottom)):
        return set()
    if isinstance(f, Atom):
        result: set[Term] = set()
        for t in f.args:
            result |= _terms_in_term(t)
        return result
    if isinstance(f, Not):
        return _terms_in_formula(f.formula)
    if isinstance(f, (And, Or, Implies)):
        return _terms_in_formula(f.left) | _terms_in_formula(f.right)
    if isinstance(f, (ForAll, Exists)):
        return _terms_in_formula(f.formula)
    return set()


def _terms_in_term(t: Term) -> set[Term]:
    if isinstance(t, (Var, Const)):
        return {t}
    if isinstance(t, Func):  # type: ignore[attr-defined]
        result: set[Term] = set()
        for a in t.args:
            result |= _terms_in_term(a)
        return result
    return set()


# ---------------------------------------------------------------------------
# Fresh name generator
# ---------------------------------------------------------------------------

_fresh_counter = 0

def fresh_const() -> Const:
    """Generate a fresh constant name."""
    global _fresh_counter
    _fresh_counter += 1
    return Const(f"_c{_fresh_counter}")

def reset_fresh():
    """Reset the fresh-constant counter."""
    global _fresh_counter
    _fresh_counter = 0


# ---------------------------------------------------------------------------
# Helper: is_closed
# ---------------------------------------------------------------------------

def is_closed(seq: Sequent) -> bool:
    """
        Immediate closure checks:
            - same formula appears on both sides (id)
            - ⊤ appears on the right (TopR)
            - ⊥ appears on the left (BotL)
    """
    right_set = set(seq.right)
    for f in seq.left:
        if f in right_set:
            return True
    if any(isinstance(f, Top) for f in seq.right):
        return True
    if any(isinstance(f, Bottom) for f in seq.left):
        return True
    return False


# Backward rule functions
# Return list[Sequent] for sub-goals, or None when not applicable.

# NotR
# Goal:   Γ ⊢ ¬A, Δ
# Parent: Γ, A ⊢ Δ
def apply_NotR(seq: Sequent, f: Formula) -> Optional[list[Sequent]]:
    if not isinstance(f, Not) or f not in seq.right:
        return None
    new_seq = seq.replace_right(f).add_left(f.formula)
    return [new_seq]


# NotL
# Goal:   Γ, ¬A ⊢ Δ
# Parent: Γ ⊢ A, Δ
def apply_NotL(seq: Sequent, f: Formula) -> Optional[list[Sequent]]:
    if not isinstance(f, Not) or f not in seq.left:
        return None
    new_seq = seq.replace_left(f).add_right(f.formula)
    return [new_seq]


# AndR
# Goal:   Γ ⊢ A ∧ B, Δ
# Parents: Γ ⊢ A, Δ   AND   Γ ⊢ B, Δ
def apply_AndR(seq: Sequent, f: Formula) -> Optional[list[Sequent]]:
    if not isinstance(f, And) or f not in seq.right:
        return None
    base = seq.replace_right(f)
    return [base.add_right(f.left), base.add_right(f.right)]


# AndL
# Goal:   Γ, A ∧ B ⊢ Δ
# Parent: Γ, A, B ⊢ Δ
def apply_AndL(seq: Sequent, f: Formula) -> Optional[list[Sequent]]:
    if not isinstance(f, And) or f not in seq.left:
        return None
    new_seq = seq.replace_left(f, f.left, f.right)
    return [new_seq]


# OrR
# Goal:   Γ ⊢ A ∨ B, Δ
# Parent: Γ ⊢ A, B, Δ
def apply_OrR(seq: Sequent, f: Formula) -> Optional[list[Sequent]]:
    if not isinstance(f, Or) or f not in seq.right:
        return None
    new_seq = seq.replace_right(f, f.left, f.right)
    return [new_seq]


# OrL
# Goal:   Γ, A ∨ B ⊢ Δ
# Parents: Γ, A ⊢ Δ   AND   Γ, B ⊢ Δ
def apply_OrL(seq: Sequent, f: Formula) -> Optional[list[Sequent]]:
    if not isinstance(f, Or) or f not in seq.left:
        return None
    base = seq.replace_left(f)
    return [base.add_left(f.left), base.add_left(f.right)]


# ImpliesR
# Goal:   Γ ⊢ A → B, Δ
# Parent: Γ, A ⊢ B, Δ
def apply_ImpliesR(seq: Sequent, f: Formula) -> Optional[list[Sequent]]:
    if not isinstance(f, Implies) or f not in seq.right:
        return None
    new_seq = seq.replace_right(f, f.right).add_left(f.left)
    return [new_seq]


# ImpliesL
# Goal:   Γ, A → B ⊢ Δ
# Parents: Γ ⊢ A, Δ   AND   Γ, B ⊢ Δ
def apply_ImpliesL(seq: Sequent, f: Formula) -> Optional[list[Sequent]]:
    if not isinstance(f, Implies) or f not in seq.left:
        return None
    base = seq.replace_left(f)
    return [base.add_right(f.left), base.add_left(f.right)]


# ForAllR
# Goal:   Γ ⊢ ∀x.A, Δ
# Parent: Γ ⊢ A[x/c], Δ    where c is a FRESH constant
def apply_ForAllR(seq: Sequent, f: Formula) -> Optional[list[Sequent]]:
    if not isinstance(f, ForAll) or f not in seq.right:
        return None
    c = fresh_const()
    instantiated = f.formula.substitute(f.var, c)
    new_seq = seq.replace_right(f, instantiated)
    return [new_seq]


# ForAllL
# Goal:   Γ, ∀x.A ⊢ Δ
# Parent: Γ, ∀x.A, A[x/t] ⊢ Δ   for some term t already in the sequent
# Original formula stays, so it can be instantiated again.
def apply_ForAllL(seq: Sequent, f: Formula, t: Term) -> Optional[list[Sequent]]:
    if not isinstance(f, ForAll) or f not in seq.left:
        return None
    instantiated = f.formula.substitute(f.var, t)
    # Avoid trivial loops from repeated identical instantiations.
    if instantiated in seq.left:
        return None
    new_seq = seq.add_left(instantiated)
    return [new_seq]


# ExistsR
# Goal:   Γ ⊢ ∃x.A, Δ
# Parent: Γ ⊢ ∃x.A, A[x/t], Δ   for some term t already in the sequent
# Original formula stays, so it can be instantiated again.
def apply_ExistsR(seq: Sequent, f: Formula, t: Term) -> Optional[list[Sequent]]:
    if not isinstance(f, Exists) or f not in seq.right:
        return None
    instantiated = f.formula.substitute(f.var, t)
    if instantiated in seq.right:
        return None
    new_seq = seq.add_right(instantiated)
    return [new_seq]


# ExistsL
# Goal:   Γ, ∃x.A ⊢ Δ
# Parent: Γ, A[x/c] ⊢ Δ    where c is a FRESH constant
def apply_ExistsL(seq: Sequent, f: Formula) -> Optional[list[Sequent]]:
    if not isinstance(f, Exists) or f not in seq.left:
        return None
    c = fresh_const()
    instantiated = f.formula.substitute(f.var, c)
    new_seq = seq.replace_left(f, instantiated)
    return [new_seq]


# ---------------------------------------------------------------------------
# Rule classifier helpers (used by Algorithm 2)
# ---------------------------------------------------------------------------

def closing_rules(seq: Sequent) -> bool:
    """True when the sequent closes immediately (id / TopR / BotL)."""
    return is_closed(seq)


def nonbranching_formulas(seq: Sequent) -> list[tuple[Formula, str]]:
    """
        Return (formula, rule) pairs where a non-branching rule applies:
      ¬L, ¬R, →R, ∧L, ∨R, ∃L
        Each produces exactly one sub-goal.
    """
    result = []
    for f in seq.right:
        if isinstance(f, Not):       result.append((f, "NotR"))
        if isinstance(f, Implies):   result.append((f, "ImpliesR"))
        if isinstance(f, Or):        result.append((f, "OrR"))
    for f in seq.left:
        if isinstance(f, Not):       result.append((f, "NotL"))
        if isinstance(f, And):       result.append((f, "AndL"))
        if isinstance(f, Exists):    result.append((f, "ExistsL"))
    return result


def branching_formulas(seq: Sequent) -> list[tuple[Formula, str]]:
    """
        Return (formula, rule) pairs where a branching rule applies:
      ∧R, ∨L, →L
        These produce two sub-goals.
    """
    result = []
    for f in seq.right:
        if isinstance(f, And):       result.append((f, "AndR"))
    for f in seq.left:
        if isinstance(f, Or):        result.append((f, "OrL"))
        if isinstance(f, Implies):   result.append((f, "ImpliesL"))
    return result


def quantifier_candidates(seq: Sequent) -> list[tuple[Formula, str]]:
    """
        Return (formula, rule) pairs for quantifier rules:
            ∀L, ∃R need an instantiation term
            ∀R, ∃L use a fresh constant
    """
    result = []
    for f in seq.right:
        if isinstance(f, ForAll):    result.append((f, "ForAllR"))
        if isinstance(f, Exists):    result.append((f, "ExistsR"))
    for f in seq.left:
        if isinstance(f, ForAll):    result.append((f, "ForAllL"))
    return result


# ---------------------------------------------------------------------------
# Apply a named rule to a sequent (dispatcher)
# ---------------------------------------------------------------------------

def apply_rule(seq: Sequent, rule: str, f: Formula,
               term: Optional[Term] = None) -> Optional[list[Sequent]]:
    """
    Dispatch to the requested rule function.
    `term` is required for ForAllL and ExistsR.
    """
    if rule == "NotR":      return apply_NotR(seq, f)
    if rule == "NotL":      return apply_NotL(seq, f)
    if rule == "AndR":      return apply_AndR(seq, f)
    if rule == "AndL":      return apply_AndL(seq, f)
    if rule == "OrR":       return apply_OrR(seq, f)
    if rule == "OrL":       return apply_OrL(seq, f)
    if rule == "ImpliesR":  return apply_ImpliesR(seq, f)
    if rule == "ImpliesL":  return apply_ImpliesL(seq, f)
    if rule == "ForAllR":   return apply_ForAllR(seq, f)
    if rule == "ForAllL":   return apply_ForAllL(seq, f, term)
    if rule == "ExistsR":   return apply_ExistsR(seq, f, term)
    if rule == "ExistsL":   return apply_ExistsL(seq, f)
    raise ValueError(f"Unknown rule: {rule}")


# ---------------------------------------------------------------------------
# Quick demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from parser import parse_formula

    def demo(src: str):
        f = parse_formula(src)
        seq = Sequent((), (f,))
        print(f"Formula : {f}")
        print(f"Sequent : {seq}")
        print(f"Closed? : {is_closed(seq)}")
        print(f"Non-branching: {nonbranching_formulas(seq)}")
        print(f"Branching    : {branching_formulas(seq)}")
        print(f"Quantifiers  : {quantifier_candidates(seq)}")
        print()

    reset_fresh()
    demo("(or (P x) (not (P x)))")           # P(x) ∨ ¬P(x)
    demo("(=> (P x) (P x))")                  # P(x) → P(x)
    demo("(forall ((x S)) (=> (P x) (P x)))") # ∀x.(P(x) → P(x))
    demo("(and (P x) (Q y))")                 # P(x) ∧ Q(y)

    # Manually step through:  ⊢ P(x) → P(x)
    print("=== Step-through: ⊢ P(x) → P(x) ===")
    f = parse_formula("(=> (P x) (P x))")
    s0 = Sequent((), (f,))
    print(f"Goal    : {s0}")
    s1 = apply_ImpliesR(s0, f)[0]
    print(f"ImpliesR: {s1}")
    print(f"Closed? : {is_closed(s1)}")
