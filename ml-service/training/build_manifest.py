"""Build a reproducible manifest for the Stage 6.2 dataset."""

from pathlib import Path
import json

from dataset import load_dataset, manifest

ROOT = Path(__file__).resolve().parent
payload = load_dataset(ROOT / "stage_6_2_dataset.json")
(ROOT / "stage_6_2_dataset_manifest.json").write_text(
    json.dumps(manifest(payload), indent=2, ensure_ascii=False) + "\n",
    encoding="utf-8",
)
print(json.dumps(manifest(payload), indent=2))
