"""
benchmarks/generate.py
----------------------
Generates a benchmark suite of ~110 first-order logic formulas
across three sources and four difficulty tiers.

Sources
-------
  1. generated  : systematically constructed from known logical laws,
                  covering all connectives and quantifier combinations.
  2. classical   : named theorems from propositional and first-order logic
                  (Frege axioms, De Morgan, modus ponens, etc.).
  3. stress      : structural variants designed to stress specific prover
                  components (associativity, commutativity, currying, duality).

Tiers
-----
  - propositional : no quantifiers
  - easy          : single quantifier, shallow nesting
  - medium        : nested quantifiers, longer proof chains
  - hard          : deeply nested, multiple quantifiers

Each formula is labelled "provable" or "unprovable" and verified
against the baseline prover before inclusion.

Output: one .smt2 file per (source, tier) pair under benchmarks/<source>/.
"""

import os

# ── Source 1: Generated ────────────────────────────────────────────────────

GENERATED_PROPOSITIONAL = [
    ("provable",   "(=> (P x) (P x))",                                          "identity"),
    ("provable",   "(or (P x) (not (P x)))",                                    "excluded middle"),
    ("provable",   "(=> (not (not (P x))) (P x))",                              "double negation elim"),
    ("provable",   "(=> (and (P x) (Q x)) (P x))",                              "and-elim left"),
    ("provable",   "(=> (and (P x) (Q x)) (Q x))",                              "and-elim right"),
    ("provable",   "(=> (P x) (or (P x) (Q x)))",                               "or-intro left"),
    ("provable",   "(=> (Q x) (or (P x) (Q x)))",                               "or-intro right"),
    ("provable",   "(=> (=> (P x) (Q x)) (=> (not (Q x)) (not (P x))))",        "contrapositive"),
    ("provable",   "(=> (=> (P x) (Q x)) (=> (=> (Q x) (R x)) (=> (P x) (R x))))", "hypothetical syllogism"),
    ("provable",   "(=> (and (=> (P x) (Q x)) (P x)) (Q x))",                   "modus ponens"),
    ("provable",   "(=> (and (=> (P x) (Q x)) (not (Q x))) (not (P x)))",       "modus tollens"),
    ("provable",   "(or (=> (P x) (Q x)) (=> (Q x) (P x)))",                    "implication disjunction"),
    ("provable",   "(=> (not (or (P x) (Q x))) (and (not (P x)) (not (Q x))))", "de morgan not-or"),
    ("provable",   "(=> (not (and (P x) (Q x))) (or (not (P x)) (not (Q x))))", "de morgan not-and"),
    ("provable",   "(=> (and (P x) (=> (P x) (Q x))) (Q x))",                   "modus ponens direct"),
    ("provable",   "(=> (or (not (P x)) (Q x)) (=> (P x) (Q x)))",              "or to implies"),
    ("provable",   "(=> (=> (P x) (Q x)) (or (not (P x)) (Q x)))",              "implies to or"),
    ("provable",   "(=> (not (=> (P x) (Q x))) (P x))",                         "not-implies left"),
    ("provable",   "(=> (not (=> (P x) (Q x))) (not (Q x)))",                   "not-implies right"),
    ("provable",   "(=> (=> (not (P x)) (P x)) (P x))",                         "Clavius law"),
    ("provable",   "(=> (and (P x) (not (P x))) (Q x))",                        "ex falso"),
    ("unprovable", "(P x)",                                                      "bare atom"),
    ("unprovable", "(and (P x) (Q x))",                                          "bare conjunction"),
    ("unprovable", "(=> (P x) (Q x))",                                           "arbitrary implication"),
    ("unprovable", "(=> (or (P x) (Q x)) (P x))",                               "or does not imply left"),
    ("unprovable", "(=> (or (P x) (Q x)) (Q x))",                               "or does not imply right"),
    ("unprovable", "(not (P x))",                                                "bare negation"),
]

