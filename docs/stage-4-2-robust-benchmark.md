# Stage 4.2 robust benchmark

The Stage 4.2 benchmark combines the original 20 Stage 4 examples with 80
additional manually authored synthetic examples in
`ml-service/benchmarks/supplemental_dataset.json`. The original expected labels
were retained unchanged.

Each evaluated record has an ID, original and modified claims, manually
authored expected labels, mutation-presence truth, language, difficulty,
category, explanation, split, and a leakage-group identifier.

The evaluator assigns legacy records to development or held-out partitions
using a stable SHA-256 group rule. Supplemental records retain their explicit
grouped assignments. A group may occur in only one split; the runner fails if
that invariant is violated.

The benchmark reports development, held-out, and overall metrics, as well as
category, difficulty, language, mutation-count, and error slices. Held-out
results are not used to change detector thresholds or production rules.

This remains a curated synthetic evaluation. It is not independent validation
and does not establish real-world or multilingual accuracy.
