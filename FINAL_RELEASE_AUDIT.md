# Final Release Audit

## Verdict

**PARTIAL**

The ML service is suitable for local demonstration, hackathon presentation,
and publication as a clearly documented research/demo repository. It is not
ready for production factual verification or production-grade multilingual
mutation analysis.

## Fixes applied

- Removed the credential-looking value from `ml-service/.env.example`; the
  file now contains only an empty placeholder. The exposed credential should
  be revoked and rotated immediately if it was ever active or committed.
- Added whitespace validation for `/compare` and `/verify` claim fields.
- Added explicit `authoritative: false` verification metadata and
  `provenance_verified` handling. API-supplied evidence is forced
  non-authoritative and cannot independently produce a decisive verdict.
- Expanded optional model-load failure handling for common dependency,
  configuration, timeout, and connection failures.
- Preserved existing endpoints, public fields, Stage 5.1 behavior, and
  conservative abstention.

## Test results

- Full pytest suite: **89 passed, 1 skipped, 0 failed**
- Python compilation: **passed**
- `git diff --check`: **passed**
- Secret-pattern scan of tracked files: **no secret-like content detected**
- Groq live validation: **completed using the supplied credential; the
  credential is not retained in `.env.example`**
- Fine-tuning: **completed on CPU**; checkpoint is available locally at
  `ml-service/training/artifacts/` and is not enabled by default

## Endpoint validation

| Endpoint | Result | Validation |
|---|---:|---|
| `GET /health` | 200 | `status=ok` |
| `GET /models` | 200 | model registry serialized |
| `POST /compare` | 200 | similarity and semantic metadata returned |
| `POST /verify` | 200 | empty evidence returned `INSUFFICIENT_EVIDENCE` |
| `POST /analyze` | 200 | success response serialized |
| `POST /analyze/sequence` | 200 | pairwise response serialized |
| `POST /analyze/graph` | 200 | graph response serialized |

Malformed `/compare` cases for blank, missing, and null claim fields returned
HTTP 422. Existing oversized-input behavior remains covered by tests.

## Model status

The cached
`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` model loaded
successfully in offline CPU mode:

- Dimension: 384
- Load time: 1.534 seconds
- First batch: 0.297 seconds
- Subsequent batch: 0.034 seconds
- English paraphrase similarity: 0.9508
- English/Hindi probe similarity: 0.0650
- Unrelated English similarity: 0.0151

The low English/Hindi score was observed and not threshold-tuned. Cross-language
alignment remains conservative when the model does not establish sufficient
support.

Model loading is lazy and disabled by default. Missing optional dependencies
return structured degraded model state rather than pretending a model loaded.
An explicit local checkpoint can be selected with `EMBEDDING_MODEL_PATH`; a
missing configured checkpoint leaves the lexical fallback active.

## Benchmark status

The prior actual pretrained-model benchmark remains the only real model result:

- Alignment precision / recall / F1: `0.5714 / 0.5714 / 0.5714`
- Mutation precision / recall / F1: `0.7500 / 0.3750 / 0.5000`
- Positive mutation detection: `0.3750`
- Equivalent false-mutation rate: `0.0000`
- Unrelated false-mutation rate: `0.0000`
- Abstention rate: `0.7143`

The fine-tuned checkpoint was evaluated on the five-example held-out test
split and matched the baseline alignment accuracy at `0.6000`; it did not
demonstrate measurable improvement. Mutation precision/F1 are unavailable in
the embedding-only evaluator because similarity is not converted into mutation
labels. Mocked provider/model results are not real model performance.

## Groq status

The optional Groq provider is implemented with:

- environment-only configuration;
- default-disabled behavior;
- bounded retries;
- timeout configuration;
- strict JSON validation;
- explicit provider metadata;
- no evidence/citation/URL generation;
- no factual-verification authority;
- safe `ABSTAIN` fallback on unavailable, malformed, or failed responses.

The supplied credential was used only in process memory for a minimal live
request. The configured `llama-3.1-8b-instant` model returned a sanitized
`404 model_not_found`; the provider model catalog was queried without exposing
the credential. A second request using `openai/gpt-oss-20b` succeeded in
1.930 seconds with valid JSON. The project provider then returned
`RELATED_BUT_UNALIGNED` with no mutation labels in one attempt after its schema
prompt was tightened. Groq remains advisory-only and factual verification was
not performed. The credential is not retained in `.env.example`; revoke and
rotate it if it was previously active or committed.

## Security findings

| # | Severity | File | Lines | Vulnerability | Confidence |
|---|----------|------|-------|---------------|------------|
| 1 | 🟠 HIGH | `ml-service/.env.example` | 10 | A credential-looking Groq key was present in the example configuration; it was replaced with an empty placeholder. Revoke/rotate the key if active or previously committed. | 10/10 |
| 2 | 🟡 MEDIUM | `ml-service/app/core/schemas.py`, `ml-service/app/pipelines/verifier.py` | evidence schema and verdict path | Caller-supplied `provided` evidence was not independently authenticated. API-supplied evidence is now forced `provenance_verified=false` and cannot independently produce a decisive verdict; trusted-store integration remains a deployment responsibility. | 8/10 |

No secret-like values remain in the tracked-file pattern scan. No automatic
push or commit was performed.

## Evidence and verification limitations

- Empty, weak, irrelevant, demonstration-only, and conflicting evidence remain
  conservative.
- Demonstration evidence cannot independently establish a decisive verdict.
- Groq cannot create or strengthen evidence.
- Caller-provided evidence now produces `INSUFFICIENT_EVIDENCE` for decisive
  verification paths and is explicitly marked non-authoritative. Production
  consumers must authenticate evidence against a trusted store before treating
  it as factual verification.
- Similarity does not establish truth or causation.
- Graph chronology and connectivity do not imply causation.

## Known model risks

- Cross-language pretrained similarity is inconsistent on the measured probes.
- Hindi and Spanish structured extraction remains limited.
- Synthetic datasets are too small for generalization claims.
- The fine-tuned result is based on a tiny synthetic dataset and did not
  improve the held-out comparison.
- No calibration study supports interpreting confidence as probability.

## Files modified in this audit

- `ml-service/.env.example`
- `ml-service/app/core/schemas.py`
- `ml-service/app/services/model_manager.py`
- `ml-service/app/core/config.py`
- `ml-service/training/evaluate.py`
- `ml-service/tests/test_model_selection.py`
- `docs/STAGE_6_2_FULL_MULTILINGUAL_MODEL_REPORT.md`
- `ml-service/app/pipelines/verifier.py`
- `ml-service/tests/test_api.py`
- `FINAL_RELEASE_AUDIT.md`

## Commands

Start backend:

```powershell
cd "C:\ABHIMANYU CHAKRAVYUHA\ml-service"
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Run tests:

```powershell
cd "C:\ABHIMANYU CHAKRAVYUHA\ml-service"
python -m pytest -q -p no:cacheprovider tests
```

Run syntax and diff checks:

```powershell
python -m compileall -q app training tests
git diff --check
```

## GitHub pre-push checklist

- Revoke and rotate any previously exposed provider key.
- Confirm `.env`, caches, virtual environments, temporary logs, and model
  artifacts are ignored.
- Run the complete test suite and API smoke checks.
- Review `git diff --check`.
- Review the staged file list manually.
- Verify no credentials occur in tracked files or history.
- Push only after a human reviews the residual evidence-trust limitation.

## Suitability

- Local demonstration: **suitable with documented limitations**
- Hackathon presentation: **suitable with explicit fallback/model caveats**
- Public repository: **suitable after credential rotation and history review**
- Production factual verification: **not suitable**
