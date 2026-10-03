# Team Handoff

## 1. Project overview

Abhimanyu Chakravyuha is an NLP intelligence system for comparing claims,
detecting conservative mutation indicators, and attaching evidence-aware
verification results. The active implementation is the Python service in
`ml-service/`.

Current capabilities include:

- Claim normalization and deterministic English mutation analysis.
- Typed numeric, currency, unit, temporal, certainty, urgency, negation, and
  persuasion signals.
- Optional multilingual sentence-transformer similarity.
- Explicit language, alignment, comparison, limitation, and abstention
  metadata.
- Evidence retrieval and conservative verification labels.
- Ordered sequence analysis and claim-graph serialization.
- Optional Groq semantic interpretation with strict JSON validation.
- Lazy model loading with lexical fallback.

The system is not production-ready for factual verification. The multilingual
datasets are synthetic and small, no human-reviewed real-world evaluation has
been established, and mutation detection remains insufficiently validated.

## 2. Architecture

```text
User input
  -> FastAPI request validation
  -> claim extraction and normalization
  -> deterministic mutation analysis
  -> lexical or optional embedding semantic relatedness
  -> evidence retrieval and provenance-aware verification
  -> sequence or graph analysis
  -> JSON API response
```

Important modules:

- `app/main.py`: FastAPI routes and request-size limits.
- `app/core/schemas.py`: Pydantic request and response contracts.
- `app/pipelines/claim_extractor.py`: claim and structured signal extraction.
- `app/pipelines/claim_normalizer.py`: normalization and typed attributes.
- `app/pipelines/mutation_detector.py`: certainty, urgency, persuasion, and
  structured mutation logic.
- `app/pipelines/semantic_analyzer.py`: relatedness, language metadata,
  abstention, and optional provider metadata.
- `app/pipelines/embedding_engine.py`: lexical similarity or optional
  sentence-transformer similarity.
- `app/pipelines/alignment_engine.py`: supported cross-language alignment
  states and pair gating.
- `app/pipelines/evidence_retriever.py`: bounded evidence candidate retrieval.
- `app/pipelines/verifier.py`: provenance-aware evidence verification and
  optional NLI.
- `app/pipelines/claim_graph.py`: nodes, sequential edges, and graph metadata.
- `app/services/model_manager.py`: lazy embedding/NLI loading and fallback
  state.
- `app/services/groq_provider.py`: advisory-only Groq interpretation boundary.

## 3. Current API endpoints

All endpoints return JSON. Empty strings are rejected. Inputs exceeding
`ABHIMANYU_MAX_INPUT_CHARS` return HTTP 413. Sequence endpoints accept at most
`ABHIMANYU_MAX_SEQUENCE_LENGTH` messages.

### `GET /health`

Returns service liveness:

```json
{"status": "ok", "service": "ml-service"}
```

### `GET /models`

Returns lazy model registry state, including `component`, `name`, `loaded`,
`fallback_active`, `initialization_status`, and limitations. Model instances
are not serialized.

### `POST /compare`

Request:

```json
{"first": "The company may launch a product.", "second": "The company is expected to launch a product."}
```

Returns `semantic_similarity`, a relatedness disclaimer, and additive
`semantic_analysis` metadata. Similarity is not truth probability.

### `POST /verify`

Request:

```json
{
  "claim": "The market rose today.",
  "evidence": [
    {
      "document_id": "source-1",
      "passage": "The market rose today.",
      "source_name": "Example source",
      "source_type": "provided"
    }
  ]
}
```

Returns `label`, `evidence`, `limitations`, `method`, and an optional
explanation. Labels are `SUPPORTED`, `REFUTED`, `INSUFFICIENT_EVIDENCE`, and
`CONFLICTING`. API-provided evidence is marked unverified and cannot by itself
produce a decisive authoritative verdict.

### `POST /analyze`

Request:

```json
{"messages": ["The company may launch a product.", "The company will launch a product."], "evidence": []}
```

Returns status, language, extracted claims, semantic similarity,
`mutation_analysis`, verification, uncertainty, explanation, and support
metadata.

### `POST /analyze/sequence`

Request:

```json
{"messages": ["It may happen.", "It will happen.", "Buy immediately."]}
```

Returns ordered `pairs`. Each pair includes message index, semantic
similarity, certainty and urgency changes, added claims, removed qualifiers,
persuasion indicators, and explanation. These are heuristic observations.

### `POST /analyze/graph`

Request:

```json
{"messages": ["The company may launch.", "The company will launch."], "evidence": []}
```

Returns normalized claim nodes, sequential mutation edges, verification
annotations, graph metadata, and review flags. Edge metadata preserves
alignment and abstention information where available.

## 4. ML/NLP implementation

Normalization preserves original text while extracting typed attributes.
Numeric values include normalized value, currency/unit context, numeric type,
and source spans. Temporal values are handled separately to avoid treating
dates as ordinary numeric mutations. English certainty, negation, urgency,
and persuasion rules are deterministic and conservative.

The mutation taxonomy includes certainty escalation/reduction, negation,
numeric, temporal, entity, and related structured changes. Similarity never
creates a mutation label by itself.

Cross-language statuses include `ALIGNED`, `RELATED_BUT_UNALIGNED`,
`DISTINCT`, `UNKNOWN`, and `ABSTAIN`. Comparison statuses include `RELATED`,
`DISTINCT`, `UNKNOWN`, and `ABSTAIN`. Unsupported or insufficiently aligned
language pairs must remain uncertain.

