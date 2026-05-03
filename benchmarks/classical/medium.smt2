; Benchmark: medium
; 3 formulas

; forall-not-exists duality
provable (=> (forall ((x S)) (P x)) (not (exists ((x S)) (not (P x)))))

; not-exists-forall-not duality
provable (=> (not (exists ((x S)) (P x))) (forall ((x S)) (not (P x))))

; classical non-entailment
unprovable (=> (exists ((x S)) (P x)) (exists ((x S)) (Q x)))

