import json
from pathlib import Path

import pytest

from benchmarks.runner import (
    _binary_metrics,
    check_leakage,
    dataset_hash,
    evaluate_examples,
    load_dataset,
    load_robust_dataset,
    run,
    run_robust,
)


DATASET = Path(__file__).parents[1] / "benchmarks" / "dataset.json"


def test_dataset_schema_and_unique_ids():
    dataset = load_dataset(DATASET)
    assert dataset["dataset_version"]
    assert len(dataset["examples"]) >= 13
    assert len({item["example_id"] for item in dataset["examples"]}) == len(dataset["examples"])


def test_binary_metrics_handles_empty_predictions():
    metrics = _binary_metrics([True, False], [False, False])
    assert metrics["true_positives"] == 0
    assert metrics["false_negatives"] == 1
    assert metrics["precision"] == 0


def test_multilabel_evaluation_reports_category_and_presence_metrics():
    evaluation = evaluate_examples(load_dataset(DATASET)["examples"])
    assert evaluation["overall"]["examples"] >= 13
    assert "NUMERICAL_MUTATION" in evaluation["per_category"]
    assert "mutation_presence" in evaluation


def test_error_records_identify_category_mismatch():
    examples = [{
        "example_id": "test-error",
        "original_claim": "The company may launch a product.",
        "modified_claim": "The company will launch a product.",
        "expected_mutation_labels": ["ENTITY_MUTATION"],
        "expected_mutation_present": True,
        "explanation": "Synthetic mismatch.",
        "language": "en",
        "split": "test",
        "category": "test",
    }]
    evaluation = evaluate_examples(examples)
    assert evaluation["records"][0]["error_type"] == "incorrect_categories"


def test_optional_model_evaluation_is_skipped_without_opt_in(monkeypatch):
    monkeypatch.delenv("ENABLE_TRANSFORMERS", raising=False)
    output = run(DATASET, Path("stage4-test-output"))
    try:
        config = output["configuration"]["optional_model"]
        assert config["status"] == "skipped"
    finally:
        for path in Path("stage4-test-output").glob("*"):
            path.unlink()
        Path("stage4-test-output").rmdir()


def test_benchmark_outputs_are_machine_readable_and_reproducible_shape(tmp_path):
    first = run(DATASET, tmp_path / "first")
    second = run(DATASET, tmp_path / "second")
    assert first["dataset_version"] == second["dataset_version"]
    first_metrics = json.loads((tmp_path / "first" / "STAGE_4_BENCHMARK_METRICS.json").read_text())
    assert first_metrics["metrics"]["overall"]["examples"] == len(load_dataset(DATASET)["examples"])


def test_robust_dataset_has_at_least_100_examples_and_required_metadata():
    dataset = load_robust_dataset()
    assert len(dataset["examples"]) >= 100
    required = {"example_id", "difficulty", "category", "language", "group", "split"}
    assert all(required.issubset(example) for example in dataset["examples"])


def test_robust_dataset_has_no_group_leakage_and_stable_hash():
    first = load_robust_dataset()
    second = load_robust_dataset()
    assert check_leakage(first["examples"])["passed"]
    assert dataset_hash(first) == dataset_hash(second)


def test_invalid_split_and_duplicate_ids_are_rejected():
    invalid = {
        "dataset_version": "test",
        "examples": [{
            "example_id": "dup", "original_claim": "A.", "modified_claim": "B.",
            "expected_mutation_labels": [], "expected_mutation_present": False,
            "explanation": "x", "language": "en", "difficulty": "simple",
            "category": "no_meaningful_mutation", "split": "development",
        }, {
            "example_id": "dup", "original_claim": "C.", "modified_claim": "D.",
            "expected_mutation_labels": [], "expected_mutation_present": False,
            "explanation": "x", "language": "en", "difficulty": "simple",
            "category": "no_meaningful_mutation", "split": "development",
        }],
    }
    path = Path("invalid-stage4-2.json")
    path.write_text(json.dumps(invalid), encoding="utf-8")
    try:
        with pytest.raises(ValueError):
            load_dataset(path)
    finally:
        path.unlink()


def test_missing_labels_are_rejected():
    invalid = {
        "dataset_version": "test",
        "examples": [{
            "example_id": "missing-labels", "original_claim": "A.", "modified_claim": "B.",
            "expected_mutation_present": False, "explanation": "x", "language": "en",
            "difficulty": "simple", "category": "no_meaningful_mutation",
            "split": "development",
        }],
    }
    path = Path("missing-labels-stage4-2.json")
    path.write_text(json.dumps(invalid), encoding="utf-8")
    try:
        with pytest.raises(ValueError):
            load_dataset(path)
    finally:
        path.unlink()


def test_empty_slice_metrics_are_zero_safe():
    from benchmarks.runner import evaluate_records
    assert evaluate_records([])["micro_f1"] == 0.0


def test_robust_run_writes_split_and_error_reports(tmp_path):
    result = run_robust(tmp_path)
    assert result["dataset"]["examples"] >= 100
    assert result["dataset"]["leakage"]["passed"]
    assert (tmp_path / "STAGE_4_2_METRICS.json").exists()
    assert (tmp_path / "STAGE_4_2_ERROR_ANALYSIS.md").exists()