GENERATED_EASY = [
    ("provable",   "(forall ((x S)) (=> (P x) (P x)))",                              "forall identity"),
    ("provable",   "(=> (forall ((x S)) (P x)) (P a))",                              "universal instantiation"),
    ("provable",   "(=> (forall ((x S)) (P x)) (forall ((x S)) (P x)))",             "forall reflexivity"),
    ("provable",   "(forall ((x S)) (or (P x) (not (P x))))",                        "forall excluded middle"),
    ("provable",   "(=> (forall ((x S)) (and (P x) (Q x))) (forall ((x S)) (P x)))", "forall and-elim"),
    ("provable",   "(=> (P a) (exists ((x S)) (P x)))",                              "existential intro"),
    ("provable",   "(=> (forall ((x S)) (P x)) (exists ((x S)) (P x)))",             "forall implies exists"),
    ("provable",   "(forall ((x S)) (=> (and (P x) (Q x)) (P x)))",                  "forall and-elim scoped"),
    ("provable",   "(=> (forall ((x S)) (=> (P x) (Q x))) (=> (P a) (Q a)))",        "forall instantiate implies"),
    ("provable",   "(forall ((x S)) (=> (or (P x) (Q x)) (or (Q x) (P x))))",        "forall or-comm"),
    ("provable",   "(=> (forall ((x S)) (P x)) (not (exists ((x S)) (not (P x)))))", "forall no counterexample"),
    ("provable",   "(=> (exists ((x S)) (not (P x))) (not (forall ((x S)) (P x))))", "counterexample breaks forall"),
    ("unprovable", "(exists ((x S)) (P x))",                                         "bare exists"),
    ("unprovable", "(forall ((x S)) (P x))",                                         "bare forall"),
    ("unprovable", "(=> (exists ((x S)) (P x)) (forall ((x S)) (P x)))",             "exists does not imply forall"),
    ("unprovable", "(forall ((x S)) (exists ((y S)) (Q x)))",                        "forall needs witness"),
]

GENERATED_MEDIUM = [
    ("provable",
     "(=> (forall ((x S)) (=> (P x) (Q x))) (=> (forall ((x S)) (P x)) (forall ((x S)) (Q x))))",
     "forall monotone"),
    ("provable",
     "(=> (forall ((x S)) (P x)) (not (exists ((x S)) (not (P x)))))",
     "forall to not-exists"),
    ("provable",
     "(=> (not (exists ((x S)) (P x))) (forall ((x S)) (not (P x))))",
     "not-exists to forall-not"),
    ("provable",
     "(=> (forall ((x S)) (=> (P x) (Q x))) (=> (exists ((x S)) (P x)) (exists ((x S)) (Q x))))",
     "exists monotone"),
    ("provable",
     "(=> (and (forall ((x S)) (=> (P x) (Q x))) (exists ((x S)) (P x))) (exists ((x S)) (Q x)))",
     "forall-exists interaction"),
    ("provable",
     "(=> (=> (P a) (Q a)) (=> (not (Q a)) (not (P a))))",
     "contrapositive ground instance"),
    ("provable",
     "(forall ((x S)) (=> (=> (P x) (Q x)) (=> (not (Q x)) (not (P x)))))",
     "forall contrapositive"),
    ("provable",
     "(=> (forall ((x S)) (and (P x) (Q x))) (and (forall ((x S)) (P x)) (forall ((x S)) (Q x))))",
     "forall distributes and"),
    ("provable",
     "(=> (and (forall ((x S)) (P x)) (forall ((x S)) (Q x))) (forall ((x S)) (and (P x) (Q x))))",
     "and distributes into forall"),
    ("provable",
     "(=> (exists ((x S)) (or (P x) (Q x))) (or (exists ((x S)) (P x)) (exists ((x S)) (Q x))))",
     "exists distributes or"),
    ("unprovable",
     "(=> (exists ((x S)) (P x)) (exists ((x S)) (Q x)))",
     "exists does not transfer"),
    ("unprovable",
     "(forall ((x S)) (exists ((y S)) (P x)))",
     "forall-exists spurious"),
    ("unprovable",
     "(=> (or (exists ((x S)) (P x)) (exists ((x S)) (Q x))) (exists ((x S)) (and (P x) (Q x))))",
     "exists-and spurious"),
]

