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
from src.preprocess.crop import adaptive_spacing, bbox_extent_voxel, mask_center_extent_voxel
from src.preprocess.geometry import AXIS_ORDERS, bbox_center_voxel, voxel_to_world
from src.preprocess.grid import make_reference_image
from src.preprocess.normalize import clip_and_zscore
from src.preprocess.resample import read_image, resample_to_grid, to_numpy
from src.utils.io import load_yaml, resolve_cache_dir, resolve_data_root
from src.utils.logging import CsvLogger, get_logger

logger = get_logger(__name__)

CROP_MODES = ("fixed_mm", "lesion_tight")
LESION_SOURCES = ("bbox", "mask")

__all__ = [
    "build_cache",
    "process_patient",
    "process_patient_with_meta",
    "resolve_cache_dir",
]


def _git_commit() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=10
        )
        return out.stdout.strip() or "unknown"
    except Exception:  # noqa: BLE001 — chỉ là metadata, không được làm hỏng build
        return "unknown"


def _lesion_center_extent(
    patient_id: str,
    annotation: Annotation,
    ref_phase: str,
    axis_order: str,
    ref_image,
    mask_path: Path | None,
) -> tuple[np.ndarray, np.ndarray, str]:
    """Tâm và kích thước tổn thương theo voxel của pha tham chiếu.

    Ưu tiên mask nếu có; rơi về bbox của annotation khi không có mask hoặc mask
    rỗng. Trả về thêm nguồn thực sự đã dùng để `build_cache` ghi lại — cần biết
    ca nào rơi về bbox, không được im lặng.
    """
    if mask_path is not None:
        try:
            center, extent = mask_center_extent_voxel(to_numpy(read_image(mask_path)))
            return center, extent, "mask"
        except (ValueError, RuntimeError) as exc:
            logger.warning("%s: mask không dùng được (%s), rơi về bbox", patient_id, exc)

    box = annotation.bbox3d(patient_id, ref_phase)
    return bbox_center_voxel(box, axis_order), bbox_extent_voxel(box, axis_order), "bbox"


