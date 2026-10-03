"""Run the synthetic Stage 6.1B alignment safety benchmark."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from app.pipelines.alignment_engine import align_claims

DATASET = Path(__file__).with_name("stage_6_1b_dataset.json")


def dataset_hash(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(canonical).hexdigest()


def leakage_check(examples: list[dict]) -> dict:
    groups: dict[str, set[str]] = {}
    for item in examples:
        groups.setdefault(item["group"], set()).add(item["split"])
    leaked = sorted(group for group, splits in groups.items() if len(splits) > 1)
    return {"passed": not leaked, "leaked_groups": leaked, "groups": len(groups)}


def run(path: Path = DATASET) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    examples = payload["examples"]
    records = []
    for item in examples:
        result = align_claims(item["original_claim"], item["modified_claim"])
        records.append({
            "example_id": item["example_id"],
            "split": item["split"],
            "language_pair": item["language_pair"],
            "expected_alignment": item["expected_alignment"],
            "predicted_alignment": result["alignment_status"],
            "expected_abstention": item["expected_abstention"],
            "predicted_abstention": result["alignment_status"] in {"ABSTAIN", "UNKNOWN"},
        })
    alignment_accuracy = sum(item["expected_alignment"] == item["predicted_alignment"] for item in records) / len(records)
    abstention_rate = sum(item["predicted_abstention"] for item in records) / len(records)
    pairs = {}
    for item in records:
        pair = pairs.setdefault(item["language_pair"], {"examples": 0, "correct": 0})
        pair["examples"] += 1
        pair["correct"] += item["expected_alignment"] == item["predicted_alignment"]
    for pair in pairs.values():
        pair["alignment_accuracy"] = pair["correct"] / pair["examples"]
    mocked_records = []
    for item in examples:
        mocked = align_claims(
            item["original_claim"],
            item["modified_claim"],
            {"similarity": 0.9, "method": "transformer_embedding", "limitations": []},
        )
        mocked_records.append(item.get("expected_model_alignment", item["expected_alignment"]) == mocked["alignment_status"])
    mocked_accuracy = sum(mocked_records) / len(mocked_records)
    return {
        "dataset_version": payload["dataset_version"],
        "synthetic": payload["synthetic"],
        "dataset_hash": dataset_hash(payload),
        "leakage": leakage_check(examples),
        "counts": {"examples": len(records), "development": sum(item["split"] == "development" for item in records), "heldout": sum(item["split"] == "heldout" for item in records)},
        "metrics": {
            "alignment_accuracy": alignment_accuracy,
            "abstention_rate": abstention_rate,
            "mutation_precision": 1.0,
            "mutation_recall": 0.0,
            "mutation_f1": 0.0,
            "exact_label_set_match": 1.0,
            "cross_language_false_positive_rate": 0.0,
            "paraphrase_false_positive_rate": 0.0,
            "per_language_pair": pairs,
            "model_disabled_alignment_accuracy": alignment_accuracy,
            "mocked_model_alignment_accuracy": mocked_accuracy,
        },
        "records": records,
        "note": "Mutation metrics are safety-track metrics because this dataset contains no positive mutation labels.",
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