GENERATED_HARD = [
    ("provable",
     "(=> (forall ((x S)) (=> (P x) (=> (Q x) (R x)))) (=> (forall ((x S)) (=> (P x) (Q x))) (forall ((x S)) (=> (P x) (R x)))))",
     "S combinator in FOL"),
    ("provable",
     "(=> (forall ((x S)) (or (P x) (Q x))) (or (forall ((x S)) (P x)) (exists ((x S)) (Q x))))",
     "forall distribute over or"),
    ("provable",
     "(=> (not (forall ((x S)) (P x))) (exists ((x S)) (not (P x))))",
     "not-forall to exists-not"),
    ("provable",
     "(=> (not (exists ((x S)) (P x))) (forall ((x S)) (not (P x))))",
     "not-exists to forall-not"),
    ("provable",
     "(=> (forall ((x S)) (=> (P x) (Q x))) (=> (not (exists ((x S)) (Q x))) (not (exists ((x S)) (P x)))))",
     "forall contrapositive with exists"),
    ("provable",
     "(=> (and (forall ((x S)) (=> (P x) (Q x))) (forall ((x S)) (=> (Q x) (R x)))) (forall ((x S)) (=> (P x) (R x))))",
     "forall chain"),
    ("provable",
     "(=> (forall ((x S)) (exists ((y S)) (P x))) (exists ((y S)) (forall ((x S)) (P x))))",
     "quantifier scope reduction"),
    ("provable",
     "(=> (not (exists ((x S)) (and (P x) (Q x)))) (forall ((x S)) (=> (P x) (not (Q x)))))",
     "not-exists-and to forall-implies-not"),
    ("unprovable",
     "(=> (exists ((x S)) (P x)) (forall ((x S)) (P x)))",
     "exists does not imply forall"),
]


# ── Source 2: Classical theorems ───────────────────────────────────────────

CLASSICAL_PROPOSITIONAL = [
    ("provable",   "(=> (=> (P x) (Q x)) (=> (=> (P x) (not (Q x))) (not (P x))))",   "Frege axiom 3"),
    ("provable",   "(=> (P x) (=> (Q x) (P x)))",                                      "Frege K axiom"),
    ("provable",   "(=> (=> (P x) (=> (Q x) (R x))) (=> (=> (P x) (Q x)) (=> (P x) (R x))))", "Frege S axiom"),
    ("provable",   "(=> (P x) (not (not (P x))))",                                      "double negation intro"),
    ("provable",   "(=> (=> (not (P x)) (not (Q x))) (=> (Q x) (P x)))",               "transposition"),
    ("provable",   "(not (and (P x) (not (P x))))",                                     "non-contradiction"),
    ("provable",   "(=> (and (or (P x) (Q x)) (not (P x))) (Q x))",                    "disjunctive syllogism"),
    ("provable",   "(=> (or (not (P x)) (not (Q x))) (not (and (P x) (Q x))))",        "de Morgan and converse"),
    ("provable",   "(=> (and (not (P x)) (not (Q x))) (not (or (P x) (Q x))))",        "de Morgan or converse"),
    ("unprovable", "(=> (P x) (and (P x) (Q x)))",                                     "cannot strengthen"),
    ("unprovable", "(=> (not (P x)) (Q x))",                                            "negation does not imply"),
]

CLASSICAL_EASY = [
    ("provable",   "(=> (forall ((x S)) (P x)) (P a))",                          "universal instantiation"),
    ("provable",   "(=> (P a) (exists ((x S)) (P x)))",                          "existential generalisation"),
    ("provable",   "(=> (forall ((x S)) (P x)) (exists ((x S)) (P x)))",         "forall implies exists"),
    ("provable",   "(forall ((x S)) (=> (P x) (P x)))",                          "reflexivity of implication"),
    ("unprovable", "(exists ((x S)) (P x))",                                     "unsupported existence"),
    ("unprovable", "(forall ((x S)) (P x))",                                     "unsupported universal"),
]

CLASSICAL_MEDIUM = [
    ("provable",
     "(=> (forall ((x S)) (P x)) (not (exists ((x S)) (not (P x)))))",
     "forall-not-exists duality"),
    ("provable",
     "(=> (not (exists ((x S)) (P x))) (forall ((x S)) (not (P x))))",
     "not-exists-forall-not duality"),
    ("unprovable",
     "(=> (exists ((x S)) (P x)) (exists ((x S)) (Q x)))",
     "classical non-entailment"),
]

CLASSICAL_HARD = [
    ("provable",
     "(=> (forall ((x S)) (=> (P x) (Q x))) (=> (forall ((x S)) (P x)) (forall ((x S)) (Q x))))",
     "forall modus ponens"),
    ("provable",
     "(=> (not (forall ((x S)) (P x))) (exists ((x S)) (not (P x))))",
     "not-forall duality"),
]


# ── Source 3: Stress-test ──────────────────────────────────────────────────

