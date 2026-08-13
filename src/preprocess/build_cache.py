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
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np

from src.data.annotation import Annotation
from src.data.images import DEFAULT_LABEL_SUFFIXES, scan_image_index
from src.preprocess.crop import adaptive_spacing, bbox_extent_voxel, mask_center_extent_voxel
from src.preprocess.geometry import AXIS_ORDERS, bbox_center_voxel, voxel_to_world
from src.preprocess.grid import make_reference_image
from src.preprocess.normalize import clip_and_zscore
from src.preprocess.resample import read_image, resample_to_grid, to_numpy
from src.utils.io import load_yaml, resolve_cache_dir, resolve_data_root
from src.utils.logging import CsvLogger, get_logger

logger = get_logger(__name__)

CROP_MODES = ("fixed_mm", "lesion_tight")
# reference: một lưới duy nhất, tâm tại tổn thương của pha tham chiếu (v0).
# per_phase: mỗi pha một lưới, tâm tại tổn thương của CHÍNH pha đó (E4).
ALIGN_MODES = ("reference", "per_phase")
LESION_SOURCES = ("bbox", "mask")

__all__ = [
    "build_cache",
    "process_uploaded_with_masks",
    "process_patient",
    "process_patient_with_meta",
    "resample_annotation_masks",
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


def _phase_center_world(
    patient_id: str,
    phase_name: str,
    phase_token: str,
    image,
    annotation: Annotation,
    mask_index: dict | None,
    key: str,
    axis_order: str,
    fallback_world: np.ndarray,
) -> tuple[np.ndarray, str]:
    """Tâm tổn thương của **riêng một pha**, trong toạ độ mm.

    Đây là lõi của chế độ `align_phases: per_phase`. Mỗi pha có bbox riêng trong
    annotation (đó chính là cách WORKLOG S-031 đo được độ tán giữa các pha), nên
    căn theo tịnh tiến không cần thuật toán registration nào — chỉ cần dùng đúng
    con số đã có sẵn.

    Thứ tự ưu tiên: mask của pha đó → bbox của pha đó → tâm của pha tham chiếu.
    Rơi về `fallback_world` được ghi lại chứ không im lặng: một pha không căn được
    nghĩa là kênh đó vẫn lệch, và người đọc kết quả cần biết.
    """
    affine = np.eye(4)
    direction = np.array(image.GetDirection(), dtype=float).reshape(3, 3)
    affine[:3, :3] = direction @ np.diag(np.array(image.GetSpacing(), dtype=float))
    affine[:3, 3] = image.GetOrigin()

    if mask_index is not None:
        mask_path = mask_index.get((key, phase_token))
        if mask_path is not None:
            try:
                center, _ = mask_center_extent_voxel(to_numpy(read_image(mask_path)))
                return voxel_to_world(affine, center), "mask"
            except (ValueError, RuntimeError) as exc:
                logger.warning("%s/%s: mask không dùng được (%s)", patient_id, phase_name, exc)

    try:
        box = annotation.bbox3d(patient_id, phase_name)
        return voxel_to_world(affine, bbox_center_voxel(box, axis_order)), "bbox"
    except (KeyError, ValueError) as exc:
        logger.warning(
            "%s/%s: không có bbox riêng (%s), dùng tâm của pha tham chiếu",
            patient_id,
            phase_name,
            exc,
        )
        return fallback_world, "fallback_ref"


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

    align = config.get("align_phases", "reference")
    if align not in ALIGN_MODES:
        raise ValueError(f"align_phases phải thuộc {ALIGN_MODES}, nhận {align!r}")

    # Lề dư: lưới cache rộng hơn kích thước model nhận, để lúc train cắt ngẫu nhiên
    # được mà KHÔNG phải đệm 0 (`src/data/transforms.py::RandomCrop3D`).
    #
    # `spacing` đã tính từ `size` (kích thước TRONG), không từ `grid_size`, nên độ
    # phân giải vật lý giữ nguyên và phần thêm ra là mô thật ở rìa chứ không phải
    # cùng một khối bị kéo giãn. Hệ quả quan trọng: **cắt giữa `size` từ cache có
    # lề cho ra đúng khối mà cache không lề tạo ra** — nhờ vậy val của hai cache so
    # trực tiếp được, và phép so chỉ khác đúng một biến là augmentation lúc train.
    margin = tuple(int(m) for m in (config.get("crop_margin_voxels") or (0, 0, 0)))
    if len(margin) != 3 or any(m < 0 for m in margin):
        raise ValueError(f"crop_margin_voxels phải là 3 số không âm, nhận {margin!r}")
    grid_size = tuple(s + 2 * m for s, m in zip(size, margin, strict=True))

    center_world = voxel_to_world(ref_affine, center_voxel)
    reference = make_reference_image(center_world, affine_direction, spacing, grid_size)

    channels: list[np.ndarray] = []
    shifts: list[np.ndarray] = []
    center_sources: list[str] = []
    for phase in phase_config:
        path = image_index.get((key, phase["file"]))
        if path is None:
            raise FileNotFoundError(f"{patient_id}: thiếu pha {phase['file']}")
        image = read_image(path) if path != ref_path else ref_image

        if align == "per_phase" and phase["name"] != ref_phase:
            # Hướng và spacing GIỮ NGUYÊN của pha tham chiếu, chỉ đổi tâm. Nhờ vậy
            # cả 8 khối cắt có cùng kích thước vật lý và cùng hướng, tổn thương
            # hiện ở cùng một tỉ lệ — khác biệt duy nhất là phép tịnh tiến.
            phase_center, center_source = _phase_center_world(
                patient_id,
                phase["name"],
                phase["file"],
                image,
                annotation,
                mask_index,
                key,
                axis_order,
                center_world,
            )
            grid = make_reference_image(phase_center, affine_direction, spacing, grid_size)
        else:
            phase_center, center_source, grid = center_world, crop_source, reference

        shifts.append(np.asarray(phase_center, dtype=float) - center_world)
        center_sources.append(center_source)
        patch = to_numpy(resample_to_grid(image, grid, interpolator))
        stats_source = to_numpy(image) if scope == "volume" else None
        channels.append(clip_and_zscore(patch, stats_source, clip))

    shift_array = np.asarray(shifts, dtype=np.float32)
    meta = {
        "lesion_extent_mm": extent_mm.astype(np.float32),
        "fov_mm": np.asarray(fov_mm, dtype=np.float32),
        "spacing": np.asarray(spacing, dtype=np.float32),
        # Cache tự mô tả được lề dư của chính nó: cổng kiểm trong notebook đối chiếu
        # `crop_margin_voxels` thay vì suy từ hình dạng mảng.
        "crop_margin_voxels": np.asarray(margin, dtype=np.int32),
        "inner_size": np.asarray(size, dtype=np.int32),
        "crop_source": crop_source,
        "crop_mode": crop_mode,
        "align_phases": align,
        # Độ dịch của từng pha so với pha tham chiếu, theo mm. Đây là bằng chứng
        # kiểm được rằng việc căn có thật sự làm gì: ở chế độ `reference` mảng này
        # toàn 0, ở `per_phase` nó phải phản ánh đúng biên độ đã đo ở S-031
        # (trung vị ~12.4mm trong mặt phẳng, ~23.3mm theo Z).
        "phase_shift_mm": shift_array,
        "max_phase_shift_mm": np.float32(np.abs(shift_array).max(initial=0.0)),
        "phase_center_source": np.array(center_sources),
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


def _same_image_grid(image, mask) -> bool:
    """Return whether an uploaded mask occupies its paired image grid.

    A lesion mask on a different physical grid would produce a plausible crop
    at the wrong location.  Reject it rather than silently resampling a label
    whose origin/direction is unknown.
    """
    return (
        image.GetSize() == mask.GetSize()
        and np.allclose(image.GetSpacing(), mask.GetSpacing(), rtol=0.0, atol=1e-6)
        and np.allclose(image.GetOrigin(), mask.GetOrigin(), rtol=0.0, atol=1e-6)
        and np.allclose(image.GetDirection(), mask.GetDirection(), rtol=0.0, atol=1e-6)
    )


def _image_affine(image) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Build the voxel-to-world affine used by the E4 preprocessing path."""
    direction = np.array(image.GetDirection(), dtype=float).reshape(3, 3)
    spacing = np.array(image.GetSpacing(), dtype=float)
    affine = np.eye(4)
    affine[:3, :3] = direction @ np.diag(spacing)
    affine[:3, 3] = image.GetOrigin()
    return affine, direction, spacing


def process_uploaded_with_masks(
    image_paths: Mapping[str, Path],
    mask_paths: Mapping[str, Path],
    phase_config: list[dict[str, str]],
    config: Mapping[str, Any],
) -> tuple[np.ndarray, dict[str, Any]]:
    """Create a lesion-aligned model tensor from an uploaded MRI + mask set.

    The ROI recipes used by E4 and UniFormer are lesion-tight and align every
    phase using that phase's lesion centre. Eight MRI volumes alone therefore
    cannot reproduce either training input. This helper deliberately requires
    a paired annotation mask on the *same physical grid* for every phase, then mirrors
    :func:`process_patient_with_meta` without needing a dataset annotation.

    It is intentionally a preprocessing helper rather than serve-only code so
    offline notebooks and the web app share one geometry implementation.
    """
    expected_tokens = [phase["file"] for phase in phase_config]
    if len(expected_tokens) != 8 or len(set(expected_tokens)) != 8:
        raise ValueError("phase_config phải có đúng 8 file token khác nhau")
    missing_images = [token for token in expected_tokens if token not in image_paths]
    missing_masks = [token for token in expected_tokens if token not in mask_paths]
    if missing_images or missing_masks:
        details = []
        if missing_images:
            details.append(f"thiếu ảnh cho {missing_images}")
        if missing_masks:
            details.append(f"thiếu mask cho {missing_masks}")
        raise FileNotFoundError("; ".join(details))

    crop_mode = config.get("crop_mode", "fixed_mm")
    lesion_cfg = config.get("lesion_tight") or {}
    source = lesion_cfg.get("source", "bbox")
    align = config.get("align_phases", "reference")
    if crop_mode != "lesion_tight" or source != "mask" or align != "per_phase":
        raise ValueError(
            "suy luận upload chỉ hỗ trợ contract E4: lesion_tight + mask + per_phase"
        )

    ref_phase = str(config["reference_phase"])
    ref_token = next((phase["file"] for phase in phase_config if phase["name"] == ref_phase), None)
    if ref_token is None:
        raise ValueError(f"không tìm thấy pha tham chiếu {ref_phase!r} trong phase_config")

    size = tuple(int(value) for value in config["target_size"])
    if len(size) != 3 or any(value <= 0 for value in size):
        raise ValueError(f"target_size không hợp lệ: {size!r}")
    margin = tuple(int(value) for value in (config.get("crop_margin_voxels") or (0, 0, 0)))
    if len(margin) != 3 or any(value < 0 for value in margin):
        raise ValueError(f"crop_margin_voxels không hợp lệ: {margin!r}")
    grid_size = tuple(value + 2 * extra for value, extra in zip(size, margin, strict=True))
    interpolator = str(config.get("interpolator", "linear"))
    norm_cfg = config.get("normalize") or {}
    clip = tuple(norm_cfg.get("clip_percentile", (0.5, 99.5)))
    scope = norm_cfg.get("scope", "volume")

    ref_image = read_image(image_paths[ref_token])
    ref_mask = read_image(mask_paths[ref_token])
    if not _same_image_grid(ref_image, ref_mask):
        raise ValueError(f"mask {ref_token} không cùng lưới vật lý với ảnh MRI tương ứng")
    ref_affine, ref_direction, ref_spacing = _image_affine(ref_image)
    ref_center_voxel, extent_voxel = mask_center_extent_voxel(to_numpy(ref_mask))
    extent_mm = extent_voxel * ref_spacing
    spacing, fov_mm = adaptive_spacing(
        extent_mm,
        size,
        margin_factor=float(lesion_cfg.get("margin_factor", 1.6)),
        min_fov_mm=tuple(lesion_cfg.get("min_fov_mm", (40.0, 40.0, 40.0))),
        max_fov_mm=tuple(lesion_cfg.get("max_fov_mm", (200.0, 200.0, 200.0))),
    )
    ref_center_world = voxel_to_world(ref_affine, ref_center_voxel)

    channels: list[np.ndarray] = []
    annotation_masks: list[np.ndarray] = []
    shifts: list[np.ndarray] = []
    for phase in phase_config:
        token = phase["file"]
        image = ref_image if token == ref_token else read_image(image_paths[token])
        mask = ref_mask if token == ref_token else read_image(mask_paths[token])
        if not _same_image_grid(image, mask):
            raise ValueError(f"mask {token} không cùng lưới vật lý với ảnh MRI tương ứng")

        phase_affine, _, _ = _image_affine(image)
        phase_center_voxel, _ = mask_center_extent_voxel(to_numpy(mask))
        phase_center_world = voxel_to_world(phase_affine, phase_center_voxel)
        grid = make_reference_image(phase_center_world, ref_direction, spacing, grid_size)
        patch = to_numpy(resample_to_grid(image, grid, interpolator))
        # Keep the annotation on exactly the same per-phase crop grid as the MRI.
        # The serving layer uses this only for an optional viewer overlay; it is
        # never an output produced by the classifier.
        annotation_patch = to_numpy(resample_to_grid(mask, grid, "nearest"))
        stats_source = to_numpy(image) if scope == "volume" else None
        channels.append(clip_and_zscore(patch, stats_source, clip))
        annotation_masks.append((annotation_patch > 0).astype(np.uint8))
        shifts.append(np.asarray(phase_center_world, dtype=float) - ref_center_world)

    shift_array = np.asarray(shifts, dtype=np.float32)
    return np.stack(channels, axis=0), {
        "lesion_extent_mm": extent_mm.astype(np.float32),
        "fov_mm": np.asarray(fov_mm, dtype=np.float32),
        "spacing": np.asarray(spacing, dtype=np.float32),
        "crop_margin_voxels": np.asarray(margin, dtype=np.int32),
        "inner_size": np.asarray(size, dtype=np.int32),
        "crop_source": "mask",
        "crop_mode": crop_mode,
        "align_phases": align,
        "phase_shift_mm": shift_array,
        "max_phase_shift_mm": np.float32(np.abs(shift_array).max(initial=0.0)),
        "phase_center_source": np.asarray(["mask"] * len(phase_config)),
        # This is intentionally kept alongside the in-memory upload result only.
        # It lets the web viewer render the exact UniFormer crop without retaining
        # the original NIfTI files after inference.
        "annotation_masks": np.stack(annotation_masks, axis=0),
    }


def resample_annotation_masks(
    patient_id: str,
    annotation: Annotation,
    image_index: dict,
    phase_config: list[dict[str, str]],
    config: dict[str, Any],
    mask_index: dict | None,
) -> np.ndarray:
    """Resample eight annotation masks to the exact E4 crop grids.

    This mirrors the grid construction in :func:`process_patient_with_meta`,
    including ``align_phases: per_phase``.  It deliberately does not use the
    cached, normalised image tensor as a geometry proxy: each phase has its own
    crop centre under E4.  The helper is the only supported path for the Kaggle
    export notebook, preventing a visually plausible but spatially wrong
    overlay from being produced there.
    """
    from src.utils.ids import normalize_pid

    if mask_index is None:
        raise ValueError("mask_index is required to export annotation overlays")

    axis_order = config["axis_order"]
    ref_phase = config["reference_phase"]
    size = tuple(config["target_size"])
    crop_mode = config.get("crop_mode", "fixed_mm")
    lesion_cfg = config.get("lesion_tight") or {}
    source = lesion_cfg.get("source", "bbox")
    align = config.get("align_phases", "reference")
    if crop_mode not in CROP_MODES or source not in LESION_SOURCES or align not in ALIGN_MODES:
        raise ValueError("invalid crop, lesion source, or phase-alignment configuration")

    key = normalize_pid(patient_id)
    ref_token = next(p["file"] for p in phase_config if p["name"] == ref_phase)
    ref_path = image_index.get((key, ref_token))
    if ref_path is None:
        raise FileNotFoundError(f"{patient_id}: missing reference phase {ref_phase}")
    ref_image = read_image(ref_path)

    affine_direction = np.array(ref_image.GetDirection(), dtype=float).reshape(3, 3)
    ref_spacing = np.array(ref_image.GetSpacing(), dtype=float)
    ref_affine = np.eye(4)
    ref_affine[:3, :3] = affine_direction @ np.diag(ref_spacing)
    ref_affine[:3, 3] = ref_image.GetOrigin()

    ref_mask_path = (
        mask_index.get((key, ref_token))
        if crop_mode == "lesion_tight" and source == "mask"
        else None
    )
    center_voxel, extent_voxel, crop_source = _lesion_center_extent(
        patient_id, annotation, ref_phase, axis_order, ref_image, ref_mask_path
    )
    extent_mm = extent_voxel * ref_spacing
    if crop_mode == "lesion_tight":
        spacing, _ = adaptive_spacing(
            extent_mm,
            size,
            margin_factor=float(lesion_cfg.get("margin_factor", 1.6)),
            min_fov_mm=tuple(lesion_cfg.get("min_fov_mm", (40.0, 40.0, 40.0))),
            max_fov_mm=tuple(lesion_cfg.get("max_fov_mm", (200.0, 200.0, 200.0))),
        )
    else:
        spacing = tuple(config["target_spacing"])

    margin = tuple(int(m) for m in (config.get("crop_margin_voxels") or (0, 0, 0)))
    if len(margin) != 3 or any(m < 0 for m in margin):
        raise ValueError(f"invalid crop_margin_voxels: {margin!r}")
    grid_size = tuple(s + 2 * m for s, m in zip(size, margin, strict=True))
    center_world = voxel_to_world(ref_affine, center_voxel)
    reference = make_reference_image(center_world, affine_direction, spacing, grid_size)

    masks: list[np.ndarray] = []
    for phase in phase_config:
        image_path = image_index.get((key, phase["file"]))
        mask_path = mask_index.get((key, phase["file"]))
        if image_path is None:
            raise FileNotFoundError(f"{patient_id}: missing phase {phase['file']}")
        if mask_path is None:
            raise FileNotFoundError(
                f"{patient_id}: missing annotation mask for phase {phase['file']}"
            )
        image = read_image(image_path) if image_path != ref_path else ref_image
        if align == "per_phase" and phase["name"] != ref_phase:
            phase_center, _ = _phase_center_world(
                patient_id,
                phase["name"],
                phase["file"],
                image,
                annotation,
                mask_index,
                key,
                axis_order,
                center_world,
            )
            grid = make_reference_image(phase_center, affine_direction, spacing, grid_size)
        else:
            grid = reference
        mask = to_numpy(resample_to_grid(read_image(mask_path), grid, "nearest"))
        masks.append((mask > 0).astype(np.uint8))
    return np.stack(masks, axis=0)


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

        label_suffixes = data_config.get("label_suffixes", DEFAULT_LABEL_SUFFIXES)
        mask_index = scan_image_index(labels_dir, label_suffixes)
        logger.info("Đã quét %d file mask ở %s", len(mask_index), labels_dir)

        # Quét ra 0 mask mà vẫn chạy tiếp là hỏng âm thầm: mọi ca sẽ lặng lẽ rơi về
        # bbox và cả mẻ build xong trông như thành công, trong khi mask chưa từng
        # được dùng. Đã xảy ra một lần vì mask không mang hậu tố `_0000` như ảnh
        # (WORKLOG S-059). Dừng ngay, và in tên file thật để chẩn đoán được liền.
        if not mask_index:
            sample = sorted(p.name for p in list(labels_dir.iterdir())[:5])
            raise SystemExit(
                f"Quét được 0 mask ở {labels_dir} với đuôi {tuple(label_suffixes)}.\n"
                f"Vài tên file thật trong thư mục đó: {sample}\n"
                "Sửa 'label_suffixes' trong configs/data.yaml cho khớp, hoặc đổi "
                "lesion_tight.source sang 'bbox' nếu cố ý không dùng mask."
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
                "crop_mode": crop_mode,
                "lesion_tight": lesion_cfg if crop_mode == "lesion_tight" else None,
                "target_spacing": config["target_spacing"],
                # `target_size` là kích thước TRONG (model nhận). Hình dạng mảng thật
                # trong .npz là `target_size + 2*crop_margin_voxels` — hai khoá này
                # phải đọc cùng nhau, đừng suy kích thước model từ shape của mảng.
                "target_size": config["target_size"],
                "crop_margin_voxels": list(config.get("crop_margin_voxels") or (0, 0, 0)),
                "interpolator": config.get("interpolator", "linear"),
                "normalize": config.get("normalize"),
                "align_phases": config.get("align_phases", "reference"),
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
        [
            "patient_id",
            "status",
            "seconds",
            "crop_source",
            "fov_mm",
            "max_shift_mm",
            "n_fallback_center",
            "note",
        ],
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
                crop_margin_voxels=meta["crop_margin_voxels"],
                inner_size=meta["inner_size"],
                crop_source=np.str_(meta["crop_source"]),
                align_phases=np.str_(meta["align_phases"]),
                phase_shift_mm=meta["phase_shift_mm"],
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
                    "max_shift_mm": round(float(meta["max_phase_shift_mm"]), 1),
                    "n_fallback_center": int((meta["phase_center_source"] == "fallback_ref").sum()),
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
