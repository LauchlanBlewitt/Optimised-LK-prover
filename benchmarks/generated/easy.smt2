; Benchmark: easy
; 16 formulas

; forall identity
provable (forall ((x S)) (=> (P x) (P x)))

; universal instantiation
provable (=> (forall ((x S)) (P x)) (P a))

; forall reflexivity
provable (=> (forall ((x S)) (P x)) (forall ((x S)) (P x)))

; forall excluded middle
provable (forall ((x S)) (or (P x) (not (P x))))

; forall and-elim
provable (=> (forall ((x S)) (and (P x) (Q x))) (forall ((x S)) (P x)))

; existential intro
provable (=> (P a) (exists ((x S)) (P x)))

; forall implies exists
provable (=> (forall ((x S)) (P x)) (exists ((x S)) (P x)))

; forall and-elim scoped
provable (forall ((x S)) (=> (and (P x) (Q x)) (P x)))

; forall instantiate implies
provable (=> (forall ((x S)) (=> (P x) (Q x))) (=> (P a) (Q a)))

; forall or-comm
provable (forall ((x S)) (=> (or (P x) (Q x)) (or (Q x) (P x))))

; forall no counterexample
provable (=> (forall ((x S)) (P x)) (not (exists ((x S)) (not (P x)))))

; counterexample breaks forall
provable (=> (exists ((x S)) (not (P x))) (not (forall ((x S)) (P x))))

; bare exists
unprovable (exists ((x S)) (P x))

; bare forall
unprovable (forall ((x S)) (P x))

; exists does not imply forall
unprovable (=> (exists ((x S)) (P x)) (forall ((x S)) (P x)))

; forall needs witness
unprovable (forall ((x S)) (exists ((y S)) (Q x)))

