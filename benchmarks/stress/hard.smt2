; Benchmark: hard
; 2 formulas

; forall transitivity stress
provable (=> (and (forall ((x S)) (=> (P x) (Q x))) (forall ((x S)) (=> (Q x) (R x)))) (forall ((x S)) (=> (P x) (R x))))

; contrapositive exists stress
provable (=> (forall ((x S)) (=> (P x) (Q x))) (=> (not (exists ((x S)) (Q x))) (not (exists ((x S)) (P x)))))

