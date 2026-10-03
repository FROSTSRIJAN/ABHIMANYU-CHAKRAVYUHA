import json
from pathlib import Path

import pytest

from training.dataset import load_dataset, manifest, validate_examples


DATASET = Path(__file__).parents[1] / "training" / "stage_6_2_dataset.json"


def test_stage_62_dataset_validates_and_has_grouped_splits():
    payload = load_dataset(DATASET)
    summary = manifest(payload)
    assert summary["group_leakage_check"] == "passed"
    assert summary["counts"]["total"] == 16
    assert set(summary["counts"]["splits"]) == {"train", "validation", "test"}


def test_stage_62_rejects_group_leakage():
    payload = load_dataset(DATASET)
    examples = [dict(item) for item in payload["examples"]]
    examples[0]["group_id"] = examples[1]["group_id"]
    with pytest.raises(ValueError, match="Group leakage"):
        validate_examples(examples)


def test_stage_62_manifest_is_reproducible():
    payload = load_dataset(DATASET)
    first = manifest(payload)
    second = manifest(json.loads(DATASET.read_text(encoding="utf-8")))
    assert first == second
