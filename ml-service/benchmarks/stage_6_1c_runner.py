"""Evaluate positive Stage 6.1C cross-lingual mutation cases."""

from __future__ import annotations

import hashlib
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from app.pipelines.alignment_engine import align_claims
from app.pipelines.claim_normalizer import extract_claims
from app.pipelines.mutation_detector import compare_claim_versions
from app.pipelines.semantic_analyzer import analyze_similarity

DATASET = Path(__file__).with_name("stage_6_1c_dataset.json")


def _hash(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _leakage(examples: list[dict]) -> dict:
    groups: dict[str, set[str]] = defaultdict(set)
    for item in examples:
        groups[item["group"]].add(item["split"])
    leaked = sorted(group for group, splits in groups.items() if len(splits) > 1)
    return {"passed": not leaked, "groups": len(groups), "leaked_groups": leaked}


def _mock_semantic(item: dict) -> dict:
    expected = item["expected_model_alignment"]
    score = {"ALIGNED": 0.9, "RELATED_BUT_UNALIGNED": 0.5, "DISTINCT": 0.2, "ABSTAIN": 0.2}[expected]
    return {"similarity": score, "method": "transformer_embedding", "limitations": [], "comparison_status": "RELATED"}


def _metrics(records: list[dict]) -> dict:
    expected_sets = [set(item["expected_labels"]) for item in records]
    predicted_sets = [set(item["predicted_labels"]) for item in records]
    tp = sum(len(expected & predicted) for expected, predicted in zip(expected_sets, predicted_sets))
    fp = sum(len(predicted - expected) for expected, predicted in zip(expected_sets, predicted_sets))
    fn = sum(len(expected - predicted) for expected, predicted in zip(expected_sets, predicted_sets))
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    f1 = 2 * precision * recall / (precision + recall) if precision is not None and recall and precision + recall else None
    align_expected = [item["expected_alignment"] for item in records]
    align_predicted = [item["predicted_alignment"] for item in records]
    align_labels = {"ALIGNED", "RELATED_BUT_UNALIGNED", "DISTINCT", "UNKNOWN", "ABSTAIN"}
    align_tp = sum(expected == predicted and expected in align_labels for expected, predicted in zip(align_expected, align_predicted))
    alignment_precision = align_tp / len(align_predicted) if align_predicted else None
    alignment_recall = align_tp / len(align_expected) if align_expected else None
    alignment_f1 = (
        2 * alignment_precision * alignment_recall / (alignment_precision + alignment_recall)
        if alignment_precision is not None and alignment_recall is not None and alignment_precision + alignment_recall
        else None
    )
    exact = sum(expected == predicted for expected, predicted in zip(expected_sets, predicted_sets)) / len(records)
    equivalent = [item for item in records if item["kind"] == "equivalent"]
    unrelated = [item for item in records if item["kind"] == "unrelated"]
    positives = [item for item in records if item["kind"] == "positive"]
    def false_rate(items: list[dict]) -> float | None:
        return sum(bool(item["predicted_labels"]) for item in items) / len(items) if items else None
    per_pair: dict[str, dict] = {}
    for pair in sorted({item["language_pair"] for item in records}):
        subset = [item for item in records if item["language_pair"] == pair]
        pair_tp = sum(bool(set(item["expected_labels"]) & set(item["predicted_labels"])) for item in subset)
        pair_predicted = sum(bool(item["predicted_labels"]) for item in subset)
        per_pair[pair] = {
            "examples": len(subset),
            "mutation_precision": pair_tp / pair_predicted if pair_predicted else None,
            "positive_detection_rate": sum(bool(item["predicted_labels"]) for item in subset if item["kind"] == "positive") / max(1, sum(item["kind"] == "positive" for item in subset)),
        }
    per_type = {}
    for mutation_type in sorted({item.get("mutation_type") for item in records if item.get("mutation_type")}):
        subset = [item for item in positives if item.get("mutation_type") == mutation_type]
        per_type[mutation_type] = {"examples": len(subset), "detection_rate": sum(mutation_type in item["predicted_labels"] for item in subset) / len(subset) if subset else None}
    return {
        "alignment_precision": alignment_precision,
        "alignment_recall": alignment_recall,
        "alignment_f1": alignment_f1,
        "mutation_precision": precision,
        "mutation_recall": recall,
        "mutation_f1": f1,
        "exact_mutation_label_set_match": exact,
        "abstention_rate": sum(item["predicted_abstention"] for item in records) / len(records) if records else None,
        "false_mutation_rate_equivalent": false_rate(equivalent),
        "false_mutation_rate_unrelated": false_rate(unrelated),
        "positive_mutation_detection_rate": sum(bool(item["predicted_labels"]) for item in positives) / len(positives) if positives else None,
        "per_language_pair": per_pair,
        "per_mutation_type": per_type,
    }


def evaluate(mode: str, payload: dict) -> dict:
    records = []
    for item in payload["examples"]:
        source = extract_claims([item["original_claim"]])[0]
        target = extract_claims([item["modified_claim"]])[0]
        if mode == "mocked":
            semantic = _mock_semantic(item)
        elif mode == "deterministic":
            semantic = None
        else:
            semantic = analyze_similarity(source["normalized_text"], target["normalized_text"])
        if mode == "real" and semantic["method"] != "transformer_embedding":
            predicted_alignment = "UNAVAILABLE"
            result = {"mutation_types": []}
        else:
            alignment = align_claims(source["normalized_text"], target["normalized_text"], semantic)
            result = compare_claim_versions(source, target, semantic)
            predicted_alignment = alignment["alignment_status"]
        expected_labels = set(item["expected_mutation_labels"])
        predicted_labels = set(result.get("mutation_types", []))
        records.append({
            "example_id": item["example_id"], "split": item["split"], "kind": item["kind"],
            "language_pair": item["language_pair"], "mutation_type": item.get("mutation_type"),
            "expected_labels": sorted(expected_labels), "predicted_labels": sorted(predicted_labels),
            "expected_alignment": item["expected_model_alignment"] if mode != "deterministic" else item["expected_alignment"],
            "predicted_alignment": predicted_alignment,
            "predicted_abstention": predicted_alignment in {"ABSTAIN", "UNKNOWN", "UNAVAILABLE"} or not predicted_labels,
        })
    return {
        "mode": mode,
        "metrics": _metrics(records),
        "development": _metrics([item for item in records if item["split"] == "development"]),
        "heldout": _metrics([item for item in records if item["split"] == "heldout"]),
        "records": records,
    }


def run(path: Path = DATASET) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    modes = ["deterministic", "mocked"]
    if os.getenv("STAGE_6_1C_RUN_REAL_MODEL", "").lower() == "true" and os.getenv("ENABLE_TRANSFORMERS", "").lower() == "true":
        modes.append("real")
    return {
        "dataset_version": payload["dataset_version"],
        "synthetic": payload["synthetic"],
        "dataset_hash": _hash(payload),
        "split_integrity": _leakage(payload["examples"]),
        "counts": Counter(item["split"] for item in payload["examples"]),
        "evaluations": [evaluate(mode, payload) for mode in modes],
        "real_model_note": "Real mode is unavailable unless explicitly enabled with STAGE_6_1C_RUN_REAL_MODEL=true and ENABLE_TRANSFORMERS=true.",
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
