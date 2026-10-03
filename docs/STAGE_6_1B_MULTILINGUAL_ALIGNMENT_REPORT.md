# Stage 6.1B Multilingual Alignment Report

## Verdict

## PARTIAL

The alignment abstraction and safety gates are implemented and verified.
However, the optional multilingual embedding model was not enabled, and the
benchmark is a small synthetic safety benchmark without positive mutation
examples. Real multilingual alignment and mutation performance therefore
remain unvalidated.

## Architecture

Stage 6.1B separates:

1. Language support assessment
2. Semantic relatedness
3. Claim alignment
4. Structured attribute comparison
5. Mutation classification
6. Abstention
7. Explanation and graph serialization

The new [`alignment_engine.py`](<C:/ABHIMANYU CHAKRAVYUHA/ml-service/app/pipelines/alignment_engine.py>)
provides:

- `alignment_status`
- `alignment_method`
- `semantic_similarity`
- `language_pair`
- `confidence_type`
- `limitations`
- `abstention_reason`

Supported alignment states are:

```text
ALIGNED
RELATED_BUT_UNALIGNED
DISTINCT
UNKNOWN
ABSTAIN
```

Similarity is retained as a relatedness signal and is never treated as a
mutation probability or factual confidence.

### Alignment policy

- Same-language English comparisons can remain deterministic.
- Cross-language comparisons require the optional multilingual embedding
  method.
- English/Hindi and English/Spanish are the initial alignment pairs.
- Unsupported language attributes remain unavailable even when semantic
  alignment succeeds.
- Cross-language mutation labels are not emitted unless alignment and
  language-aware structured attributes are both sufficient.
- Existing English `SEMANTIC_DRIFT` behavior is preserved.

## Modified and created files

### Production files

- [`alignment_engine.py`](<C:/ABHIMANYU CHAKRAVYUHA/ml-service/app/pipelines/alignment_engine.py>)
- [`mutation_detector.py`](<C:/ABHIMANYU CHAKRAVYUHA/ml-service/app/pipelines/mutation_detector.py>)
- [`claim_graph.py`](<C:/ABHIMANYU CHAKRAVYUHA/ml-service/app/pipelines/claim_graph.py>)
- [`schemas.py`](<C:/ABHIMANYU CHAKRAVYUHA/ml-service/app/core/schemas.py>)

### Tests

- [`test_alignment.py`](<C:/ABHIMANYU CHAKRAVYUHA/ml-service/tests/test_alignment.py>)

### Benchmark

- [`stage_6_1b_dataset.json`](<C:/ABHIMANYU CHAKRAVYUHA/ml-service/benchmarks/stage_6_1b_dataset.json>)
- [`stage_6_1b_runner.py`](<C:/ABHIMANYU CHAKRAVYUHA/ml-service/benchmarks/stage_6_1b_runner.py>)

### Documentation

- [`STAGE_6_1B_MULTILINGUAL_ALIGNMENT_REPORT.md`](<C:/ABHIMANYU CHAKRAVYUHA/docs/STAGE_6_1B_MULTILINGUAL_ALIGNMENT_REPORT.md>)

No frontend files were modified. Stage 4.2 datasets, labels, and metrics were
not modified.

## Structured mutation behavior

Attributes are compared only after sufficient alignment.

Current safe behavior:

- English attributes remain available through the existing deterministic
  extractor.
- Hindi script claims can be semantically aligned only through the optional
  model path, but Hindi certainty/date/entity/negation attributes remain
  unavailable in this milestone.
- Spanish claims can be semantically aligned through the optional model path
  for the scoped `en-es` pair, but Spanish structured mutation extraction
  remains unavailable.
- Missing attributes produce abstention or no mutation label, not fabricated
  changes.
- Similarity alone never creates a mutation.

Graph edges now preserve, additively:

- Source language
- Target language
- Language pair
- Alignment status
- Alignment method
- Changed attributes
- Abstention reason

