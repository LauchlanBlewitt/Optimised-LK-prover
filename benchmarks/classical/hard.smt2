; Benchmark: hard
; 2 formulas

; forall modus ponens
provable (=> (forall ((x S)) (=> (P x) (Q x))) (=> (forall ((x S)) (P x)) (forall ((x S)) (Q x))))

; not-forall duality
provable (=> (not (forall ((x S)) (P x))) (exists ((x S)) (not (P x))))

