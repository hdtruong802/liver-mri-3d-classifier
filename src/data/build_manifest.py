"""Sinh `data/manifest.csv`: patient_id, class, thiếu pha, split.

Thuần Python + stdlib csv (không phụ thuộc pandas) để chạy được ở bước sớm nhất,
trước khi cài deep-learning stack. Chạy:

    python -m src.data.build_manifest --config configs/data.yaml
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from src.data.annotation import Annotation
from src.data.images import scan_image_index
from src.data.splits import Splits
from src.data.taxonomy import CLASS_NAMES
from src.utils.ids import normalize_pid
from src.utils.io import load_yaml, resolve_data_root
from src.utils.logging import get_logger

logger = get_logger(__name__)


def _split_label(key: str, splits: Splits) -> str:
    if key in splits.test_keys():
        return "test"
    if key in splits.trainval_keys():
        return "trainval"
    return "unknown"  # không nên xảy ra nếu splits.validate() đã pass


def build_manifest(config_path: str | Path) -> Path:
    config = load_yaml(config_path)
    data_root = resolve_data_root(config)
    annotation_path = data_root / config["annotation_rel"]
    images_dir = data_root / config["images_rel"]
    phase_tokens = [p["file"] for p in config["phases"]]
    phase_names = [p["name"] for p in config["phases"]]

    ann = Annotation(annotation_path)
    splits = Splits(config["splits_dir"])
    splits.validate()
    index = scan_image_index(images_dir, config.get("image_suffix", "_0000.nii.gz"))

    out_path = Path("data/manifest.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    n_missing_any = 0
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "patient_id",
                "class_index",
                "class_name",
                "split",
                "n_phases_present",
                "missing_phases",
            ]
        )
        for pid in ann.patient_ids():
            key = normalize_pid(pid)
            cls = ann.category_of(pid)
            present = [tok for tok in phase_tokens if (key, tok) in index]
            missing = [tok for tok in phase_tokens if tok not in present]
            if missing:
                n_missing_any += 1
            writer.writerow(
                [
                    pid,
                    cls,
                    CLASS_NAMES[cls],
                    _split_label(key, splits),
                    len(present),
                    ";".join(missing),
                ]
            )

    logger.info("manifest: %d bệnh nhân, %d thiếu >=1 pha -> %s", len(ann), n_missing_any, out_path)
    assert len(phase_names) == 8, "config phases phải đúng 8 thì"
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/data.yaml")
    args = parser.parse_args()
    build_manifest(args.config)


if __name__ == "__main__":
    main()
