; Benchmark: easy
; 11 formulas

; forall P->P
provable (forall ((x S)) (=> (P x) (P x)))

; universal instantiation
provable (=> (forall ((x S)) (P x)) (P a))

; forall identity
provable (=> (forall ((x S)) (P x)) (forall ((x S)) (P x)))

; forall excluded middle
provable (forall ((x S)) (or (P x) (not (P x))))

; forall and-elim
provable (=> (forall ((x S)) (and (P x) (Q x))) (forall ((x S)) (P x)))

; exists intro
provable (=> (P a) (exists ((x S)) (P x)))

; forall implies exists
provable (=> (forall ((x S)) (P x)) (exists ((x S)) (P x)))

; forall and-elim scoped
provable (forall ((x S)) (=> (and (P x) (Q x)) (P x)))

; bare exists
unprovable (exists ((x S)) (P x))

; bare forall
unprovable (forall ((x S)) (P x))

; exists does not imply forall
unprovable (=> (exists ((x S)) (P x)) (forall ((x S)) (P x)))

