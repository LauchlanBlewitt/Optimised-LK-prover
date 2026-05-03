; Benchmark: hard
; 8 formulas

; S combinator in FOL
provable (=> (forall ((x S)) (=> (P x) (=> (Q x) (R x)))) (=> (forall ((x S)) (=> (P x) (Q x))) (forall ((x S)) (=> (P x) (R x)))))

; forall distribute over or
provable (=> (forall ((x S)) (or (P x) (Q x))) (or (forall ((x S)) (P x)) (exists ((x S)) (Q x))))

; not-forall to exists-not
provable (=> (not (forall ((x S)) (P x))) (exists ((x S)) (not (P x))))

; not-exists to forall-not
provable (=> (not (exists ((x S)) (P x))) (forall ((x S)) (not (P x))))

; forall contrapositive with exists
provable (=> (forall ((x S)) (=> (P x) (Q x))) (=> (not (exists ((x S)) (Q x))) (not (exists ((x S)) (P x)))))

; forall chain
provable (=> (and (forall ((x S)) (=> (P x) (Q x))) (forall ((x S)) (=> (Q x) (R x)))) (forall ((x S)) (=> (P x) (R x))))

; exists does not imply forall
unprovable (=> (exists ((x S)) (P x)) (forall ((x S)) (P x)))

; quantifier scope reduction
provable (=> (forall ((x S)) (exists ((y S)) (P x))) (exists ((y S)) (forall ((x S)) (P x))))

