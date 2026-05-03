; Benchmark: propositional
; 18 formulas

; P -> P
provable (=> (P x) (P x))

; excluded middle
provable (or (P x) (not (P x)))

; double negation
provable (=> (not (not (P x))) (P x))

; and-elim left
provable (=> (and (P x) (Q x)) (P x))

; and-elim right
provable (=> (and (P x) (Q x)) (Q x))

; or-intro left
provable (=> (P x) (or (P x) (Q x)))

; or-intro right
provable (=> (Q x) (or (P x) (Q x)))

; contrapositive
provable (=> (=> (P x) (Q x)) (=> (not (Q x)) (not (P x))))

; hypothetical syllogism
provable (=> (=> (P x) (Q x)) (=> (=> (Q x) (R x)) (=> (P x) (R x))))

; modus ponens
provable (=> (and (=> (P x) (Q x)) (P x)) (Q x))

; modus tollens
provable (=> (and (=> (P x) (Q x)) (not (Q x))) (not (P x)))

; implication disjunction
provable (or (=> (P x) (Q x)) (=> (Q x) (P x)))

; de morgan 1
provable (=> (not (or (P x) (Q x))) (and (not (P x)) (not (Q x))))

; de morgan 2
provable (=> (not (and (P x) (Q x))) (or (not (P x)) (not (Q x))))

; bare atom
unprovable (P x)

; conjunction
unprovable (and (P x) (Q x))

; arbitrary implication
unprovable (=> (P x) (Q x))

; or does not imply left
unprovable (=> (or (P x) (Q x)) (P x))