The optional baseline model is
`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`. It is disabled
by default and loaded lazily. An explicit local fine-tuned checkpoint can be
selected with `EMBEDDING_MODEL_PATH`; a missing checkpoint keeps lexical
fallback active.

Groq is optional and advisory only. It interprets claim relationships and
returns validated JSON. It does not establish factual truth, create evidence,
invent citations or URLs, or override provenance and abstention safeguards.

## 5. Verification and safety

Verification is evidence-aware and conservative:

- Demonstration-only evidence cannot establish a decisive verdict.
- API-supplied evidence is forced to `provenance_verified=false`.
- Weak, irrelevant, neutral, conflicting, or missing evidence can produce
  `INSUFFICIENT_EVIDENCE` or `CONFLICTING`.
- Optional NLI is gated by relevance and provenance.
- Negation is clause-aware rather than a document-wide string rule.
- Dates and numbers are compared using typed structured attributes.
- Similarity is relatedness, not factual confidence.
- Unknown language or alignment is surfaced rather than silently treated as
  English.

The verifier remains heuristic without authoritative retrieval and calibrated
models. Direct internal construction of trusted evidence is not a substitute
for a production authenticated evidence store.

## 6. Model and evaluation status

The Stage 6.2 dataset contains 16 synthetic examples: 7 train, 4 validation,
and 5 test, with zero human-reviewed examples and grouped leakage checks
passing.

Actual CPU fine-tuning completed for one epoch and two optimizer steps after
installing `accelerate 1.15.0`. The checkpoint is stored under
`ml-service/training/artifacts/`, is excluded from Git, and is not the default
model.

On the five-example held-out split:

- Baseline alignment accuracy: `0.6000`
- Fine-tuned alignment accuracy: `0.6000`
- Demonstrated improvement: none
- Mutation precision/F1: unavailable in the embedding-only evaluator
- Mutation recall: `0.0000` for both
- Equivalent false-mutation rate: `0.0000` for both

These are diagnostic synthetic results, not real-world accuracy. Do not claim
production readiness or reliable multilingual mutation detection.

## 7. Setup instructions

From PowerShell:

```powershell
cd "C:\ABHIMANYU CHAKRAVYUHA"
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
cd ml-service
python -m pip install -r requirements.txt
```

Optional model/training dependencies:

```powershell
python -m pip install -r requirements-advanced.txt
```

Create a local `.env` from `.env.example`. Keep credentials blank in tracked
files and configure secrets only in the process environment. Relevant safe
defaults are:

```text
ENABLE_TRANSFORMERS=false
ENABLE_NLI=false
MODEL_DEVICE=cpu
GROQ_ENABLED=false
GROQ_API_KEY=
```

Start the service:

```powershell
uvicorn app.main:app --reload --port 8000
```

Run tests:

```powershell
python -m pytest -q -p no:cacheprovider tests
```

Validate data without loading a model:

```powershell
python training/train.py
python training/build_manifest.py
```

Run real-model evaluation against the local checkpoint:

```powershell
python training/evaluate.py --mode real --model-path training/artifacts --split test
```

Explicitly enable the baseline model:

```powershell
$env:ENABLE_TRANSFORMERS="true"
$env:HF_HUB_OFFLINE="1"
$env:TRANSFORMERS_OFFLINE="1"
uvicorn app.main:app --reload --port 8000
```

Explicitly select the fine-tuned checkpoint:

```powershell
$env:ENABLE_TRANSFORMERS="true"
$env:EMBEDDING_MODEL_PATH="C:\ABHIMANYU CHAKRAVYUHA\ml-service\training\artifacts"
uvicorn app.main:app --reload --port 8000
```

Use Groq only with a securely injected runtime key and a currently available
model:

```powershell
$env:GROQ_ENABLED="true"
$env:GROQ_API_KEY="<set securely; never commit>"
$env:GROQ_MODEL="openai/gpt-oss-20b"
uvicorn app.main:app --reload --port 8000
```

## 8. Team ownership

### Srijan — ML/NLP

Claim processing, mutation detection, model integration, multilingual
evaluation, Groq semantic interpretation, ML testing, and safety.

### Adit — Backend

API contracts, backend integration, persistence/database integration,
request/response validation, and backend testing.

### Auranzeb — Frontend

UI integration, claim comparison, mutation timeline, graph visualization,
evidence and uncertainty presentation, API errors, and loading states.

## 9. Integration contracts

- Do not change existing response fields without coordinating with all owners.
- Treat similarity only as semantic relatedness, never factual truth.
- Preserve `UNKNOWN`, `ABSTAIN`, limitations, uncertainty, and abstention
  reasons in the UI.
- Do not display demonstration or caller-supplied evidence as verified
  evidence.
- Keep optional model and provider behavior explicit.
- Coordinate schema changes before implementation.

## 10. Known issues and next milestones

Priority order:

1. Build a human-reviewed multilingual benchmark with grouped held-out splits.
2. Improve mutation detection and calibrate labels on real data.
3. Strengthen cross-language entity, number, currency, and temporal alignment.
4. Add backend/frontend integration tests.
5. Replace caller-trust assumptions with an authenticated evidence store.
6. Harden performance, observability, deployment, and credential rotation.

## 11. Current release status

The current release is suitable for local demonstration and controlled
hackathon use with limitations. The verified suite is **89 passed, 1 skipped**,
Python compilation and whitespace checks pass, and all seven API smoke tests
return HTTP 200. Groq live validation succeeded with an available model, but
the provider remains advisory-only. The system is **not production-ready** for
factual verification or reliable multilingual mutation intelligence.
