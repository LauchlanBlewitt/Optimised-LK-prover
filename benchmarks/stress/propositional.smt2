; Benchmark: propositional
; 9 formulas

; and commutativity
provable (=> (and (P x) (Q x)) (and (Q x) (P x)))

; or commutativity
provable (=> (or (P x) (Q x)) (or (Q x) (P x)))

; and associativity
provable (=> (and (P x) (and (Q x) (R x))) (and (and (P x) (Q x)) (R x)))

; and associativity conv
provable (=> (and (and (P x) (Q x)) (R x)) (and (P x) (and (Q x) (R x))))

; and reorder 3
provable (=> (and (P x) (and (Q x) (R x))) (and (R x) (and (Q x) (P x))))

; or reorder 3
provable (=> (or (P x) (or (Q x) (R x))) (or (R x) (or (Q x) (P x))))

; currying
provable (=> (=> (P x) (=> (Q x) (=> (R x) (S x)))) (=> (and (P x) (and (Q x) (R x))) (S x)))

; or does not imply and
unprovable (=> (or (P x) (Q x)) (and (P x) (Q x)))

; conjunction unprovable
unprovable (and (P x) (Q x))

