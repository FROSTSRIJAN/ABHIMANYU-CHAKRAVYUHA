# Stage 6.2 Multilingual Claim-Pair Model Card

## Intended use

An optional semantic-alignment adapter for English, Hindi, and Spanish claim
pairs. It is not a truth detector, a calibrated mutation probability, or an
evidence verifier.

## Base architecture

`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` is the planned
base encoder. Stage 6.2 fine-tuning uses a supervised pair-similarity
objective, with `ALIGNED` pairs as positive examples and other alignment
labels as negative examples. Mutation labels remain structured comparison
outputs; they are not learned as a direct consequence of similarity.

## Data

The included dataset is synthetic and template-derived. It contains no
human-reviewed examples. Grouped train/validation/test splits prevent
translation or paraphrase groups from crossing splits. See
`stage_6_2_dataset_manifest.json`.

## Limitations

- No weights are shipped by this repository.
- The model is disabled by default and must be explicitly enabled.
- The current dataset is too small and synthetic for generalization claims.
- Hindi and Spanish structured extraction is limited.
- Unsupported languages and low-confidence alignment must abstain.
- Similarity is not a calibrated confidence or factuality score.
