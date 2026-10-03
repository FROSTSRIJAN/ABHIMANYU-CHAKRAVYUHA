# Stage 6.2 Full Multilingual Model Report

## Final status

**PARTIAL**

The Stage 6.2 training and evaluation infrastructure is implemented and the
cached pretrained multilingual encoder completed real CPU inference. A
fine-tuned checkpoint was subsequently produced through a bounded CPU run.
The application remains safe and backward compatible, and the new checkpoint
is opt-in rather than the default.

## Architecture

The implementation preserves the existing pipeline:

`language assessment -> semantic relatedness -> alignment -> structured
attribute comparison -> mutation classification -> confidence/abstention ->
explanation -> graph`

The existing `ModelManager` remains the single lazy loading boundary. The
pretrained encoder remains selected through `EMBEDDING_MODEL_NAME`. An
explicit local checkpoint can be selected through `EMBEDDING_MODEL_PATH`.
Models remain disabled by default, and a missing checkpoint keeps the lexical
fallback active. Similarity is not treated as a mutation probability or factual truth score, and
Stage 5.1 evidence-verification safeguards were not changed.

New training utilities:

- `ml-service/training/dataset.py`: schema validation, grouped leakage checks,
  hashes, and manifests.
- `ml-service/training/train.py`: validation-only by default; explicit,
  local-only fine-tuning with `--train`.
- `ml-service/training/evaluate.py`: separate fallback, mocked, and real
  evaluation modes.
- `ml-service/training/stage_6_2_dataset.json`: synthetic grouped data.
- `ml-service/training/config.json`: reproducible training configuration.
- `ml-service/training/MODEL_CARD.md`: intended use and limitations.

No implicit download is performed. `--allow-downloads` is required to permit
model acquisition during a deliberate training run.

## Model and actual inference

### Base model

