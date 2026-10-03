# Model card

## Current default

The default service uses a lexical cosine similarity fallback, sentence-level
claim extraction, rule-based mutation indicators, and lexical evidence
retrieval. It runs on CPU without downloading model checkpoints.

## Optional models

- Embeddings: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- NLI: `MoritzLaurer/mDeBERTa-v3-base-mnli-xnli`

Set `ENABLE_TRANSFORMERS=true` or `ENABLE_NLI=true` only after installing the
corresponding packages and reviewing model licenses, resource requirements, and
language coverage. Models load lazily and failures are reported by `/models`.

Similarity is semantic relatedness, not truth probability. NLI scores are model
outputs, not calibrated factual confidence. Persuasion and urgency indicators
are linguistic signals, not evidence of fraud or falsity.
