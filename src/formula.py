"""
formula.py
----------
Data structures for first-order logic formulas.

A formula is a tree. Each node is one of:
  - Atom        e.g. P(x, a)  — a predicate applied to terms
  - Not         ¬A
  - And         A ∧ B
  - Or          A ∨ B
  - Implies     A → B
  - ForAll      ∀x. A
  - Exists      ∃x. A
  - Top         ⊤  (true)
  - Bottom      ⊥  (false)

Terms are also trees:
  - Var         a variable, e.g. x
  - Const       a constant, e.g. a, b
  - Func        a function applied to terms, e.g. f(x, a)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


# ---------------------------------------------------------------------------
# Terms
# ---------------------------------------------------------------------------

class Term:
    """Base class for all terms."""

    def free_vars(self) -> set[str]:
        raise NotImplementedError

    def substitute(self, var: str, replacement: "Term") -> "Term":
        """Return a new term with every free occurrence of `var` replaced by `replacement`."""
        raise NotImplementedError


@dataclass(frozen=True)
class Var(Term):
    """A variable, e.g. x, y, z."""
    name: str

    def free_vars(self) -> set[str]:
        return {self.name}

    def substitute(self, var: str, replacement: Term) -> Term:
        return replacement if self.name == var else self

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class Const(Term):
    """A constant, e.g. a, b, c0."""
    name: str

    def free_vars(self) -> set[str]:
        return set()

    def substitute(self, var: str, replacement: Term) -> Term:
        return self  # constants are never replaced

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class Func(Term):
    """A function application, e.g. f(x, a)."""
    name: str
    args: tuple[Term, ...]

    def free_vars(self) -> set[str]:
        result = set()
        for arg in self.args:
            result |= arg.free_vars()
        return result

    def substitute(self, var: str, replacement: Term) -> Term:
        return Func(self.name, tuple(a.substitute(var, replacement) for a in self.args))

    def __str__(self) -> str:
        args_str = ", ".join(str(a) for a in self.args)
        return f"{self.name}({args_str})"


# 
# Formulas

class Formula:
    """Base class for all formulas."""

    def free_vars(self) -> set[str]:
        raise NotImplementedError

    def substitute(self, var: str, replacement: Term) -> "Formula":
        """Return a copy of this formula with free occurrences of `var` replaced."""
        raise NotImplementedError


@dataclass(frozen=True)
class Top(Formula):
    """⊤ — always true."""

    def free_vars(self) -> set[str]:
        return set()

    def substitute(self, var: str, replacement: Term) -> Formula:
        return self

    def __str__(self) -> str:
        return "⊤"


@dataclass(frozen=True)
class Bottom(Formula):
    """⊥ — always false."""

    def free_vars(self) -> set[str]:
        return set()

    def substitute(self, var: str, replacement: Term) -> Formula:
        return self

    def __str__(self) -> str:
        return "⊥"


@dataclass(frozen=True)
class Atom(Formula):
    """A predicate applied to terms, e.g. P(x, a)."""
    predicate: str
    args: tuple[Term, ...]

    def free_vars(self) -> set[str]:
        result = set()
        for arg in self.args:
            result |= arg.free_vars()
        return result

    def substitute(self, var: str, replacement: Term) -> Formula:
        return Atom(self.predicate, tuple(a.substitute(var, replacement) for a in self.args))

    def __str__(self) -> str:
        if not self.args:
            return self.predicate
        args_str = ", ".join(str(a) for a in self.args)
        return f"{self.predicate}({args_str})"


@dataclass(frozen=True)
class Not(Formula):
    """¬A"""
    formula: Formula

    def free_vars(self) -> set[str]:
        return self.formula.free_vars()

    def substitute(self, var: str, replacement: Term) -> Formula:
        return Not(self.formula.substitute(var, replacement))

    def __str__(self) -> str:
        return f"¬{self.formula}"


@dataclass(frozen=True)
class And(Formula):
    """A ∧ B"""
    left: Formula
    right: Formula

    def free_vars(self) -> set[str]:
        return self.left.free_vars() | self.right.free_vars()

    def substitute(self, var: str, replacement: Term) -> Formula:
        return And(self.left.substitute(var, replacement),
                   self.right.substitute(var, replacement))

    def __str__(self) -> str:
        return f"({self.left} ∧ {self.right})"


@dataclass(frozen=True)
class Or(Formula):
    """A ∨ B"""
    left: Formula
    right: Formula

    def free_vars(self) -> set[str]:
        return self.left.free_vars() | self.right.free_vars()

    def substitute(self, var: str, replacement: Term) -> Formula:
        return Or(self.left.substitute(var, replacement),
                  self.right.substitute(var, replacement))

    def __str__(self) -> str:
        return f"({self.left} ∨ {self.right})"


@dataclass(frozen=True)
class Implies(Formula):
    """A → B"""
    left: Formula
    right: Formula

    def free_vars(self) -> set[str]:
        return self.left.free_vars() | self.right.free_vars()

    def substitute(self, var: str, replacement: Term) -> Formula:
        return Implies(self.left.substitute(var, replacement),
                       self.right.substitute(var, replacement))

    def __str__(self) -> str:
        return f"({self.left} → {self.right})"


@dataclass(frozen=True)
class ForAll(Formula):
    """∀x. A"""
    var: str
    formula: Formula

    def free_vars(self) -> set[str]:
        return self.formula.free_vars() - {self.var}

    def substitute(self, var: str, replacement: Term) -> Formula:
        if var == self.var:
            return self  # bound variable, don't substitute inside
        return ForAll(self.var, self.formula.substitute(var, replacement))

    def __str__(self) -> str:
        return f"∀{self.var}.{self.formula}"


@dataclass(frozen=True)
class Exists(Formula):
    """∃x. A"""
    var: str
    formula: Formula

    def free_vars(self) -> set[str]:
        return self.formula.free_vars() - {self.var}

    def substitute(self, var: str, replacement: Term) -> Formula:
        if var == self.var:
            return self  # bound variable, don't substitute inside
        return Exists(self.var, self.formula.substitute(var, replacement))

    def __str__(self) -> str:
        return f"∃{self.var}.{self.formula}"
