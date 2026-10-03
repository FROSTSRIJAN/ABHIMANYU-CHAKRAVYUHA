# Stage 6.1C Cross-Lingual Mutation Intelligence Report

## Status

**PARTIAL**

The implementation demonstrates positive cross-language mutation detection in a
mocked semantic-alignment mode while preserving conservative deterministic
fallback behavior. Real model-backed results were not available in this
environment, so multilingual production capability is not validated.

## Scope and architecture

Stage 6.1C keeps the pipeline explicitly separated:

1. language assessment;
2. semantic relatedness and alignment;
3. structured attribute extraction;
4. mutation comparison;
5. abstention;
6. explanation and graph metadata.

Similarity does not directly produce a mutation label. Cross-language
attributes are compared only after an `ALIGNED` result for the scoped `en-hi`
or `en-es` pair. Missing or unsupported attributes remain unavailable rather
than being interpreted as changes. Unsupported pairs remain explicitly
abstained.

The deterministic mode continues to abstain for cross-language semantic
alignment. The mocked mode injects a controlled semantic result for evaluation;
it is not model accuracy. Real mode is gated by both
`STAGE_6_1C_RUN_REAL_MODEL=true` and `ENABLE_TRANSFORMERS=true`, and remains
disabled by default.

## Dataset and leakage controls

- Dataset: `ml-service/benchmarks/stage_6_1c_dataset.json`
- Version: `6.1c-1.0.0`
- Examples: 14
- Development: 7
- Held-out: 7
- SHA-256: `faa14d3bd1229a14df844e9f425d27e63b8be4dae69d5c2d55c3c93cae815846`
- Group leakage check: passed

The dataset contains English-Hindi and English-Spanish equivalents, certainty,
numeric, date, and negation mutations, unrelated claims, and unsupported
examples. Variants sharing a semantic claim use the same group identifier.
The data is synthetic and should not be treated as a multilingual accuracy
benchmark for deployment.

## Evaluation results

### Deterministic fallback mode

The fallback correctly preserves safe abstention for cross-language semantic
comparisons:

- Alignment F1: 1.0000
- Cross-language equivalent false-mutation rate: 0.0000
- Unrelated false-mutation rate: 0.0000
- Positive mutation detection rate: 0.0000

The zero positive rate is expected: this mode has no cross-language semantic
model and must not infer equivalence from lexical overlap.

### Mocked semantic-model mode

The semantic result was injected by the benchmark harness using the expected
model alignment. These are controlled-path results only:

- Alignment precision/recall/F1: 1.0000 / 1.0000 / 1.0000
- Mutation precision/recall/F1: 1.0000 / 1.0000 / 1.0000
- Exact mutation-label-set match: 1.0000
- Abstention rate: 0.4286
- Equivalent false-mutation rate: 0.0000
- Unrelated false-mutation rate: 0.0000
- Positive mutation detection rate: 1.0000

Per mutation type in mocked mode:

| Mutation type | Examples | Detection rate |
|---|---:|---:|
| `CERTAINTY_ESCALATION` | 2 | 1.0000 |
| `CERTAINTY_REDUCTION` | 1 | 1.0000 |
| `NEGATION_MUTATION` | 2 | 1.0000 |
| `NUMERICAL_MUTATION` | 2 | 1.0000 |
| `TEMPORAL_MUTATION` | 1 | 1.0000 |

Per language pair in mocked mode:

| Pair | Examples | Mutation precision | Positive detection |
|---|---:|---:|---:|
| `en-hi` | 7 | 1.0000 | 1.0000 |
| `en-es` | 6 | 1.0000 | 1.0000 |
| `en-fr` | 1 | unavailable | 0.0000 |

The small sample size means these metrics are diagnostic, not statistically
reliable. The mocked harness does not test embedding model quality.

### Real model-backed mode

Unavailable and not executed. No transformer model was enabled or downloaded
during this milestone. Consequently, no real-model alignment, latency, memory,
or production multilingual accuracy is reported.

## Error analysis

The initial mocked run exposed false certainty escalation for an equivalent
English-Spanish pair because the Spanish future form was not in the scoped
certainty map. The implementation was corrected by adding the narrowly scoped
`lanzara`/`lanzará` and `sera`/`será` forms. The final benchmark reports zero
false mutations for equivalent and unrelated examples.

The benchmark also exposed an unsupported-pair risk when English marker coverage
was too narrow and French text could become `UNKNOWN`. The final dataset uses
unaccented probe text and the detector recognizes it as French, allowing the
pair gate to return explicit `ABSTAIN` rather than treating it as English.
This remains a heuristic language detector, not a general language-identification
model.

## Implementation and modified files

- `ml-service/app/pipelines/language_detector.py`
  - Expanded conservative English, Spanish, and French marker coverage.
- `ml-service/app/pipelines/mutation_detector.py`
  - Added scoped Hindi/Spanish certainty and negation comparison support,
    injected semantic-result support, and aligned cross-language structured
    mutation handling.
- `ml-service/benchmarks/stage_6_1c_dataset.json`
  - Added the grouped positive synthetic benchmark.
- `ml-service/benchmarks/stage_6_1c_runner.py`
  - Added deterministic, mocked, and explicitly gated real evaluation modes,
    leakage checking, dataset hashing, and required metrics.
- `ml-service/tests/test_alignment.py`
  - Added positive mutation, abstention, unsupported-pair, and mocked-model
    regression coverage.
- `docs/STAGE_6_1C_CROSS_LINGUAL_MUTATION_REPORT.md`
  - This report.

No frontend files, Stage 4.2 datasets, verifier safeguards, or public endpoint
names were changed.

## Validation

- Focused Stage 6.1C and related regressions: **59 passed**
- Complete regression suite: **77 passed, 1 skipped**
- API smoke tests: **7/7 endpoints returned HTTP 200**
  (`/health`, `/models`, `/compare`, `/verify`, `/analyze`,
  `/analyze/sequence`, `/analyze/graph`)
- Python compilation: **passed**
- `git diff --check`: **passed**
- Model download during tests: **none**

Exact commands:

```powershell
cd "C:\ABHIMANYU CHAKRAVYUHA\ml-service"
$env:PYTHONPATH=(Get-Location).Path
python -m pytest -q -p no:cacheprovider tests
python benchmarks/stage_6_1c_runner.py
```

The real-model path, when deliberately available, requires:

```powershell
$env:ENABLE_TRANSFORMERS="true"
$env:STAGE_6_1C_RUN_REAL_MODEL="true"
python benchmarks/stage_6_1c_runner.py
```

Those settings were not enabled for this validation.

## Limitations and remaining risks

- The language detector is heuristic and limited to explicitly scoped markers
  and scripts.
- Hindi and Spanish structured extraction remains incomplete outside the tested
  certainty, negation, numeric, and temporal patterns.
- Mocked semantic results do not establish real multilingual embedding quality.
- The benchmark is small, synthetic, and not representative of production
  language variation.
- Real-model memory, latency, alignment quality, and mutation recall remain
  unmeasured.
- No calibrated probabilities or factual truth judgments are introduced.

## Final verdict

**PARTIAL.** Stage 6.1C safety behavior and positive mutation handling are
demonstrated on the synthetic mocked path, with zero equivalent and unrelated
false mutations in the final run. The stage cannot receive PASS because the
real model-backed path was not available and the deterministic fallback
intentionally abstains from positive cross-language mutation detection.