## Benchmark design and metrics

Benchmark files:

- [`stage_6_1b_dataset.json`](<C:/ABHIMANYU CHAKRAVYUHA/ml-service/benchmarks/stage_6_1b_dataset.json>)
- [`stage_6_1b_runner.py`](<C:/ABHIMANYU CHAKRAVYUHA/ml-service/benchmarks/stage_6_1b_runner.py>)

The benchmark is explicitly synthetic and contains five grouped examples:

- English paraphrase
- English/Hindi fallback
- English/Spanish fallback
- Unrelated English/Spanish input
- Unsupported English/French input

Counts:

```text
Development: 3
Held-out: 2
Total: 5
```

Leakage check:

```text
passed: true
groups: 5
leaked_groups: []
```

Dataset hash:

```text
418855c1f8a1274104d6af8d7ca8793ae9b7b0b184369ad7bcf52584efb469fa
```

Model-disabled benchmark:

```text
Alignment accuracy: 1.0000
Abstention rate: 0.8000
Exact label-set match: 1.0000
Cross-language false-positive rate: 0.0000
Paraphrase false-positive rate: 0.0000
```

Per-language-pair alignment accuracy:

```text
en-en: 1.0000 (1 example)
en-hi: 1.0000 (1 example)
en-es: 1.0000 (2 examples)
en-fr: 1.0000 (1 example)
```

Mutation metrics are safety-track metrics only because this dataset contains no
positive mutation labels:

```text
Mutation precision: 1.0000
Mutation recall: 0.0000
Mutation F1: 0.0000
```

The runner also executes a mocked model-path harness using an injected
transformer method and fixed similarity. Its alignment accuracy was `0.8000`.
This is not model accuracy: the harness does not run a transformer and the
fixed similarity is intentionally not a calibrated model output.

## Test results

Focused alignment, semantic, API, and Stage 5.1 safety tests passed during
development. Final full regression:

```text
74 passed, 1 skipped in 2.04s
```

The skipped test is the existing opt-in real-model integration test. Models
were intentionally not enabled.

API smoke checks:

```text
7/7 passed
```

Verified:

- `GET /health`
- `GET /models`
- `POST /compare`
- `POST /verify`
- `POST /analyze`
- `POST /analyze/sequence`
- `POST /analyze/graph`

## Model state and loading

No transformer, embedding, or NLI model was enabled or downloaded.

The existing lazy model manager remains unchanged. The model-disabled path uses
lexical fallback and explicitly abstains for cross-language alignment.

Mocked semantic results were injected directly into the alignment abstraction
for tests. No real model inference is claimed.

## Limitations and risks

- The benchmark is small and synthetic.
- It contains no positive cross-language mutation labels.
- Hindi and Spanish structured attribute extraction is not implemented.
- No real English/Hindi or English/Spanish embedding inference was performed in
  this milestone.
- The mocked-model harness is not a substitute for model evaluation.
- Similarity thresholds are conservative heuristics, not calibrated universal
  cross-language thresholds.
- A semantically aligned pair can still abstain from mutation classification
  when attributes are unavailable.
- Language identification remains heuristic.
- Cross-language certainty, dates, negation, currency, and entity alignment
  require a later language-aware extraction milestone.
- No real-world multilingual accuracy or factual verification claim is made.

## Acceptance assessment

Verified:

1. Alignment is separate from similarity.
2. Similarity alone cannot generate mutation labels.
3. Missing language attributes produce uncertainty or abstention.
4. English regression tests pass.
5. Stage 5.1 safety tests pass.
6. API compatibility remains intact.
7. Model loading remains lazy.
8. No automatic model download occurred.
9. Benchmark leakage checks pass.
10. Full tests and diff checks are executed.

The milestone remains **PARTIAL** because actual multilingual model-backed
performance could not be validated and the synthetic benchmark does not measure
positive mutation recall.

Stage 6.1C was not started.
