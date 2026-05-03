"""
parser.py
---------
Parsing small chunk of SMT-LIB 2 syntax and turn it into Formula/Term
objects so  can reason over a clean syntax tree later.

 support:
    (and  A B)
    (or   A B)
    (not  A)
    (=>   A B)
    (forall ((x S)) A)
    (exists ((x S)) A)
    true / false
    (P t1 t2 ...)           -- predicate atom
    (f t1 t2 ...)           -- function term
    x                       -- bare name (variable / constant style token)


In quantifiers, reading things like the "S" in (x S) so parsing stays valid,
but  ignore sorts semantically.  treat everything as single-sorted/untyped.

"""

from __future__ import annotations
from typing import Union
from formula import (
    Formula, Term,
    Top, Bottom, Atom, Not, And, Or, Implies, ForAll, Exists,
    Var, Const, Func,
)

# Tokeniser

def tokenise(text: str) -> list[str]:
    """
     break raw SMT-LIB text into simple tokens.
    1) remove ';' line comments
    2) pad parentheses so '(' and ')' become standalone tokens
    """
    #  drop anything after ';' on each line (SMT-LIB comment style).
    lines = []
    for line in text.splitlines():
        idx = line.find(";")
        if idx >= 0:
            line = line[:idx]
        lines.append(line)
    text = " ".join(lines)

    # make parentheses their own tokens, then split by whitespace.
    text = text.replace("(", " ( ").replace(")", " ) ")
    return text.split()


# Recursive-descent parser

class Parser:
    def __init__(self, tokens: list[str]):
        self.tokens = tokens
        self.pos = 0


    def peek(self) -> str | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def consume(self) -> str:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def expect(self, value: str) -> None:
        tok = self.consume()
        if tok != value:
            raise SyntaxError(f"Expected '{value}', got '{tok}' at position {self.pos}")

    #  entry point for formulas 

    def parse_formula(self) -> Formula:
        tok = self.peek()
        if tok is None:
            raise SyntaxError("Unexpected end of input")

        if tok == "(":
            return self._parse_compound_formula()
        elif tok == "true":
            self.consume()
            return Top()
        elif tok == "false":
            self.consume()
            return Bottom()
        else:
            # If  only see a bare symbol,  treat it as a propositional atom.
            name = self.consume()
            return Atom(name, ())

    # formulas that start with '(' 

    def _parse_compound_formula(self) -> Formula:
        self.expect("(")
        head = self.consume()

        if head == "and":
            left = self.parse_formula()
            right = self.parse_formula()
            self.expect(")")
            return And(left, right)

        elif head == "or":
            left = self.parse_formula()
            right = self.parse_formula()
            self.expect(")")
            return Or(left, right)

        elif head == "not":
            sub = self.parse_formula()
            self.expect(")")
            return Not(sub)

        elif head == "=>":
            left = self.parse_formula()
            right = self.parse_formula()
            self.expect(")")
            return Implies(left, right)

        elif head == "forall":
            var, _ = self._parse_single_binding()
            body = self.parse_formula()
            self.expect(")")
            return ForAll(var, body)

        elif head == "exists":
            var, _ = self._parse_single_binding()
            body = self.parse_formula()
            self.expect(")")
            return Exists(var, body)

        else:
            # Anything else in formula position becomes a predicate
            # application: (Head arg1 arg2 ...)
            args = []
            while self.peek() != ")":
                args.append(self._parse_term())
            self.expect(")")
            return Atom(head, tuple(args))

    # quantifier binding list ((x S)) 

    def _parse_single_binding(self) -> tuple[str, str]:
        """
         parse one quantifier binding of the form ((var sort)).

        Returns:
            (var, sort)

         parse the sort for syntax, but  ignore it while reasoning.
        """
        self.expect("(")          # start outer binding list
        self.expect("(")          # start actual (var sort) pair
        var = self.consume()
        sort = self.consume()
        self.expect(")")          # end (var sort)
        self.expect(")")          # end outer binding list
        return var, sort

    #  terms 

    def _parse_term(self) -> Term:
        tok = self.peek()
        if tok is None:
            raise SyntaxError("Expected term but reached end of input")

        if tok == "(":
            return self._parse_compound_term()
        else:
            name = self.consume()
            return Var(name)   # in term position,  treat bare symbols as vars

    def _parse_compound_term(self) -> Term:
        """parse a function-style term: (f t1 t2 ...)."""
        self.expect("(")
        name = self.consume()
        args = []
        while self.peek() != ")":
            args.append(self._parse_term())
        self.expect(")")
        return Func(name, tuple(args))



# Public API

def parse_formula(text: str) -> Formula:
    """parse one SMT-LIB formula string into a Formula object."""
    tokens = tokenise(text)
    parser = Parser(tokens)
    formula = parser.parse_formula()
    if parser.pos != len(parser.tokens):
        remaining = parser.tokens[parser.pos:]
        raise SyntaxError(f"Unexpected trailing tokens: {remaining}")
    return formula


def parse_file(path: str) -> list[Formula]:
    """
     parse formulas from a text file, one useful formula per line.

    While reading:
    - skip blank lines
    - skip full-line comments starting with ';'
    - unwrap lines like (assert ...)

    If a line is malformed,  print a warning and keep going.
    """
    formulas = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(";"):
                continue
            # Many benchmark files wrap each formula in (assert ...).
            if line.startswith("(assert ") and line.endswith(")"):
                line = line[len("(assert "):-1].strip()
            try:
                formulas.append(parse_formula(line))
            except SyntaxError as e:
                print(f"[parser] Skipping malformed line: {e}\n  >> {line}")
    return formulas


#
#  demo

if __name__ == "__main__":
    examples = [
        "true",
        "false",
        "(not (P x))",
        "(and (P x) (Q y))",
        "(or (P x) (not (P x)))",
        "(=> (P x) (Q x))",
        "(forall ((x S)) (=> (P x) (Q x)))",
        "(exists ((x S)) (and (P x) (Q x)))",
        "(P (f x) a)",                          # P(f(x), a)
        "(=> (forall ((x U)) (P x)) (P a))",    # (∀x.P(x)) → P(a)
    ]

    print("=== Parser Demo ===\n")
    for src in examples:
        try:
            f = parse_formula(src)
            fvars = f.free_vars()
            print(f"Input : {src}")
            print(f"Parsed: {f}")
            print(f"FVars : {fvars}")
            print()
        except SyntaxError as e:
            print(f"ERROR on '{src}': {e}\n")
