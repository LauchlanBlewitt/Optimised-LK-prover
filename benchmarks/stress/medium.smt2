; Benchmark: medium
; 2 formulas

; forall-or split
provable (=> (forall ((x S)) (or (P x) (Q x))) (or (exists ((x S)) (P x)) (forall ((x S)) (Q x))))

; forall distributes over or
provable (=> (or (forall ((x S)) (P x)) (forall ((x S)) (Q x))) (forall ((x S)) (or (P x) (Q x))))