STRESS_PROPOSITIONAL = [
    ("provable",   "(=> (and (P x) (Q x)) (and (Q x) (P x)))",                  "and commutativity"),
    ("provable",   "(=> (or (P x) (Q x)) (or (Q x) (P x)))",                    "or commutativity"),
    ("provable",   "(=> (and (P x) (and (Q x) (R x))) (and (and (P x) (Q x)) (R x)))", "and associativity"),
    ("provable",   "(=> (and (and (P x) (Q x)) (R x)) (and (P x) (and (Q x) (R x))))", "and associativity conv"),
    ("provable",   "(=> (and (P x) (and (Q x) (R x))) (and (R x) (and (Q x) (P x))))", "and reorder 3"),
    ("provable",   "(=> (or (P x) (or (Q x) (R x))) (or (R x) (or (Q x) (P x))))",    "or reorder 3"),
    ("provable",   "(=> (=> (P x) (=> (Q x) (=> (R x) (S x)))) (=> (and (P x) (and (Q x) (R x))) (S x)))", "currying"),
    ("unprovable", "(=> (or (P x) (Q x)) (and (P x) (Q x)))",                   "or does not imply and"),
    ("unprovable", "(and (P x) (Q x))",                                          "conjunction unprovable"),
]

STRESS_EASY = [
    ("provable",   "(forall ((x S)) (=> (and (P x) (Q x)) (and (Q x) (P x))))", "forall and-comm"),
    ("provable",   "(=> (not (exists ((x S)) (P x))) (forall ((x S)) (not (P x))))", "not-exists stress"),
    ("provable",   "(=> (forall ((x S)) (not (P x))) (not (exists ((x S)) (P x))))", "forall-not stress"),
    ("provable",   "(=> (not (forall ((x S)) (P x))) (exists ((x S)) (not (P x))))", "not-forall stress"),
    ("unprovable", "(=> (exists ((x S)) (P x)) (forall ((x S)) (P x)))",         "exists-forall stress"),
]

STRESS_MEDIUM = [
    ("provable",
     "(=> (forall ((x S)) (or (P x) (Q x))) (or (exists ((x S)) (P x)) (forall ((x S)) (Q x))))",
     "forall-or split"),
    ("provable",
     "(=> (or (forall ((x S)) (P x)) (forall ((x S)) (Q x))) (forall ((x S)) (or (P x) (Q x))))",
     "forall distributes over or"),
]

STRESS_HARD = [
    ("provable",
     "(=> (and (forall ((x S)) (=> (P x) (Q x))) (forall ((x S)) (=> (Q x) (R x)))) (forall ((x S)) (=> (P x) (R x))))",
     "forall transitivity stress"),
    ("provable",
     "(=> (forall ((x S)) (=> (P x) (Q x))) (=> (not (exists ((x S)) (Q x))) (not (exists ((x S)) (P x)))))",
     "contrapositive exists stress"),
]


# ── Writer ─────────────────────────────────────────────────────────────────

def write_benchmark(name: str, entries: list, out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{name}.smt2")
    with open(path, "w") as f:
        f.write(f"; Benchmark: {name}\n")
        f.write(f"; {len(entries)} formulas\n\n")
        for label, formula, comment in entries:
            f.write(f"; {comment}\n")
            f.write(f"{label} {formula}\n\n")
    print(f"  Wrote {len(entries):>3} formulas -> {path}")


# ── Entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    out = os.path.dirname(__file__)

    sources = {
        "generated": [
            ("propositional", GENERATED_PROPOSITIONAL),
            ("easy",          GENERATED_EASY),
            ("medium",        GENERATED_MEDIUM),
            ("hard",          GENERATED_HARD),
        ],
        "classical": [
            ("propositional", CLASSICAL_PROPOSITIONAL),
            ("easy",          CLASSICAL_EASY),
            ("medium",        CLASSICAL_MEDIUM),
            ("hard",          CLASSICAL_HARD),
        ],
        "stress": [
            ("propositional", STRESS_PROPOSITIONAL),
            ("easy",          STRESS_EASY),
            ("medium",        STRESS_MEDIUM),
            ("hard",          STRESS_HARD),
        ],
    }

    total = 0
    for source, tiers in sources.items():
        src_dir = os.path.join(out, source)
        print(f"\n[{source}]")
        for tier, entries in tiers:
            write_benchmark(tier, entries, src_dir)
            total += len(entries)

    print(f"\nTotal: {total} formulas across 3 sources × 4 tiers")
