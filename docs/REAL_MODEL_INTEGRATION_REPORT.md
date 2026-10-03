# Real Model Integration Report

Date: 2026-10-03

## Environment audit

| Item | Observed value |
|---|---|
| Python | 3.11.9, 64-bit Windows |
| PyTorch | 2.8.0+cpu |
| Transformers | 4.55.4 |
| Sentence Transformers | 4.1.0 |
| FAISS | 1.11.0 available |
| GPU/CUDA | No GPU; `torch.cuda.is_available()` was `False`; CUDA version was `None`; `nvidia-smi` was unavailable |
| Physical RAM | 15.42 GB |
| Available RAM at audit | 2.24 GB |

The compatible environment is CPU-first Python 3.11 with the existing Torch
CPU build. The optional dependency set is recorded in
[requirements-advanced.txt](../ml-service/requirements-advanced.txt). The
machine had low free memory during the audit, so model loading should be
performed one process at a time and not alongside unrelated heavyweight
workloads.

## Embedding model

Model: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

- Download and initialization succeeded.
- Device: CPU.
- Load time: 205.491 seconds in a fresh process.
- Output shape: `[3, 384]`.
- Normalization: all measured vector norms were `1.0`.
- Batch inference latency: 0.134 seconds for three texts.
- Subsequent two-text inference: 0.025 seconds.
- Paraphrase similarity: `0.855798`.
- Unrelated similarity: `0.043716`.
- Available RAM after probe: approximately 2.321 GB.

These values demonstrate semantic relatedness behavior, not factual
confidence.

## NLI model

Model: `MoritzLaurer/mDeBERTa-v3-base-mnli-xnli`

- Download and initialization succeeded.
- Device: CPU.
- Load time: 227.780 seconds in a fresh process.
- Actual model configuration mapping:
  - `0: entailment`
  - `1: neutral`
  - `2: contradiction`
- Entailment probe scores: `[0.995360, 0.003983, 0.000657]`.
- Contradiction probe scores: `[0.000197, 0.000278, 0.999525]`.
- Neutral probe scores: `[0.005814, 0.984133, 0.010052]`.
- First measured inference: 0.280 seconds.
- Later measured inference: 0.135 seconds.
- Available RAM after probe: approximately 2.981 GB.

The application maps labels from the model configuration rather than assuming
class-index order.

## End-to-end sequence

The four requested messages were sent through `POST /analyze` with both model
flags enabled. The application reported:

- Embedding model loaded: `true`, CPU, fallback inactive.
- NLI model loaded: `true`, CPU, fallback inactive.
- Semantic similarity between the first and final messages: `0.1961`.
- Certainty change: `INCREASED`.
- Urgency change: `INCREASED`.
- Investment-persuasion indicators: detected after adding `buy immediately`
  and `guaranteed` indicators to the heuristic vocabulary.
- Evidence: two records from the local demo corpus, both with null source URLs.
- Verification: model-backed when the NLI model is enabled.
- Human review: recommended for mutation and uncertainty signals.

The demo corpus includes passages contradicting a guaranteed share-price
increase and risk-free investment language. A `REFUTED` result in this probe is
therefore evidence-dependent; urgency alone does not produce a false verdict.
The corpus is explicitly demonstration data and is not a real-world source.

## Tests

The lightweight regression suite passed:

```text
14 passed
```

Opt-in model integration tests are in
[test_real_models.py](../ml-service/tests/test_real_models.py). Run them only
after the checkpoints are available:

```powershell
cd "C:\ABHIMANYU CHAKRAVYUHA\ml-service"
$env:ENABLE_TRANSFORMERS="true"
$env:ENABLE_NLI="true"
python -m pytest -m integration -q
```

## Limitations

- No GPU or CUDA execution was available.
- Memory measurements are process/environment observations, not a controlled
  peak-RSS benchmark.
- The local evidence corpus is small and synthetic/demo-oriented.
- Claim extraction and mutation indicators remain heuristic.
- BM25 and FAISS are available in the environment but the current default
  retriever remains lexical fallback; no claim is made that dense retrieval is
  active in this report.
- No calibrated probability or benchmark accuracy is reported.

## Startup commands

Lightweight fallback mode:

```powershell
cd "C:\ABHIMANYU CHAKRAVYUHA\ml-service"
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Advanced CPU mode:

```powershell
cd "C:\ABHIMANYU CHAKRAVYUHA\ml-service"
python -m pip install -r requirements-advanced.txt
$env:ENABLE_TRANSFORMERS="true"
$env:ENABLE_NLI="true"
$env:MODEL_DEVICE="cpu"
uvicorn app.main:app --reload --port 8000
```

## Final mode

Advanced mode was successfully validated in a controlled process with both
requested models loaded and actual inference completed. The default startup
configuration remains fallback mode unless both feature flags are explicitly
enabled.
