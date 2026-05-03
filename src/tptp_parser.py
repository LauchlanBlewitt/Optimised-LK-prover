"""
tptp_parser.py
--------------
Minimal TPTP FOF formula parser. Converts TPTP first-order formula
syntax into the same Formula/Term objects used by our SMT-LIB parser.

Supported connectives:
    ~A          Not
    A & B       And
    A | B       Or
    A => B      Implies
    A <=> B     biconditional (expanded to (A=>B)&(B=>A))
    ! [X] : A   ForAll
    ? [X] : A   Exists
    p(t1,t2)    Atom
    $true       Top
    $false      Bottom

Terms:
    Uppercase names → Var
    Lowercase names → Const  (or Func if followed by '(')
"""

from __future__ import annotations
import re
from formula import (
    Formula, Term,
    Top, Bottom, Atom, Not, And, Or, Implies, ForAll, Exists,
    Var, Const, Func,
)

# ── Tokeniser ────────────────────────────────────────────────────────────────

_TOKEN_RE = re.compile(
    r'<=>|=>|!=|!|[?]'          # multi-char ops first
    r'|[A-Za-z0-9_$]+'          # identifiers / numbers
    r'|[(),:~&|\[\].]'           # single-char punctuation
)


def tokenise_tptp(text: str) -> list[str]:
    """Strip % comments and split into tokens."""
    text = re.sub(r'%[^\n]*', '', text)
    return _TOKEN_RE.findall(text)


# ── Recursive-descent parser ─────────────────────────────────────────────────

class TptpFormulaParser:
    def __init__(self, tokens: list[str]):
        self.tokens = tokens
        self.pos = 0

    # helpers ─────────────────────────────────────────────────────────────────

    def peek(self) -> str | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def consume(self, expected: str | None = None) -> str:
        if self.pos >= len(self.tokens):
            raise SyntaxError(f"Unexpected end of input, expected {expected!r}")
        tok = self.tokens[self.pos]
        if expected is not None and tok != expected:
            raise SyntaxError(f"Expected {expected!r}, got {tok!r} at position {self.pos}")
        self.pos += 1
        return tok

    # formula levels (low → high precedence) ─────────────────────────────────

    def parse_formula(self) -> Formula:
        """Top level: handles => and <=>."""
        lhs = self.parse_or()
        op = self.peek()
        if op == '=>':
            self.consume('=>')
            rhs = self.parse_formula()   # right-associative
            return Implies(lhs, rhs)
        if op == '<=>':
            self.consume('<=>')
            rhs = self.parse_formula()
            return And(Implies(lhs, rhs), Implies(rhs, lhs))
        return lhs

    def parse_or(self) -> Formula:
        lhs = self.parse_and()
        while self.peek() == '|':
            self.consume('|')
            rhs = self.parse_and()
            lhs = Or(lhs, rhs)
        return lhs

    def parse_and(self) -> Formula:
        lhs = self.parse_unary()
        while self.peek() == '&':
            self.consume('&')
            rhs = self.parse_unary()
            lhs = And(lhs, rhs)
        return lhs

    def parse_unary(self) -> Formula:
        tok = self.peek()
        if tok == '~':
            self.consume('~')
            return Not(self.parse_unary())
        if tok == '!':
            return self.parse_forall()
        if tok == '?':
            return self.parse_exists()
        return self.parse_primary()

    def parse_forall(self) -> Formula:
        self.consume('!')
        self.consume('[')
        vars_ = self._parse_var_list()
        self.consume(']')
        self.consume(':')
        body = self.parse_unary()
        for v in reversed(vars_):
            body = ForAll(v, body)
        return body

    def parse_exists(self) -> Formula:
        self.consume('?')
        self.consume('[')
        vars_ = self._parse_var_list()
        self.consume(']')
        self.consume(':')
        body = self.parse_unary()
        for v in reversed(vars_):
            body = Exists(v, body)
        return body

    def _parse_var_list(self) -> list[str]:
        """Parse [X, Y, Z] variable list (brackets already consumed)."""
        # TPTP variable names start uppercase
        v = self.consume()
        vars_ = [v]
        while self.peek() == ',':
            self.consume(',')
            vars_.append(self.consume())
        return vars_

    def parse_primary(self) -> Formula:
        tok = self.peek()
        if tok == '(':
            self.consume('(')
            f = self.parse_formula()
            self.consume(')')
            return f
        name = self.consume()
        if name == '$true':
            return Top()
        if name == '$false':
            return Bottom()
        # predicate atom: p(t1, t2, ...) or bare propositional atom
        if self.peek() == '(':
            self.consume('(')
            args = self._parse_term_list()
            self.consume(')')
            return Atom(name, tuple(args))
        return Atom(name, ())

    # term parsing ────────────────────────────────────────────────────────────

    def _parse_term_list(self) -> list[Term]:
        terms = [self._parse_term()]
        while self.peek() == ',':
            self.consume(',')
            terms.append(self._parse_term())
        return terms

    def _parse_term(self) -> Term:
        name = self.consume()
        if self.peek() == '(':
            self.consume('(')
            args = self._parse_term_list()
            self.consume(')')
            return Func(name, tuple(args))
        # TPTP convention: uppercase = variable, lowercase = constant
        if name[0].isupper():
            return Var(name)
        return Const(name)


# ── Public API ────────────────────────────────────────────────────────────────

def parse_tptp_formula(text: str) -> Formula:
    """Parse a single TPTP FOF formula string into a Formula object."""
    tokens = tokenise_tptp(text)
    if not tokens:
        raise SyntaxError("Empty formula")
    parser = TptpFormulaParser(tokens)
    formula = parser.parse_formula()
    return formula
