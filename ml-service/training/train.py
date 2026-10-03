"""Validate or optionally fine-tune the Stage 6.2 pair model.

Training is opt-in and local-only by default. No model download occurs unless
the caller explicitly supplies --allow-downloads.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import time
from pathlib import Path

from dataset import load_dataset, manifest


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=Path(__file__).with_name("stage_6_2_dataset.json"))
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("artifacts"))
    parser.add_argument("--config", type=Path, default=Path(__file__).with_name("config.json"))
    parser.add_argument("--train", action="store_true", help="Run fine-tuning instead of validation-only.")
    parser.add_argument("--allow-downloads", action="store_true", help="Explicitly allow model downloads.")
    return parser.parse_args()


def _run_training(payload: dict, config: dict, output: Path, allow_downloads: bool) -> None:
    os.environ.setdefault("WANDB_DISABLED", "true")
    try:
        from sentence_transformers import InputExample, SentenceTransformer, losses
        from torch.utils.data import DataLoader
    except ImportError as error:
        raise RuntimeError(
            "Fine-tuning requires sentence-transformers and torch. "
            "Install requirements-advanced.txt in a dedicated environment."
        ) from error

    model_kwargs = {"device": config.get("device", "cpu")}
    if not allow_downloads:
        model_kwargs["local_files_only"] = True
    try:
        model = SentenceTransformer(config["base_model"], **model_kwargs)
    except Exception as error:
        mode = "local-only mode; the base model is not cached" if not allow_downloads else "model initialization failed"
        raise RuntimeError(f"{mode}: {error}") from error

    examples = [
        InputExample(
            texts=[item["original_claim"], item["modified_claim"]],
            label=1.0 if item["alignment_label"] == "ALIGNED" else 0.0,
        )
        for item in payload["examples"]
        if item["split"] == "train"
    ]
    if not examples:
        raise ValueError("Training split is empty.")
    loader = DataLoader(examples, shuffle=True, batch_size=int(config.get("batch_size", 4)))
    loss = losses.CosineSimilarityLoss(model)
    output.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    training_metrics = model.fit(
        train_objectives=[(loader, loss)],
        epochs=int(config.get("epochs", 1)),
        warmup_steps=0,
        output_path=str(output),
        optimizer_params={"lr": float(config.get("learning_rate", 2e-5))},
    )
    (output / "training_metadata.json").write_text(
        json.dumps(
            {
                "base_model": config["base_model"],
                "config": config,
                "dataset": manifest(payload),
                "weights_updated": True,
                "duration_seconds": round(time.perf_counter() - started, 3),
                "training_metrics": training_metrics or {
                    "epochs_completed": int(config.get("epochs", 1)),
                    "optimizer_steps": len(loader) * int(config.get("epochs", 1)),
                    "train_examples": len(examples),
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def main() -> int:
    args = _parse_args()
    random.seed(42)
    payload = load_dataset(args.dataset)
    print(json.dumps(manifest(payload), indent=2))
    if not args.train:
        print("Validation-only mode: no model was loaded and no weights were changed.")
        return 0
    _run_training(payload, json.loads(args.config.read_text(encoding="utf-8")), args.output, args.allow_downloads)
    print(f"Fine-tuning completed; artifact written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
