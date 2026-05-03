; Benchmark: propositional
; 11 formulas

; Frege axiom 3
provable (=> (=> (P x) (Q x)) (=> (=> (P x) (not (Q x))) (not (P x))))

; Frege K axiom
provable (=> (P x) (=> (Q x) (P x)))

; Frege S axiom
provable (=> (=> (P x) (=> (Q x) (R x))) (=> (=> (P x) (Q x)) (=> (P x) (R x))))

; double negation intro
provable (=> (P x) (not (not (P x))))

; transposition
provable (=> (=> (not (P x)) (not (Q x))) (=> (Q x) (P x)))

; non-contradiction
provable (not (and (P x) (not (P x))))

; disjunctive syllogism
provable (=> (and (or (P x) (Q x)) (not (P x))) (Q x))

; de Morgan and converse
provable (=> (or (not (P x)) (not (Q x))) (not (and (P x) (Q x))))

; de Morgan or converse
provable (=> (and (not (P x)) (not (Q x))) (not (or (P x) (Q x))))

; cannot strengthen
unprovable (=> (P x) (and (P x) (Q x)))

; negation does not imply
unprovable (=> (not (P x)) (Q x))

