# ML service

## Run

```powershell
cd "C:\ABHIMANYU CHAKRAVYUHA\ml-service"
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The API exposes `/health`, `/models`, `/compare`, `/verify`, and `/analyze`.
Swagger is available at `/docs`.

The default implementation is deliberately runnable without downloading large
models. It uses lexical similarity and a small local demo evidence corpus.
Those outputs are not calibrated probabilities and are not a substitute for
independent fact checking. Optional multilingual embedding and NLI adapters are
listed by `/models` but are not loaded by default. Set `ENABLE_TRANSFORMERS=true`
or `ENABLE_NLI=true` to opt in after installing and reviewing those models.

`POST /analyze/sequence` returns pairwise semantic similarity and mutation
observations for an ordered message sequence. See
`../docs/model-evaluation.md` and `../docs/model-card.md` for limitations and
evaluation policy.

## Stage 6.2 training and evaluation

The reproducible multilingual training utilities are under `training/`.
Validation is dependency-light and does not load or download a model:

```powershell
python training/train.py
python training/build_manifest.py
```

Fine-tuning is opt-in and requires the reviewed advanced dependencies:

```powershell
python -m pip install -r requirements-advanced.txt
python training/train.py --train --output training/artifacts
```

The training command uses local model files by default and refuses an
uncached model. Pass `--allow-downloads` only when model acquisition has been
explicitly reviewed. The included Stage 6.2 data is synthetic and is not
evidence of production multilingual accuracy. See
`../docs/STAGE_6_2_FULL_MULTILINGUAL_MODEL_REPORT.md`.

## Test

```powershell
python -m pytest
```