def process_patient_with_meta(
    patient_id: str,
    annotation: Annotation,
    image_index: dict,
    phase_config: list[dict[str, str]],
    config: dict[str, Any],
    mask_index: dict | None = None,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Khối ``[8, X, Y, Z]`` kèm metadata hình học của cửa sổ cắt.

    Metadata gồm `lesion_extent_mm`, `fov_mm`, `spacing`, `crop_source` — giữ lại
    kích thước tuyệt đối của tổn thương, thứ mà chế độ `lesion_tight` cắt bỏ khỏi
    ảnh (xem `src/preprocess/crop.py`).
    """
    from src.utils.ids import normalize_pid

    axis_order = config["axis_order"]
    ref_phase = config["reference_phase"]
    size = tuple(config["target_size"])
    interpolator = config.get("interpolator", "linear")
    norm_cfg = config.get("normalize") or {}
    clip = tuple(norm_cfg.get("clip_percentile", (0.5, 99.5)))
    scope = norm_cfg.get("scope", "volume")

    crop_mode = config.get("crop_mode", "fixed_mm")
    if crop_mode not in CROP_MODES:
        raise ValueError(f"crop_mode phải thuộc {CROP_MODES}, nhận {crop_mode!r}")

    key = normalize_pid(patient_id)
    ref_token = next(p["file"] for p in phase_config if p["name"] == ref_phase)
    ref_path = image_index.get((key, ref_token))
    if ref_path is None:
        raise FileNotFoundError(f"{patient_id}: thiếu pha tham chiếu {ref_phase}")

    # Tâm tổn thương trong mm + hướng lưới, đều lấy từ pha tham chiếu.
    ref_image = read_image(ref_path)
    affine_direction = np.array(ref_image.GetDirection(), dtype=float).reshape(3, 3)
    ref_spacing = np.array(ref_image.GetSpacing(), dtype=float)
    ref_affine = np.eye(4)
    ref_affine[:3, :3] = affine_direction @ np.diag(ref_spacing)
    ref_affine[:3, 3] = ref_image.GetOrigin()

    lesion_cfg = config.get("lesion_tight") or {}
    source = lesion_cfg.get("source", "bbox")
    if source not in LESION_SOURCES:
        raise ValueError(f"lesion_tight.source phải thuộc {LESION_SOURCES}, nhận {source!r}")

    mask_path = None
    if crop_mode == "lesion_tight" and source == "mask" and mask_index is not None:
        mask_path = mask_index.get((key, ref_token))
        if mask_path is None:
            logger.warning("%s: không có mask cho pha %s, rơi về bbox", patient_id, ref_phase)

    center_voxel, extent_voxel, crop_source = _lesion_center_extent(
        patient_id, annotation, ref_phase, axis_order, ref_image, mask_path
    )
    extent_mm = extent_voxel * ref_spacing

    if crop_mode == "lesion_tight":
        spacing, fov_mm = adaptive_spacing(
            extent_mm,
            size,
            margin_factor=float(lesion_cfg.get("margin_factor", 1.6)),
            min_fov_mm=tuple(lesion_cfg.get("min_fov_mm", (40.0, 40.0, 40.0))),
            max_fov_mm=tuple(lesion_cfg.get("max_fov_mm", (200.0, 200.0, 200.0))),
        )
    else:
        spacing = tuple(config["target_spacing"])
        fov_mm = np.asarray(spacing, dtype=float) * np.asarray(size, dtype=float)
        crop_source = "bbox"

    center_world = voxel_to_world(ref_affine, center_voxel)
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

    meta = {
        "lesion_extent_mm": extent_mm.astype(np.float32),
        "fov_mm": np.asarray(fov_mm, dtype=np.float32),
        "spacing": np.asarray(spacing, dtype=np.float32),
        "crop_source": crop_source,
        "crop_mode": crop_mode,
    }
    return np.stack(channels, axis=0), meta


def process_patient(
    patient_id: str,
    annotation: Annotation,
    image_index: dict,
    phase_config: list[dict[str, str]],
    config: dict[str, Any],
    mask_index: dict | None = None,
) -> np.ndarray:
    """Trả về khối ``[8, X, Y, Z]`` đã resample + chuẩn hoá cho một bệnh nhân."""
    volume, _ = process_patient_with_meta(
        patient_id, annotation, image_index, phase_config, config, mask_index
    )
    return volume


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

    crop_mode = config.get("crop_mode", "fixed_mm")
    lesion_cfg = config.get("lesion_tight") or {}
    mask_index: dict | None = None
    if crop_mode == "lesion_tight" and lesion_cfg.get("source") == "mask":
        labels_rel = data_config.get("labels_rel")
        if not labels_rel:
            raise SystemExit(
                "lesion_tight.source = 'mask' nhưng configs/data.yaml chưa có 'labels_rel'. "
                "Thêm đường dẫn thư mục mask, hoặc đổi source sang 'bbox'."
            )
        labels_dir = data_root / labels_rel
        if not labels_dir.is_dir():
            raise SystemExit(f"Không thấy thư mục mask: {labels_dir}")
        mask_index = scan_image_index(labels_dir, data_config["image_suffixes"])
        logger.info("Đã quét %d file mask ở %s", len(mask_index), labels_dir)

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
                "crop_mode": crop_mode,
                "lesion_tight": lesion_cfg if crop_mode == "lesion_tight" else None,
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

    log = CsvLogger(
        cache_dir / "build_log.csv",
        ["patient_id", "status", "seconds", "crop_source", "fov_mm", "note"],
    )
    n_done = n_skip = n_fail = n_bbox_fallback = 0
    started = time.time()

    for i, pid in enumerate(patient_ids, 1):
        out_path = cache_dir / f"{pid}.npz"
        if out_path.exists():  # resume: Kaggle có thể ngắt session bất cứ lúc nào
            n_skip += 1
            continue

        t0 = time.time()
        try:
            volume, meta = process_patient_with_meta(
                pid, annotation, image_index, phase_config, config, mask_index
            )
            # Tên tạm phải kết thúc bằng .npz: np.savez_compressed tự nối thêm ".npz"
            # vào tên không có đuôi đó, khiến file thật nằm ở chỗ khác.
            tmp_path = out_path.with_name(f"{out_path.stem}.tmp.npz")
            np.savez_compressed(
                tmp_path,
                image=volume.astype(dtype),
                label=np.int64(annotation.category_of(pid)),
                lesion_extent_mm=meta["lesion_extent_mm"],
                fov_mm=meta["fov_mm"],
                spacing=meta["spacing"],
                crop_source=np.str_(meta["crop_source"]),
            )
            tmp_path.replace(out_path)  # ghi nguyên tử: không để lại file dở
            n_done += 1
            n_bbox_fallback += meta["crop_source"] == "bbox" and crop_mode == "lesion_tight"
            log.log(
                {
                    "patient_id": pid,
                    "status": "ok",
                    "seconds": round(time.time() - t0, 2),
                    "crop_source": meta["crop_source"],
                    "fov_mm": " ".join(f"{v:.1f}" for v in meta["fov_mm"]),
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
                    "crop_source": "",
                    "fov_mm": "",
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
    if n_bbox_fallback:
        logger.warning(
            "%d ca phải rơi về bbox vì mask thiếu hoặc rỗng — cột crop_source trong %s",
            n_bbox_fallback,
            cache_dir / "build_log.csv",
        )
    return cache_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Build preprocessed cache for LLD-MMRI")
    parser.add_argument("--config", default="configs/preprocess.yaml")
    parser.add_argument("--limit", type=int, default=0, help="so benh nhan; 0 = tat ca")
    args = parser.parse_args()
    build_cache(args.config, args.limit)


if __name__ == "__main__":
    main()
