"""Sinh cache đã tiền xử lý: 498 bệnh nhân × ``[8, 96, 96, 48]``.

    python -m src.preprocess.build_cache --config configs/preprocess.yaml

Với mỗi bệnh nhân:
1. lấy bbox ở pha tham chiếu → tâm tổn thương trong toạ độ mm;
2. dựng **một** lưới đích quanh tâm đó (hướng lấy từ pha tham chiếu);
3. lấy mẫu cả 8 pha lên lưới đó — đây đồng thời là bước **căn chỉnh**;
4. chuẩn hoá từng pha (thống kê per-sample, không leakage);
5. ghi 1 file ``.npz`` cho mỗi bệnh nhân.

**Resume được**: bệnh nhân đã có file output thì bỏ qua. Bắt buộc, vì Kaggle session
≤12h và có thể bị ngắt bất cứ lúc nào (AGENTS.md §7).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path
from typing import Any

import numpy as np

from src.data.annotation import Annotation
from src.data.images import scan_image_index
from src.preprocess.geometry import AXIS_ORDERS, bbox_center_voxel, voxel_to_world
from src.preprocess.grid import make_reference_image
from src.preprocess.normalize import clip_and_zscore
from src.preprocess.resample import read_image, resample_to_grid, to_numpy
from src.utils.io import load_yaml, resolve_data_root
from src.utils.logging import CsvLogger, get_logger

logger = get_logger(__name__)


def resolve_cache_dir(config: dict[str, Any]) -> Path:
    """Thư mục cache: env ``LLDMMRI_CACHE_DIR`` thắng, sau đó config."""
    import os

    return Path(os.environ.get("LLDMMRI_CACHE_DIR") or config["cache_dir"])


def _git_commit() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=10
        )
        return out.stdout.strip() or "unknown"
    except Exception:  # noqa: BLE001 — chỉ là metadata, không được làm hỏng build
        return "unknown"


def process_patient(
    patient_id: str,
    annotation: Annotation,
    image_index: dict,
    phase_config: list[dict[str, str]],
    config: dict[str, Any],
) -> np.ndarray:
    """Trả về khối ``[8, X, Y, Z]`` đã resample + chuẩn hoá cho một bệnh nhân."""
    from src.utils.ids import normalize_pid

    axis_order = config["axis_order"]
    ref_phase = config["reference_phase"]
    spacing = tuple(config["target_spacing"])
    size = tuple(config["target_size"])
    interpolator = config.get("interpolator", "linear")
    norm_cfg = config.get("normalize") or {}
    clip = tuple(norm_cfg.get("clip_percentile", (0.5, 99.5)))
    scope = norm_cfg.get("scope", "volume")

    key = normalize_pid(patient_id)
    ref_token = next(p["file"] for p in phase_config if p["name"] == ref_phase)
    ref_path = image_index.get((key, ref_token))
    if ref_path is None:
        raise FileNotFoundError(f"{patient_id}: thiếu pha tham chiếu {ref_phase}")

    # Tâm tổn thương trong mm + hướng lưới, đều lấy từ pha tham chiếu.
    ref_image = read_image(ref_path)
    affine_direction = np.array(ref_image.GetDirection(), dtype=float).reshape(3, 3)
    ref_affine = np.eye(4)
    ref_affine[:3, :3] = affine_direction @ np.diag(ref_image.GetSpacing())
    ref_affine[:3, 3] = ref_image.GetOrigin()

    box = annotation.bbox3d(patient_id, ref_phase)
    center_world = voxel_to_world(ref_affine, bbox_center_voxel(box, axis_order))
    reference = make_reference_image(center_world, affine_direction, spacing, size)

    channels: list[np.ndarray] = []
    for phase in phase_config:
        path = image_index.get((key, phase["file"]))
        if path is None:
            raise FileNotFoundError(f"{patient_id}: thiếu pha {phase['file']}")
        image = read_image(path) if path != ref_path else ref_image
        patch = to_numpy(resample_to_grid(image, reference, interpolator))
        stats_source = to_numpy(image) if scope == "volume" else None
        channels.append(clip_and_zscore(patch, stats_source, clip))

    return np.stack(channels, axis=0)


def build_cache(config_path: str | Path, limit: int = 0) -> Path:
    """Chạy toàn bộ pipeline; trả về thư mục cache."""
    repo = Path(__file__).resolve().parents[2]
    config = load_yaml(config_path)

    axis_order = config.get("axis_order")
    if axis_order not in AXIS_ORDERS:
        raise SystemExit(
            f"axis_order trong {config_path} đang là {axis_order!r}. "
            f"Phải điền {AXIS_ORDERS} — chạy scripts/kaggle_geometry_report.py để có phán quyết. "
            "KHÔNG đoán: crop sai trục thì mọi kết quả sau đều vô nghĩa."
        )

    data_config = load_yaml(repo / "configs" / "data.yaml")
    data_root = resolve_data_root(data_config)
    phase_config = data_config["phases"]

    annotation = Annotation(data_root / data_config["annotation_rel"])
    image_index = scan_image_index(
        data_root / data_config["images_rel"], data_config["image_suffixes"]
    )

    cache_dir = resolve_cache_dir(config)
    cache_dir.mkdir(parents=True, exist_ok=True)
    dtype = np.dtype(config.get("output_dtype", "float16"))

    patient_ids = annotation.patient_ids()
    if limit:
        patient_ids = patient_ids[:limit]

    (cache_dir / "cache_meta.json").write_text(
        json.dumps(
            {
                "axis_order": axis_order,
                "reference_phase": config["reference_phase"],
                "target_spacing": config["target_spacing"],
                "target_size": config["target_size"],
                "interpolator": config.get("interpolator", "linear"),
                "normalize": config.get("normalize"),
                "n4": config.get("n4", False),
                "output_dtype": str(dtype),
                "phases": [p["name"] for p in phase_config],
                "git_commit": _git_commit(),
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    log = CsvLogger(cache_dir / "build_log.csv", ["patient_id", "status", "seconds", "note"])
    n_done = n_skip = n_fail = 0
    started = time.time()

    for i, pid in enumerate(patient_ids, 1):
        out_path = cache_dir / f"{pid}.npz"
        if out_path.exists():  # resume: Kaggle có thể ngắt session bất cứ lúc nào
            n_skip += 1
            continue

        t0 = time.time()
        try:
            volume = process_patient(pid, annotation, image_index, phase_config, config)
            # Tên tạm phải kết thúc bằng .npz: np.savez_compressed tự nối thêm ".npz"
            # vào tên không có đuôi đó, khiến file thật nằm ở chỗ khác.
            tmp_path = out_path.with_name(f"{out_path.stem}.tmp.npz")
            np.savez_compressed(
                tmp_path,
                image=volume.astype(dtype),
                label=np.int64(annotation.category_of(pid)),
            )
            tmp_path.replace(out_path)  # ghi nguyên tử: không để lại file dở
            n_done += 1
            log.log(
                {
                    "patient_id": pid,
                    "status": "ok",
                    "seconds": round(time.time() - t0, 2),
                    "note": "",
                }
            )
        except Exception as exc:  # noqa: BLE001 — một ca hỏng không được dừng cả mẻ
            n_fail += 1
            log.log(
                {
                    "patient_id": pid,
                    "status": "fail",
                    "seconds": round(time.time() - t0, 2),
                    "note": str(exc)[:200],
                }
            )
            logger.warning("%s: %s", pid, exc)

        if i % 25 == 0:
            logger.info(
                "%d/%d | xong %d, bỏ qua %d, lỗi %d | %.1f phút",
                i,
                len(patient_ids),
                n_done,
                n_skip,
                n_fail,
                (time.time() - started) / 60,
            )

    log.close()
    logger.info(
        "HOÀN TẤT: xong %d, bỏ qua %d (đã có sẵn), lỗi %d -> %s",
        n_done,
        n_skip,
        n_fail,
        cache_dir,
    )
    if n_fail:
        logger.warning("Có %d ca lỗi — xem %s", n_fail, cache_dir / "build_log.csv")
    return cache_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Build preprocessed cache for LLD-MMRI")
    parser.add_argument("--config", default="configs/preprocess.yaml")
    parser.add_argument("--limit", type=int, default=0, help="so benh nhan; 0 = tat ca")
    args = parser.parse_args()
    build_cache(args.config, args.limit)


if __name__ == "__main__":
    main()
