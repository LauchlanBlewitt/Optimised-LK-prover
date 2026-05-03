; Benchmark: medium
; 13 formulas

; forall monotone
provable (=> (forall ((x S)) (=> (P x) (Q x))) (=> (forall ((x S)) (P x)) (forall ((x S)) (Q x))))

; forall to not-exists
provable (=> (forall ((x S)) (P x)) (not (exists ((x S)) (not (P x)))))

; not-exists to forall-not
provable (=> (not (exists ((x S)) (P x))) (forall ((x S)) (not (P x))))

; exists monotone
provable (=> (forall ((x S)) (=> (P x) (Q x))) (=> (exists ((x S)) (P x)) (exists ((x S)) (Q x))))

; forall-exists interaction
provable (=> (and (forall ((x S)) (=> (P x) (Q x))) (exists ((x S)) (P x))) (exists ((x S)) (Q x)))

; contrapositive ground instance
provable (=> (=> (P a) (Q a)) (=> (not (Q a)) (not (P a))))

; forall contrapositive
provable (forall ((x S)) (=> (=> (P x) (Q x)) (=> (not (Q x)) (not (P x)))))

; forall distributes and
provable (=> (forall ((x S)) (and (P x) (Q x))) (and (forall ((x S)) (P x)) (forall ((x S)) (Q x))))

; and distributes into forall
provable (=> (and (forall ((x S)) (P x)) (forall ((x S)) (Q x))) (forall ((x S)) (and (P x) (Q x))))

; exists distributes or
provable (=> (exists ((x S)) (or (P x) (Q x))) (or (exists ((x S)) (P x)) (exists ((x S)) (Q x))))

; exists does not transfer
unprovable (=> (exists ((x S)) (P x)) (exists ((x S)) (Q x)))

; forall-exists spurious
unprovable (forall ((x S)) (exists ((y S)) (P x)))

; exists-and spurious
unprovable (=> (or (exists ((x S)) (P x)) (exists ((x S)) (Q x))) (exists ((x S)) (and (P x) (Q x))))

