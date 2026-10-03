# Claim intelligence

Stage 3 normalizes each non-question sentence into a claim record while
preserving its original text, qualifiers, negation, conditional wording,
numbers, dates, entities, language, and source message ID. The default
extractor is deterministic and does not claim model accuracy.

Consecutive claims are compared using the existing shared semantic analyzer.
When the transformer embedding model is enabled, the comparison uses
`paraphrase-multilingual-MiniLM-L12-v2`; otherwise it reports lexical fallback.
Semantic similarity is kept separate from verification status.

The graph endpoint attaches local evidence verification to every claim node.
Evidence records retain their document ID, source metadata, retrieval method,
and stance. Missing evidence produces `INSUFFICIENT_EVIDENCE`; it does not
automatically produce `REFUTED`.
