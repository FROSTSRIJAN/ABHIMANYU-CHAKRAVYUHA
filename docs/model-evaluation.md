# Model evaluation

The current test suite is a synthetic regression suite, not a benchmark. It
checks API contracts, deterministic mutation indicators, lexical retrieval,
conflicting evidence handling, and fallback behavior.

No benchmark metrics are reported yet. FEVER and X-CLAIM are available as
research references in `ML FOLDER/`, but they require a separately designed,
reproducible evaluation harness, dataset licensing review, and model/corpus
alignment before results are meaningful.

When evaluation is added, report semantic similarity separately from factual
verification and measure precision, recall, macro-F1, confusion matrix,
Recall@K, MRR, latency, and model memory. Do not combine these into a single
uncalibrated confidence percentage.
