"""Thống kê EDA cho LLD-MMRI (T2.1 trong docs/W2_plan.md).

Điểm quan trọng: **phần lớn EDA tính được chỉ từ `LLD_MMRI_Annotation.json`**
(18MB) — phân bố lớp, spacing/thickness mỗi pha, kích thước bbox, khuyến nghị
crop size. Không cần nạp ảnh 83.7GB. Chỉ `missing_phase_report()` cần chỉ mục
file ảnh, và gate geometry (`src/data/geometry_gate.py`) mới cần đọc ảnh thật.

Mọi hàm ở đây **thuần** (annotation vào → thống kê ra) để notebook chỉ là lớp
mỏng gọi vào, đúng quy ước AGENTS.md §4.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field

from src.data.annotation import Annotation
from src.data.images import ImageIndex
from src.data.taxonomy import CLASS_NAMES, SHORT_NAMES
from src.utils.ids import normalize_pid


def class_distribution(annotation: Annotation) -> dict[int, int]:
    """Đếm số bệnh nhân theo từng lớp (0..6).

    Dùng để đối chiếu với phân bố official trong PDF challenge (HCC 157 áp đảo …
    FNH 46) — nếu lệch thì bản dữ liệu không toàn vẹn, phải dừng.
    """
    counts: dict[int, int] = dict.fromkeys(CLASS_NAMES, 0)
    for pid in annotation.patient_ids():
        counts[annotation.category_of(pid)] += 1
    return counts


def format_class_distribution(counts: dict[int, int]) -> str:
    """Bảng text phân bố lớp, sắp giảm dần — tiện in trong notebook."""
    total = sum(counts.values())
    lines = [f"{'lớp':<34} {'n':>5} {'%':>7}"]
    for idx, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        pct = 100.0 * n / total if total else 0.0
        lines.append(f"{SHORT_NAMES[idx]:<10} {CLASS_NAMES[idx]:<23} {n:>5} {pct:>6.1f}%")
    lines.append(f"{'TỔNG':<34} {total:>5}")
    return "\n".join(lines)


@dataclass
class PhaseGeometry:
    """Metadata hình học của một (bệnh nhân, pha), lấy từ annotation."""

    patient_id: str
    phase: str
    pixel_spacing: tuple[float, float]
    slice_spacing: float
    slice_thickness: float


def phase_geometry(annotation: Annotation) -> list[PhaseGeometry]:
    """Trích metadata hình học mọi (bệnh nhân, pha) từ annotation.

    PDF challenge nói các thì chụp khác nhau (non-contrast coronal, DWI thô,
    T1 spacing 2mm vs T2 1mm) — hàm này cho số liệu thực để xác nhận.
    """
    out: list[PhaseGeometry] = []
    for pid in annotation.patient_ids():
        for entry in annotation.raw_entries(pid):
            ps = entry.get("pixel_spacing") or [float("nan"), float("nan")]
            out.append(
                PhaseGeometry(
                    patient_id=pid,
                    phase=entry["phase"],
                    pixel_spacing=(float(ps[0]), float(ps[1])),
                    slice_spacing=float(entry.get("slice_spacing", float("nan"))),
                    slice_thickness=float(entry.get("slice_thickness", float("nan"))),
                )
            )
    return out


def _summary(values: list[float]) -> dict[str, float]:
    """min / p50 / p95 / max cho một list số (bỏ qua list rỗng)."""
    if not values:
        return {}
    ordered = sorted(values)
    return {
        "min": ordered[0],
        "p50": statistics.median(ordered),
        "p95": ordered[min(len(ordered) - 1, int(0.95 * (len(ordered) - 1)))],
        "max": ordered[-1],
    }


def geometry_summary_by_phase(geoms: list[PhaseGeometry]) -> dict[str, dict[str, dict[str, float]]]:
    """Tóm tắt spacing/thickness theo từng pha: {pha: {trường: {min/p50/p95/max}}}."""
    by_phase: dict[str, list[PhaseGeometry]] = {}
    for g in geoms:
        by_phase.setdefault(g.phase, []).append(g)

    out: dict[str, dict[str, dict[str, float]]] = {}
    for phase, items in by_phase.items():
        out[phase] = {
            "pixel_spacing_x": _summary([g.pixel_spacing[0] for g in items]),
            "pixel_spacing_y": _summary([g.pixel_spacing[1] for g in items]),
            "slice_spacing": _summary([g.slice_spacing for g in items]),
            "slice_thickness": _summary([g.slice_thickness for g in items]),
        }
    return out


@dataclass
class BBoxStats:
    """Kích thước lesion của một (bệnh nhân, pha), cả voxel lẫn mm."""

    patient_id: str
    phase: str
    width_px: float
    height_px: float
    depth_slices: int
    width_mm: float
    height_mm: float
    depth_mm: float


def bbox_stats(annotation: Annotation, phase_name: str) -> list[BBoxStats]:
    """Kích thước bbox 3D (gộp từ 2D_box) của mọi bệnh nhân, ở một pha.

    Quy đổi sang mm bằng `pixel_spacing` / `slice_spacing` trong annotation, để
    khuyến nghị crop size không phụ thuộc độ phân giải từng ca.
    """
    out: list[BBoxStats] = []
    for pid in annotation.patient_ids():
        try:
            box = annotation.bbox3d(pid, phase_name)
        except KeyError:
            continue
        entry = annotation.phase_entry(pid, phase_name)
        ps = entry.get("pixel_spacing") or [1.0, 1.0]
        slice_spacing = float(entry.get("slice_spacing") or 1.0)

        w_px = float(box.x_max - box.x_min)
        h_px = float(box.y_max - box.y_min)
        d_sl = int(box.z_max - box.z_min) + 1  # inclusive
        out.append(
            BBoxStats(
                patient_id=pid,
                phase=phase_name,
                width_px=w_px,
                height_px=h_px,
                depth_slices=d_sl,
                width_mm=w_px * float(ps[0]),
                height_mm=h_px * float(ps[1]),
                depth_mm=d_sl * slice_spacing,
            )
        )
    return out


def recommend_crop_size(
    stats: list[BBoxStats],
    target_spacing: tuple[float, float, float] = (1.5, 1.5, 3.0),
    margin: float = 1.3,
    percentile: float = 0.95,
) -> dict[str, float | int]:
    """Gợi ý crop size (voxel) ở `target_spacing`, phủ `percentile` số ca kèm margin.

    Trả về cả số liệu mm thô để người đọc tự phán đoán, không chỉ một con số.
    Kết quả này là **đầu vào cho quyết định ở T2.2**, không tự động ghi đè config.
    """
    if not stats:
        return {}

    def pct(values: list[float]) -> float:
        ordered = sorted(values)
        return ordered[min(len(ordered) - 1, int(percentile * (len(ordered) - 1)))]

    w_mm = pct([s.width_mm for s in stats]) * margin
    h_mm = pct([s.height_mm for s in stats]) * margin
    d_mm = pct([s.depth_mm for s in stats]) * margin

    return {
        "width_mm_p95_margin": round(w_mm, 1),
        "height_mm_p95_margin": round(h_mm, 1),
        "depth_mm_p95_margin": round(d_mm, 1),
        "voxels_x": int(round(w_mm / target_spacing[0])),
        "voxels_y": int(round(h_mm / target_spacing[1])),
        "voxels_z": int(round(d_mm / target_spacing[2])),
        "n_cases": len(stats),
    }


@dataclass
class MissingPhaseReport:
    """Ca thiếu pha: tổng quan + chi tiết từng bệnh nhân."""

    n_patients: int
    n_complete: int
    n_incomplete: int
    missing_by_phase: dict[str, int] = field(default_factory=dict)
    incomplete_patients: list[tuple[str, list[str]]] = field(default_factory=list)


def missing_phase_report(
    annotation: Annotation, image_index: ImageIndex, phase_tokens: list[str]
) -> MissingPhaseReport:
    """Đối chiếu annotation với file ảnh thật -> ca nào thiếu pha nào.

    Cần `image_index` (quét thư mục ảnh) nên chỉ chạy được ở nơi có data thật
    (Kaggle). Quyết định xử lý ca thiếu pha thuộc T2.2, không quyết ở đây.
    """
    missing_by_phase = dict.fromkeys(phase_tokens, 0)
    incomplete: list[tuple[str, list[str]]] = []

    for pid in annotation.patient_ids():
        key = normalize_pid(pid)
        missing = [tok for tok in phase_tokens if (key, tok) not in image_index]
        if missing:
            incomplete.append((pid, missing))
            for tok in missing:
                missing_by_phase[tok] += 1

    n = len(annotation)
    return MissingPhaseReport(
        n_patients=n,
        n_complete=n - len(incomplete),
        n_incomplete=len(incomplete),
        missing_by_phase=missing_by_phase,
        incomplete_patients=incomplete,
    )
