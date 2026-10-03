# Stage 6.1A Safety and Abstention Report

## 1. Summary

Stage 6.1A adds a conservative multilingual safety foundation without enabling
transformer, embedding, or NLI models. The implementation:

- Adds structured language assessment metadata.
- Distinguishes `SUPPORTED`, `LIMITED`, `UNKNOWN`, and `UNSUPPORTED`.
- Keeps deterministic English mutation rules restricted to supported English
  comparisons.
- Preserves script detection for Hindi, Bengali, Punjabi, Tamil, and Telugu as
  limited support rather than full language understanding.
- Identifies common Spanish and French inputs as unsupported instead of
  silently treating them as English.
- Prevents the Spanish article `El` from becoming a named entity.
- Marks cross-language lexical fallback comparisons as `ABSTAIN`.
- Preserves existing mutation labels and API response fields.
- Propagates optional comparison and abstention metadata to mutation results and
  graph edges.

No multilingual semantic accuracy claim is made. No dedicated multilingual
benchmark was added in this milestone.

## 2. Files modified

- `ml-service/app/pipelines/language_detector.py`
- `ml-service/app/pipelines/claim_normalizer.py`
- `ml-service/app/pipelines/semantic_analyzer.py`
- `ml-service/app/pipelines/mutation_detector.py`
- `ml-service/app/services/analysis_service.py`
- `ml-service/app/core/schemas.py`
- `ml-service/app/pipelines/claim_graph.py`
- `ml-service/tests/test_claim_intelligence.py`
- `ml-service/tests/test_semantic.py`
- `docs/STAGE_6_1A_SAFETY_REPORT.md`

No frontend files were modified. Stage 4.2 datasets and labels were not
modified.

## 3. Language behavior

### Before

- Unicode scripts were detected for several Indian languages.
- All other text defaulted to `en`.
- English certainty, negation, temporal, and capitalization rules could be
  applied to unsupported Latin-script languages.
- Spanish `El` could be extracted as a capitalized entity.

### After

- English is `SUPPORTED` only when conservative English markers are present.
- Hindi, Bengali, Punjabi, Tamil, and Telugu script detection returns
  `LIMITED` with `confidence_type: "script_based"`.
- Spanish and French marker-based inputs return `UNSUPPORTED`.
- Unrecognized Latin, empty, numeric-only, and ambiguous inputs return an
  explicit non-supported status.
- Mixed-script input returns `UNKNOWN`.
- Language metadata includes:
  - `language_code`
  - `language_name`
  - `detector_method`
  - `support_status`
  - `confidence_type`
  - `limitations`

These are heuristic statuses, not calibrated language probabilities.

## 4. Abstention behavior

English-only deterministic mutation rules are disabled if either claim is not
supported English or if the pair is not safely aligned.

Cross-language comparisons without the optional embedding model return:

```text
comparison_status: ABSTAIN
semantic_relationship: ABSTAIN
method: lexical_fallback
```

The lexical score is retained for compatibility and diagnostics, but it is not
treated as cross-language equivalence, truth probability, or mutation
confidence.

Mutation results preserve raw claims and return no definitive mutation labels
when the comparison is unsafe. They include an abstention reason and
limitations. Graph edges preserve this metadata additively.

## 5. False-mutation regression results

Verified cases include:

- English possibility versus Hindi possibility:
  - Hindi is recognized as `hi`.
  - Hindi support is `LIMITED`.
  - No unsupported certainty mutation is emitted.
  - Comparison status is `ABSTAIN` without a semantic model.
- English/Spanish numeric claim:
  - `El` is not extracted as an entity.
  - Numeric extraction remains available.
  - Unsupported cross-language mutation labels are not emitted.
- Bengali, Punjabi, Tamil, and Telugu script recognition.
- Empty and numeric-only input handling.
- Mixed-script uncertainty.

Existing English certainty, numeric, temporal, entity, location, negation,
graph, and sequence behavior remained passing.

## 6. API compatibility

The following smoke checks returned HTTP 200:

- `GET /health`
- `GET /models`
- `POST /compare`
- `POST /verify`
- `POST /analyze`
- `POST /analyze/sequence`
- `POST /analyze/graph`

Existing endpoint names and existing response fields were preserved. New
metadata is optional/additive, including support status, comparison status,
language fields, and abstention reason.

The `/compare` endpoint continues to return its scalar
`semantic_similarity` field and relatedness interpretation.

## 7. Test results

Focused Stage 6.1A, API, and Stage 5.1 safety tests:

```text
51 passed in 1.47s
```

Full regression suite:

```text
67 passed, 1 skipped in 1.84s
```

The single skipped test is the existing optional real-model integration test;
models were intentionally not enabled.

Syntax validation:

```text
Syntax OK: 24 files
```

The syntax check used AST parsing with Python bytecode generation disabled.

`git diff --check` passed.

## 8. Model loading status

Embedding and NLI models remained disabled:

```text
embedding: loaded=False, initialization_status=disabled
nli: loaded=False, initialization_status=disabled
```

No model download was triggered. The lexical fallback remained active.

## 9. Known limitations

- Language identification remains dependency-free and heuristic.
- Script detection does not establish the actual language with certainty.
- Hindi and other recognized scripts have no multilingual certainty, negation,
  temporal, or entity lexicons in this milestone.
- Spanish and French recognition is limited to marker heuristics.
- Other Latin-script languages are conservatively unsupported when they do not
  match the English marker set.
- No multilingual semantic alignment was evaluated.
- No model-backed comparison was enabled.
- English detection can still be imperfect for very short or unusual English
  text.
- Numeric extraction is retained for unsupported text because numbers are
  language-neutral in many cases, but their semantic interpretation is not
  asserted.
- No calibrated language or mutation probabilities are provided.

## 10. Remaining risks

- A heuristic language detector can misclassify short or mixed-language text.
- A future embedding integration must be gated separately from mutation
  classification.
- Language-pair-specific thresholds and multilingual benchmark data remain
  necessary before enabling cross-language mutation labels.
- Existing lexical similarity scores can still be numerically nonzero for
  cross-language inputs; callers must use the explicit comparison status.

## 11. Verdict

## PASS

Stage 6.1A acceptance criteria were met:

- Unsupported Latin-script inputs are not silently treated as supported English
  when they are recognized or cannot be conservatively identified.
- Unknown and unsupported states are explicit.
- The Spanish `El` false entity case is fixed.
- Cross-language fallback comparisons abstain from definitive mutation labels.
- Existing English mutation behavior passes.
- Existing API endpoints and fields remain compatible.
- Stage 5.1 verification tests remain passing.
- Optional models remain disabled and no downloads occurred.
- The full regression suite passes with only the documented pre-existing
  optional-model skip.
- Syntax and diff checks pass.

This PASS applies only to the safety and abstention foundation. It does not
claim multilingual semantic understanding or improved multilingual accuracy.
