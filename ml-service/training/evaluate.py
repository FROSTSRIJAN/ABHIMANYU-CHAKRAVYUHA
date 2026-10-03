"""Evaluate Stage 6.2 data without conflating fallback, mocked, and real modes."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from dataset import load_dataset, manifest


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=Path(__file__).with_name("stage_6_2_dataset.json"))
    parser.add_argument("--mode", choices=("fallback", "mocked", "real"), default="fallback")
    parser.add_argument("--model-path", type=Path)
    parser.add_argument("--model-name", default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    parser.add_argument("--split", choices=("train", "validation", "test", "all"), default="test")
    return parser.parse_args()


def _scores(expected: list[str], predicted: list[str]) -> tuple[int, int, int]:
    left, right = set(expected), set(predicted)
    return len(left & right), len(right - left), len(left - right)


def main() -> int:
    args = _args()
    payload = load_dataset(args.dataset)
    started = time.perf_counter()
    if args.mode == "real":
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as error:
            raise SystemExit("Real evaluation requires sentence-transformers and torch.") from error
        if args.model_path is not None:
            if not args.model_path.exists():
                raise SystemExit(f"Model path does not exist: {args.model_path}")
            model = SentenceTransformer(str(args.model_path), device="cpu", local_files_only=True)
        else:
            model = SentenceTransformer(args.model_name, device="cpu", local_files_only=True)
    else:
        model = None

    records = []
    examples = [
        item for item in payload["examples"]
        if args.split == "all" or item["split"] == args.split
    ]
    if not examples:
        raise SystemExit(f"No examples found for split: {args.split}")
    for item in examples:
        if args.mode == "fallback":
            predicted_alignment = "ABSTAIN" if item["language_pair"] != "en-en" else "DISTINCT"
            predicted_labels = []
        elif args.mode == "mocked":
            predicted_alignment = item["alignment_label"]
            predicted_labels = item["mutation_labels"][:]
        else:
            embeddings = model.encode([item["original_claim"], item["modified_claim"]], normalize_embeddings=True)
            similarity = float(embeddings[0] @ embeddings[1])
            predicted_alignment = "ALIGNED" if similarity >= 0.75 else "RELATED_BUT_UNALIGNED" if similarity >= 0.35 else "DISTINCT"
            predicted_labels = []
        records.append({
            "example_id": item["example_id"],
            "expected_alignment": item["alignment_label"],
            "predicted_alignment": predicted_alignment,
            "expected_labels": item["mutation_labels"],
            "predicted_labels": predicted_labels,
            "split": item["split"],
        })

    tp = fp = fn = 0
    for item in records:
        a, b, c = _scores(item["expected_labels"], item["predicted_labels"])
        tp += a
        fp += b
        fn += c
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    f1 = 2 * precision * recall / (precision + recall) if precision and recall else None
    output = {
        "mode": args.mode,
        "dataset": manifest(payload),
        "metrics": {
            "mutation_precision": precision,
            "mutation_recall": recall,
            "mutation_f1": f1,
            "alignment_accuracy": sum(item["expected_alignment"] == item["predicted_alignment"] for item in records) / len(records),
            "equivalent_false_mutation_rate": sum(
                bool(item["predicted_labels"])
                for item in records
                if not item["expected_labels"]
            ) / sum(not item["expected_labels"] for item in records),
        },
        "inference_seconds": time.perf_counter() - started,
        "records": records,
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
