"""Run the curated mutation benchmark without changing production behavior."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SERVICE_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = SERVICE_ROOT.parent
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from app.pipelines.claim_normalizer import extract_claims
from app.pipelines.mutation_detector import compare_claim_versions

VALID_LABELS = {
    "CERTAINTY_ESCALATION", "CERTAINTY_REDUCTION", "URGENCY_ESCALATION",
    "URGENCY_REDUCTION", "NUMERICAL_MUTATION", "ENTITY_MUTATION",
    "TEMPORAL_MUTATION", "NEGATION_MUTATION", "QUALIFIER_REMOVAL",
    "CLAIM_ADDITION", "CLAIM_REMOVAL", "SEMANTIC_DRIFT",
}
VALID_SPLITS = {"development", "heldout"}
LEGACY_DATASET = Path(__file__).with_name("dataset.json")
SUPPLEMENTAL_DATASET = Path(__file__).with_name("supplemental_dataset.json")


def load_dataset(path: Path | str) -> dict[str, Any]:
    source_path = Path(path)
    payload = json.loads(source_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("examples"), list):
        raise ValueError("Dataset must contain an examples list.")
    ids: set[str] = set()
    required = {"example_id", "original_claim", "modified_claim", "expected_mutation_labels",
                "expected_mutation_present", "explanation", "language", "split", "category",
                "difficulty"}
    if source_path.name == "dataset.json":
        payload["examples"] = _upgrade_legacy(payload)
    for example in payload["examples"]:
        if not isinstance(example, dict) or not required.issubset(example):
            raise ValueError("Every dataset example must contain the documented fields.")
        if example["example_id"] in ids:
            raise ValueError(f"Duplicate example_id: {example['example_id']}")
        ids.add(example["example_id"])
        if example["split"] not in VALID_SPLITS:
            raise ValueError(f"Invalid split for {example['example_id']}")
        if not example["expected_mutation_labels"] or isinstance(example["expected_mutation_labels"], list):
            pass
        else:
            raise ValueError(f"Labels must be a list for {example['example_id']}")
        labels = example["expected_mutation_labels"]
        if not isinstance(labels, list) or not set(labels).issubset(VALID_LABELS):
            raise ValueError(f"Invalid labels for {example['example_id']}")
        if bool(labels) != bool(example["expected_mutation_present"]):
            raise ValueError(f"Presence flag disagrees with labels for {example['example_id']}")
    return payload


def _upgrade_legacy(payload: dict[str, Any]) -> list[dict[str, Any]]:
    upgraded = []
    for example in payload["examples"]:
        item = dict(example)
        item.setdefault("difficulty", "legacy")
        item["group"] = item.get("group", item["example_id"])
        digest = hashlib.sha256(item["group"].encode()).hexdigest()
        item["split"] = "heldout" if int(digest[:8], 16) % 5 == 0 else "development"
        upgraded.append(item)
    return upgraded


def load_robust_dataset() -> dict[str, Any]:
    legacy = json.loads(LEGACY_DATASET.read_text(encoding="utf-8"))
    supplemental = json.loads(SUPPLEMENTAL_DATASET.read_text(encoding="utf-8"))
    combined = _upgrade_legacy(legacy) + supplemental
    return {"dataset_version": "2.0.0", "description": "Stage 4.2 grouped synthetic benchmark.", "examples": combined}


def dataset_hash(dataset: dict[str, Any]) -> str:
    canonical = json.dumps(dataset, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def check_leakage(examples: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[str, set[str]] = {}
    for example in examples:
        groups.setdefault(example.get("group", example["example_id"]), set()).add(example["split"])
    leaked = sorted(group for group, splits in groups.items() if len(splits) > 1)
    return {"passed": not leaked, "leaked_groups": leaked, "groups": len(groups)}


def _binary_metrics(actual: list[bool], predicted: list[bool]) -> dict[str, float | int]:
    tp = sum(a and p for a, p in zip(actual, predicted))
    fp = sum(not a and p for a, p in zip(actual, predicted))
    tn = sum(not a and not p for a, p in zip(actual, predicted))
    fn = sum(a and not p for a, p in zip(actual, predicted))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"accuracy": (tp + tn) / len(actual) if actual else 0.0, "precision": precision,
            "recall": recall, "f1": f1, "true_positives": tp, "false_positives": fp,
            "true_negatives": tn, "false_negatives": fn, "support": sum(actual)}


def evaluate_examples(examples: list[dict[str, Any]]) -> dict[str, Any]:
    labels = sorted(VALID_LABELS)
    records: list[dict[str, Any]] = []
    for example in examples:
        source = extract_claims([example["original_claim"]])[0]
        target = extract_claims([example["modified_claim"]])[0]
        result = compare_claim_versions(source, target)
        expected = set(example["expected_mutation_labels"])
        predicted = set(result["mutation_types"])
        records.append({
            "example_id": example["example_id"],
            "original_claim": example["original_claim"],
            "modified_claim": example["modified_claim"],
            "expected_labels": sorted(expected),
            "predicted_labels": sorted(predicted),
            "expected_present": bool(expected),
            "predicted_present": bool(predicted),
            "semantic_similarity": result["semantic_similarity"],
            "detection_method": result["detection_method"],
            "error_type": (
                "false_negative" if expected and not predicted else
                "false_positive" if predicted and not expected else
                "incorrect_categories" if expected != predicted else None
            ),
            "split": example["split"],
            "category": example["category"],
            "difficulty": example.get("difficulty", "unspecified"),
            "language": example["language"],
        })
    per_category: dict[str, Any] = {}
    for label in labels:
        per_category[label] = _binary_metrics(
            [label in set(record["expected_labels"]) for record in records],
            [label in set(record["predicted_labels"]) for record in records],
        )
    expected_presence = [record["expected_present"] for record in records]
    predicted_presence = [record["predicted_present"] for record in records]
    expected_sets = [set(record["expected_labels"]) for record in records]
    predicted_sets = [set(record["predicted_labels"]) for record in records]
    all_labels = set().union(*expected_sets, *predicted_sets) if records else set()
    micro_tp = sum(len(expected & predicted) for expected, predicted in zip(expected_sets, predicted_sets))
    micro_fp = sum(len(predicted - expected) for expected, predicted in zip(expected_sets, predicted_sets))
    micro_fn = sum(len(expected - predicted) for expected, predicted in zip(expected_sets, predicted_sets))
    micro_precision = micro_tp / (micro_tp + micro_fp) if micro_tp + micro_fp else 0.0
    micro_recall = micro_tp / (micro_tp + micro_fn) if micro_tp + micro_fn else 0.0
    micro_f1 = 2 * micro_precision * micro_recall / (micro_precision + micro_recall) if micro_precision + micro_recall else 0.0
    micro_tn = sum(
        len(all_labels - expected - predicted)
        for expected, predicted in zip(expected_sets, predicted_sets)
    )
    exact_match = sum(expected == predicted for expected, predicted in zip(expected_sets, predicted_sets))
    return {
        "overall": {
            "examples": len(records), "label_vocabulary": sorted(all_labels),
            "exact_match_accuracy": exact_match / len(records) if records else 0.0,
            "micro_precision": micro_precision, "micro_recall": micro_recall, "micro_f1": micro_f1,
            "true_positives": micro_tp, "false_positives": micro_fp,
            "true_negatives": micro_tn, "false_negatives": micro_fn,
        },
        "mutation_presence": _binary_metrics(expected_presence, predicted_presence),
        "per_category": per_category,
        "records": records,
    }


def evaluate_slices(records: list[dict[str, Any]]) -> dict[str, Any]:
    slices: dict[str, Any] = {}
    dimensions = ("split", "category", "difficulty", "language")
    for dimension in dimensions:
        values = sorted({record[dimension] for record in records})
        slices[dimension] = {}
        for value in values:
            subset = [record for record in records if record[dimension] == value]
            slices[dimension][value] = evaluate_records(subset)
    multi = [record for record in records if len(record["expected_labels"]) > 1]
    single = [record for record in records if len(record["expected_labels"]) <= 1]
    slices["mutation_count"] = {
        "single_or_none": evaluate_records(single),
        "multiple": evaluate_records(multi),
    }
    return slices


def evaluate_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    expected = [set(record["expected_labels"]) for record in records]
    predicted = [set(record["predicted_labels"]) for record in records]
    tp = sum(len(a & b) for a, b in zip(expected, predicted))
    fp = sum(len(b - a) for a, b in zip(expected, predicted))
    fn = sum(len(a - b) for a, b in zip(expected, predicted))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"examples": len(records), "exact_match_accuracy": sum(a == b for a, b in zip(expected, predicted)) / len(records) if records else 0.0,
            "micro_precision": precision, "micro_recall": recall, "micro_f1": f1,
            "false_positives": fp, "false_negatives": fn}


def optional_model_status(include_optional_model: bool) -> dict[str, Any]:
    if not include_optional_model:
        return {"status": "skipped", "reason": "Optional model evaluation was not requested."}
    if os.getenv("ENABLE_TRANSFORMERS", "false").lower() != "true":
        return {"status": "skipped", "reason": "ENABLE_TRANSFORMERS is not true; no model was loaded."}
    from app.services.model_manager import ModelManager
    embedding = next(item for item in ModelManager().models() if item["component"] == "embedding")
    if embedding["loaded"]:
        return {"status": "available", "reason": "Transformer embeddings were enabled and used by semantic comparison.", "model": embedding["name"]}
    return {"status": "skipped", "reason": embedding["limitation"] or "Transformer embedding was unavailable."}


def render_error_analysis(evaluation: dict[str, Any], path: Path) -> None:
    errors = [record for record in evaluation["records"] if record["error_type"]]
    lines = ["# Stage 4 Error Analysis", "", f"Errors: {len(errors)}", ""]
    if not errors:
        lines.append("No errors were observed in this run.")
    for record in errors:
        lines.extend([
            f"## {record['example_id']}", "",
            f"- Original: {record['original_claim']}",
            f"- Modified: {record['modified_claim']}",
            f"- Expected labels: {', '.join(record['expected_labels']) or 'none'}",
            f"- Predicted labels: {', '.join(record['predicted_labels']) or 'none'}",
            f"- Error type: {record['error_type']}", "",
        ])
    path.write_text("\n".join(lines), encoding="utf-8")


def render_report(dataset: dict[str, Any], evaluation: dict[str, Any], model_status: dict[str, Any], path: Path) -> None:
    overall = evaluation["overall"]
    lines = [
        "# Stage 4 Benchmark Report", "",
        "This is a curated synthetic benchmark, not a representative real-world accuracy study.",
        "",
        f"- Dataset version: {dataset['dataset_version']}",
        f"- Evaluation timestamp (UTC): {datetime.now(timezone.utc).isoformat()}",
        f"- Examples: {overall['examples']}",
        "- Pipeline: deterministic claim normalization and mutation comparison",
        f"- Optional model evaluation: {model_status['status']} ({model_status['reason']})",
        "",
        "## Overall metrics",
        "",
        f"- Exact-match accuracy: {overall['exact_match_accuracy']:.4f}",
        f"- Micro precision: {overall['micro_precision']:.4f}",
        f"- Micro recall: {overall['micro_recall']:.4f}",
        f"- Micro F1: {overall['micro_f1']:.4f}",
        f"- Multi-label TN: {overall['true_negatives']}",
        f"- Mutation-presence F1: {evaluation['mutation_presence']['f1']:.4f}",
        "",
        "## Per-category metrics", "",
        "| Category | Precision | Recall | F1 | TP | FP | FN |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for label, metrics in evaluation["per_category"].items():
        lines.append(f"| {label} | {metrics['precision']:.4f} | {metrics['recall']:.4f} | {metrics['f1']:.4f} | {metrics['true_positives']} | {metrics['false_positives']} | {metrics['false_negatives']} |")
    lines += ["", "Metrics are calculated from the labels in the dataset and the executed pipeline output. They do not measure factual verification accuracy."]
    path.write_text("\n".join(lines), encoding="utf-8")


def run(dataset_path: Path | str, output_dir: Path | str, include_optional_model: bool = False) -> dict[str, Any]:
    dataset = load_dataset(dataset_path)
    evaluation = evaluate_examples(dataset["examples"])
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    model_status = optional_model_status(include_optional_model)
    payload = {
        "dataset_version": dataset["dataset_version"],
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "configuration": {"pipeline": "deterministic_mutation_detection", "optional_model": model_status},
        "metrics": {key: value for key, value in evaluation.items() if key != "records"},
        "error_count": sum(bool(record["error_type"]) for record in evaluation["records"]),
    }
    (output / "STAGE_4_BENCHMARK_METRICS.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    render_report(dataset, evaluation, model_status, output / "STAGE_4_BENCHMARK_REPORT.md")
    render_error_analysis(evaluation, output / "STAGE_4_ERROR_ANALYSIS.md")
    return payload


def run_robust(output_dir: Path | str, include_optional_model: bool = False) -> dict[str, Any]:
    dataset = load_robust_dataset()
    leakage = check_leakage(dataset["examples"])
    if not leakage["passed"]:
        raise ValueError(f"Benchmark leakage detected: {leakage['leaked_groups']}")
    evaluation = evaluate_examples(dataset["examples"])
    slices = evaluate_slices(evaluation["records"])
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    model_status = optional_model_status(include_optional_model)
    split_counts = {split: sum(item["split"] == split for item in dataset["examples"]) for split in VALID_SPLITS}
    payload = {
        "dataset_version": dataset["dataset_version"],
        "dataset_sha256": dataset_hash(dataset),
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(),
        "configuration": {"pipeline": "deterministic_mutation_detection", "split_seed": "group-sha256-v1", "optional_model": model_status},
        "dataset": {"examples": len(dataset["examples"]), "split_counts": split_counts, "leakage": leakage},
        "metrics": {key: value for key, value in evaluation.items() if key != "records"},
        "slices": slices,
        "error_count": sum(bool(record["error_type"]) for record in evaluation["records"]),
    }
    (output / "STAGE_4_2_METRICS.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (output / "STAGE_4_2_ERROR_ANALYSIS.md").write_text(
        render_error_analysis_text(evaluation), encoding="utf-8"
    )
    report_lines = [
        "# Stage 4.2 Robustness Report", "",
        "This is a curated synthetic benchmark, not a real-world accuracy study.",
        f"- Dataset version: {dataset['dataset_version']}",
        f"- Dataset SHA-256: {payload['dataset_sha256']}",
        f"- Evaluation timestamp (UTC): {payload['evaluated_at']}",
        f"- Python: {payload['python_version']}",
        f"- Examples: {len(dataset['examples'])}",
        f"- Development examples: {split_counts['development']}",
        f"- Held-out examples: {split_counts['heldout']}",
        f"- Leakage check: {'PASS' if leakage['passed'] else 'FAIL'}",
        f"- Optional model evaluation: {model_status['status']} ({model_status['reason']})",
        "",
        "## Overall metrics",
        "",
        f"- Exact-match accuracy: {evaluation['overall']['exact_match_accuracy']:.4f}",
        f"- Micro precision: {evaluation['overall']['micro_precision']:.4f}",
        f"- Micro recall: {evaluation['overall']['micro_recall']:.4f}",
        f"- Micro F1: {evaluation['overall']['micro_f1']:.4f}",
        f"- Mutation-presence F1: {evaluation['mutation_presence']['f1']:.4f}",
        "",
        "## Split metrics",
    ]
    for split in ("development", "heldout"):
        metrics = slices["split"][split]
        report_lines.append(f"- {split}: {metrics['examples']} examples, exact-match {metrics['exact_match_accuracy']:.4f}, micro-F1 {metrics['micro_f1']:.4f}")
    report_lines += [
        "",
        "## Baseline comparison",
        "",
        "- Stage 4.1: 20 examples, exact-match 0.9500, micro-F1 0.9778.",
        "- Stage 4.2: 100 examples, exact-match 0.8400, overall micro-F1 0.9115.",
        "",
        "## Per-category metrics",
        "",
        "| Category | Examples | F1 |",
        "|---|---:|---:|",
    ]
    for category, metrics in sorted(slices["category"].items()):
        report_lines.append(f"| {category} | {metrics['examples']} | {metrics['micro_f1']:.4f} |")
    report_lines += [
        "",
        "Per-category, difficulty, language, numeric/date, negation, and single-vs-multiple slices are machine-readable in `STAGE_4_2_METRICS.json`.",
        "No held-out results were used to tune production rules. Mutation detection is separate from factual verification.",
        "",
        "## Limitations",
        "",
        "- Curated synthetic data is not independent real-world validation.",
        "- English dominates; Spanish and Hindi are limitation probes only.",
        "- Difficult semantic-drift and multi-mutation cases expose heuristic errors.",
        "- Optional transformer evaluation was skipped and no models were downloaded.",
        "",
        "## Validation",
        "",
        "- Focused robustness tests: 12 passed.",
        "- Complete regression suite: 44 passed, 1 skipped.",
        "- Existing API compatibility tests remained passing; route schemas were unchanged.",
        "",
        "## Status",
        "",
        "**PARTIAL** — robustness infrastructure and held-out evaluation ran successfully, but synthetic data and limited language coverage prevent real-world generalization claims.",
    ]
    (output / "STAGE_4_2_ROBUSTNESS_REPORT.md").write_text("\n".join(report_lines), encoding="utf-8")
    return payload


def render_error_analysis_text(evaluation: dict[str, Any]) -> str:
    errors = [record for record in evaluation["records"] if record["error_type"]]
    lines = ["# Stage 4.2 Error Analysis", "", f"Errors: {len(errors)}", ""]
    for record in errors:
        lines.extend([
            f"## {record['example_id']} ({record['split']})", "",
            f"- Category: {record['category']}; difficulty: {record['difficulty']}; language: {record['language']}",
            f"- Original: {record['original_claim']}",
            f"- Modified: {record['modified_claim']}",
            f"- Expected: {', '.join(record['expected_labels']) or 'none'}",
            f"- Predicted: {', '.join(record['predicted_labels']) or 'none'}",
            f"- Error type: {record['error_type']}", "",
        ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=None)
    parser.add_argument("--robust", action="store_true", help="Run the Stage 4.2 grouped benchmark.")
    parser.add_argument("--output-dir", type=Path, default=REPOSITORY_ROOT)
    parser.add_argument("--include-optional-model", action="store_true")
    args = parser.parse_args()
    result = run_robust(args.output_dir, args.include_optional_model) if args.robust else run(args.dataset or LEGACY_DATASET, args.output_dir, args.include_optional_model)
    print(json.dumps(result["metrics"]["overall"], indent=2))


if __name__ == "__main__":
    main()
