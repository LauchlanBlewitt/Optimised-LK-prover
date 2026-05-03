; Benchmark: easy
; 5 formulas

; forall and-comm
provable (forall ((x S)) (=> (and (P x) (Q x)) (and (Q x) (P x))))

; not-exists stress
provable (=> (not (exists ((x S)) (P x))) (forall ((x S)) (not (P x))))

; forall-not stress
provable (=> (forall ((x S)) (not (P x))) (not (exists ((x S)) (P x))))

; not-forall stress
provable (=> (not (forall ((x S)) (P x))) (exists ((x S)) (not (P x))))

; exists-forall stress
unprovable (=> (exists ((x S)) (P x)) (forall ((x S)) (P x)))