`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

The model was already present in the local Hugging Face cache. It was loaded
with `local_files_only=True` and `HF_HUB_OFFLINE=1`; no model download occurred.

Measured CPU inference:

- Load time: **1.534 seconds**
- First six-sentence batch: **0.297 seconds**
- Subsequent six-sentence batch: **0.034 seconds**
- Embedding dimension: **384**
- Normalization: enabled
- English/Hindi equivalent probe similarity: **0.0650**
- English paraphrase probe similarity: **0.9508**
- Unrelated English probe similarity: **0.0151**

The low English/Hindi score for this short probe demonstrates that a cached
pretrained encoder alone does not establish reliable cross-language alignment
for this application. It is not a claim of multilingual model failure in
general; the observed value is one measured probe.

### Fine-tuning status

**COMPLETED ON CPU.**

The optional training dependency was upgraded in the active Python 3.11
environment from `accelerate 0.24.0` to `1.15.0`. The bounded local command
completed one epoch and two optimizer steps over the seven-example training
split. The first attempt was blocked by an interactive Weights & Biases login;
the successful retry disabled that unrelated telemetry integration.

Command:

```powershell
$env:WANDB_DISABLED="true"
Set-Location C:\ABHIMANYU CHAKRAVYUHA\ml-service\training
python train.py --train
```

Checkpoint: `ml-service/training/artifacts/`

The checkpoint contains `model.safetensors`, tokenizer/configuration files, and
`training_metadata.json`. Its SHA-256 is
`4E7C9AAAA838210F1D782B39D3533601A22B56ABE83D2655F4B1F71518BD9E3E`, which
differs from the cached baseline weight hash
`EAA086F0FFEE582AEB45B36E34CDD1FE2D6DE2BEF61F8A559A1BBC9BD955917B`.
The checkpoint loaded independently and through `ModelManager` with
`EMBEDDING_MODEL_PATH` set.

## Dataset and manifest

The Stage 6.2 dataset is synthetic and template-derived. It contains no
human-reviewed labels.

- Examples: **16**
- Train: **7**
- Validation: **4**
- Test: **5**
- Language pairs: `en-hi` 9, `en-es` 6, `en-fr` 1
- Group leakage: **passed**
- Dataset hash:
  `cbb05d037da8665de4829bd78d5d5662f3583c6a06b8d0ed55c854f0ee783523`
- Manifest:
  `ml-service/training/stage_6_2_dataset_manifest.json`

The dataset is appropriate for pipeline validation only. It is too small and
synthetic for claims of multilingual generalization.

## Evaluation

The existing Stage 6.1C benchmark was run in three separate modes using the
cached pretrained model for the real mode. Dataset hash:
`faa14d3bd1229a14df844e9f425d27e63b8be4dae69d5c2d55c3c93cae815846`.

### Deterministic fallback

- Alignment F1: **1.0000**
- Mutation precision / recall / F1: **1.0000 / 1.0000 / 1.0000**
- Positive mutation detection: **1.0000**
- Equivalent false-mutation rate: **0.0000**
- Unrelated false-mutation rate: **0.0000**
- Abstention rate: **0.4286**

This benchmark path uses the controlled Stage 6.1C structured inputs and
continues to abstain from unsupported cross-language semantic inference.

### Mocked semantic model

- Alignment F1: **1.0000**
- Mutation precision / recall / F1: **1.0000 / 1.0000 / 1.0000**
- Exact mutation-label-set match: **1.0000**
- Positive mutation detection: **1.0000**
- Equivalent false-mutation rate: **0.0000**
- Unrelated false-mutation rate: **0.0000**

These are harness results and are not real model accuracy.

### Actual pretrained baseline versus fine-tuned checkpoint

Evaluation was restricted to the held-out `test` split (five examples), using
the same evaluator and threshold for both models.

| Metric | Baseline | Fine-tuned | Difference |
|---|---:|---:|---:|
| Alignment accuracy | 0.6000 | 0.6000 | 0.0000 |
| Mutation precision | unavailable | unavailable | inconclusive |
| Mutation recall | 0.0000 | 0.0000 | 0.0000 |
| Mutation F1 | unavailable | unavailable | inconclusive |
| Equivalent false-mutation rate | 0.0000 | 0.0000 | 0.0000 |

The real evaluator intentionally does not derive structured mutation labels
from embedding scores. Mutation precision/F1 are therefore unavailable and
mutation recall is zero for both models. This is a safety property, not
evidence that either encoder classifies mutations correctly.

Both models produced the same five held-out alignment outcomes. The fine-tuned
checkpoint did not demonstrate measurable improvement and is not the default.

The broader pretrained diagnostic below is retained as historical all-split
context:

- Alignment precision / recall / F1: **0.5714 / 0.5714 / 0.5714**
- Mutation precision / recall / F1: **0.7500 / 0.3750 / 0.5000**
- Exact mutation-label-set match: **0.5714**
- Positive mutation detection: **0.3750**
- Equivalent false-mutation rate: **0.0000**
- Unrelated false-mutation rate: **0.0000**
- Abstention rate: **0.7143**

Per-type positive detection:

| Type | Detection |
|---|---:|
| Certainty escalation | 0.5000 |
| Certainty reduction | 1.0000 |
| Negation | 0.0000 |
| Numeric | 0.0000 |
| Temporal | 1.0000 |

Per-language-pair positive detection was **0.6000 for en-hi** and
**0.0000 for en-es** in the historical small evaluation. These results are
diagnostic, not generalization evidence.

## Error analysis

The baseline and fine-tuned encoders produced identical held-out alignment
predictions. Both preserved zero false mutations because the real evaluator
does not force mutation labels from similarity alone. Positive mutation
classification remains unavailable in this model-only path.

No thresholds were tuned against the held-out split.

## Hardware and environment

- OS: Windows
- Python: 3.11.9
- Installed application environment: FastAPI/Pydantic/test dependencies plus
  `torch 2.8.0`, `transformers 4.55.4`, `sentence-transformers 4.1.0`, and
  `accelerate 1.15.0`
- Available RAM: approximately 15.4 GiB free/physical total approximately
  15.4 GiB reported by the system probe
- GPU: no usable GPU was reported by the Windows video-controller probe
- Runtime device: CPU
- Pretrained model and PyTorch/Transformers were available to the configured
  editor interpreter and the model was loaded from cache

## Validation

- Stage 6.2 focused tests: **9 passed**
- Complete regression suite: **89 passed, 1 skipped**
- Python compilation: **passed**
- Dataset validation and manifest generation: **passed**
- Group leakage validation: **passed**
- API contract: existing endpoint names and schemas unchanged
- Model default: disabled; no automatic download
- API smoke tests: **7/7 endpoints returned HTTP 200**

## Reproduction commands

Validation-only dataset check:

```powershell
cd "C:\ABHIMANYU CHAKRAVYUHA\ml-service"
python training/train.py
python training/build_manifest.py
```

Run tests:

```powershell
python -m pytest -q -p no:cacheprovider tests
```

Run local-only fine-tuning after installing the reviewed optional training
stack:

```powershell
$env:WANDB_DISABLED="true"
python -m pip install -r requirements-advanced.txt
python training/train.py --train --output training/artifacts
```

The command intentionally fails rather than downloading a base model unless
`--allow-downloads` is explicitly supplied.

Run the existing real-model benchmark against the cached model:

```powershell
$env:ENABLE_TRANSFORMERS="true"
$env:STAGE_6_1C_RUN_REAL_MODEL="true"
$env:HF_HUB_OFFLINE="1"
$env:TRANSFORMERS_OFFLINE="1"
python benchmarks/stage_6_1c_runner.py
```

## Known limitations

- The fine-tuned checkpoint did not improve the five-example held-out split.
- The dataset is synthetic and not human-annotated.
- The real benchmark is small and not sufficient for deployment certification.
- Cross-language structured extraction remains limited.
- No probability calibration or reliability curve was implemented.
- CPU latency and memory vary by process and environment.
- Model-backed use remains opt-in and should be reviewed before production.

## Verdict

**PARTIAL.** Stage 6.2 now has reproducible data validation, actual CPU
fine-tuning, independent checkpoint loading, model selection, evaluation,
model-card, and reporting infrastructure. The milestone remains PARTIAL because
the dataset is synthetic and tiny, the held-out comparison showed no
improvement, and positive multilingual mutation detection is not validated by
the model-only evaluator.
