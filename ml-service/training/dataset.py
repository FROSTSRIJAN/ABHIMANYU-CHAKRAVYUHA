"""Dataset validation and grouped split utilities for Stage 6.2."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Iterable

REQUIRED_FIELDS = {
    "example_id",
    "group_id",
    "original_claim",
    "modified_claim",
    "language_pair",
    "alignment_label",
    "mutation_labels",
    "abstention",
    "split",
    "data_origin",
    "review_status",
}
ALIGNMENT_LABELS = {"ALIGNED", "RELATED_BUT_UNALIGNED", "DISTINCT", "ABSTAIN"}
SPLITS = {"train", "validation", "test"}


def load_dataset(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    examples = payload.get("examples")
    if not isinstance(examples, list) or not examples:
        raise ValueError("Dataset must contain a non-empty examples list.")
    validate_examples(examples)
    return payload


def validate_examples(examples: Iterable[dict]) -> None:
    seen: set[str] = set()
    groups: dict[str, set[str]] = {}
    for item in examples:
        missing = REQUIRED_FIELDS - item.keys()
        if missing:
            raise ValueError(f"{item.get('example_id', '<unknown>')} missing fields: {sorted(missing)}")
        if item["example_id"] in seen:
            raise ValueError(f"Duplicate example_id: {item['example_id']}")
        seen.add(item["example_id"])
        if item["split"] not in SPLITS:
            raise ValueError(f"Invalid split: {item['split']}")
        if item["alignment_label"] not in ALIGNMENT_LABELS:
            raise ValueError(f"Invalid alignment label: {item['alignment_label']}")
        if not isinstance(item["mutation_labels"], list):
            raise ValueError(f"mutation_labels must be a list: {item['example_id']}")
        if not isinstance(item["abstention"], bool):
            raise ValueError(f"abstention must be boolean: {item['example_id']}")
        groups.setdefault(item["group_id"], set()).add(item["split"])
    leaked = sorted(group for group, splits in groups.items() if len(splits) > 1)
    if leaked:
        raise ValueError(f"Group leakage detected: {leaked}")


def dataset_hash(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(canonical).hexdigest()


def manifest(payload: dict) -> dict:
    examples = payload["examples"]
    return {
        "dataset_version": payload.get("dataset_version", "unknown"),
        "dataset_hash": dataset_hash(payload),
        "synthetic": payload.get("synthetic", True),
        "human_reviewed_examples": sum(item["review_status"] == "human_reviewed" for item in examples),
        "counts": {
            "total": len(examples),
            "splits": dict(Counter(item["split"] for item in examples)),
            "language_pairs": dict(Counter(item["language_pair"] for item in examples)),
            "alignment_labels": dict(Counter(item["alignment_label"] for item in examples)),
        },
        "group_leakage_check": "passed",
    }
