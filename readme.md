# LK-Prover: Automated Theorem Prover for FOL

An implementation of the LK' sequent calculus in Python, featuring a naive baseline and an optimized prover with Loop Detection, Iterative Deepening, and Smart Term Ordering.

## Performance Summary
Tested against 205 formulas, including a stress test using the **TPTP v4.0.0 (SYN Domain)** library.

| Metric | Baseline | Improved |
| :--- | :--- | :--- |
| **TPTP Provable Accuracy** | 51.7% | **53.9%** |
| **Total Accuracy** | 55.0% | 55.0% |

### Key Insight
While optimizations introduce overhead on simple tasks, they are structurally necessary for industrial-grade logic. The Improved prover successfully resolved complex infinite branches in TPTP that the Baseline could not navigate.