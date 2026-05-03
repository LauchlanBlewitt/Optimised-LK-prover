; Benchmark: easy
; 6 formulas

; universal instantiation
provable (=> (forall ((x S)) (P x)) (P a))

; existential generalisation
provable (=> (P a) (exists ((x S)) (P x)))

; forall implies exists
provable (=> (forall ((x S)) (P x)) (exists ((x S)) (P x)))

; reflexivity of implication
provable (forall ((x S)) (=> (P x) (P x)))

; unsupported existence
unprovable (exists ((x S)) (P x))

; unsupported universal
unprovable (forall ((x S)) (P x))

