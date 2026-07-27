"""Hình học: voxel ↔ toạ độ thế giới (mm), và phán quyết thứ tự trục.

**Vì sao cần toạ độ thế giới.** 8 pha của cùng một bệnh nhân KHÔNG cùng lưới voxel:
pha động 512²×88 @0.78/2.6mm, T2WI 512²×24 @9mm, DWI 256²×24 @1.56mm (WORKLOG S-029).
Toạ độ voxel của pha này vô nghĩa với pha kia. Nhưng cả 8 đều quy chiếu về **cùng một
hệ toạ độ bệnh nhân DICOM** (annotation ghi `origin` thật, vd `[-197.13, -201.04, -98.14]`),
nên mm là ngôn ngữ chung duy nhất.

**Phán quyết thứ tự trục.** Annotation cho bbox riêng cho *từng pha*. Cùng một tổn thương
vật lý ⇒ đổi tâm bbox của 8 pha sang mm thì chúng phải **hội tụ về một điểm**. Cách hiểu
trục sai làm chúng tán loạn — và tán mạnh, vì các pha khác spacing nhiều (0.78 vs 1.56mm)
nên hoán vị x/y tạo lệch vật lý lớn. Đây là bằng chứng hình học thuần tuý, không phải
nhìn mắt cũng không phải heuristic cường độ.

Cần cách này vì kiểm biên (`src/data/geometry_gate.py`) bất lực: **0/3984 ảnh không vuông**.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field

import numpy as np

from src.data.annotation import Annotation, BBox3D
from src.data.images import ImageIndex
from src.utils.ids import normalize_pid

# Hai cách hiểu: bbox.x ứng với trục 0 của mảng ('xy'), hay với trục 1 ('yx').
AXIS_ORDERS = ("xy", "yx")

# Ngưỡng độ tán (mm) để coi 8 pha là "hội tụ". Nới tay vì có sai số nhịp thở giữa
# các lần chụp và sai số người vẽ bbox.
CONVERGENCE_TOL_MM = 25.0

# Chênh lệch tối thiểu giữa hai cách hiểu để một bệnh nhân được TÍNH PHIẾU.
#
# Vì sao cần: sức phân biệt đến từ độ lệch `origin_x - origin_y` giữa các pha. Đo trên
# dữ liệu thật, độ tán dự kiến khi hiểu sai có trung vị chỉ ~7mm và **200/498 ca dưới
# 5mm** — với những ca đó hai cách hiểu gần như trùng nhau, bỏ phiếu chỉ là nhiễu.
# Chỉ đếm ca có chênh lệch thật thì kết luận mới sạch (dù số ca dùng được ít hơn).
DECISIVE_MARGIN_MM = 5.0


def voxel_to_world(affine: np.ndarray, ijk: np.ndarray) -> np.ndarray:
    """Đổi toạ độ voxel (i, j, k) sang toạ độ thế giới (mm) qua affine NIfTI."""
    ijk = np.asarray(ijk, dtype=float)
    homogeneous = np.array([ijk[0], ijk[1], ijk[2], 1.0])
    return (np.asarray(affine, dtype=float) @ homogeneous)[:3]


def bbox_center_voxel(box: BBox3D, axis_order: str) -> np.ndarray:
    """Tâm bbox trong toạ độ voxel, theo cách hiểu trục đã chọn.

    `'xy'`: bbox.x → trục 0, bbox.y → trục 1. `'yx'`: ngược lại.
    Trục 2 luôn là slice (`slice_idx`) — điều này không mơ hồ.
    """
    if axis_order not in AXIS_ORDERS:
        raise ValueError(f"axis_order phải thuộc {AXIS_ORDERS}, nhận {axis_order!r}")
    cx = (box.x_min + box.x_max) / 2.0
    cy = (box.y_min + box.y_max) / 2.0
    cz = (box.z_min + box.z_max) / 2.0
    return np.array([cx, cy, cz]) if axis_order == "xy" else np.array([cy, cx, cz])


def lesion_center_world(
    annotation: Annotation,
    patient_id: str,
    phase_name: str,
    affine: np.ndarray,
    axis_order: str,
) -> np.ndarray:
    """Tâm tổn thương của một (bệnh nhân, pha) trong toạ độ thế giới (mm)."""
    box = annotation.bbox3d(patient_id, phase_name)
    return voxel_to_world(affine, bbox_center_voxel(box, axis_order))


def _spread_mm(points: list[np.ndarray]) -> float:
    """Độ tán của một chùm điểm: khoảng cách lớn nhất giữa hai điểm bất kỳ (mm)."""
    if len(points) < 2:
        return 0.0
    arr = np.stack(points)
    diffs = arr[:, None, :] - arr[None, :, :]
    return float(np.sqrt((diffs**2).sum(axis=-1)).max())


@dataclass
class AxisOrderVerdict:
    """Phán quyết thứ tự trục, kèm bằng chứng để người đọc tự đánh giá."""

    n_compared: int = 0  # số bệnh nhân so được (≥2 pha)
    n_decisive: int = 0  # trong đó, số ca có sức phân biệt thật
    votes: dict[str, int] = field(default_factory=dict)
    median_spread_mm: dict[str, float] = field(default_factory=dict)

    @property
    def verdict(self) -> str:
        """`'xy'` / `'yx'` / `'inconclusive'`.

        Trả `inconclusive` khi: không có ca nào phân biệt được; phiếu không áp đảo;
        hoặc bên thắng **vẫn** tán quá `CONVERGENCE_TOL_MM` (không cách hiểu nào làm
        các pha hội tụ ⇒ có vấn đề khác, phải điều tra chứ không đoán).
        """
        if self.n_decisive == 0 or not self.votes:
            return "inconclusive"
        winner = max(self.votes, key=lambda k: self.votes[k])
        if self.votes[winner] / self.n_decisive < 0.9:
            return "inconclusive"
        if self.median_spread_mm.get(winner, float("inf")) > CONVERGENCE_TOL_MM:
            return "inconclusive"
        return winner

    def summary(self) -> str:
        lines = [
            f"AXIS ORDER (toạ độ thế giới): {self.verdict}",
            f"  {self.n_compared} bệnh nhân so được · {self.n_decisive} ca có sức phân biệt "
            f"(chênh ≥ {DECISIVE_MARGIN_MM:.0f}mm)",
        ]
        for order in AXIS_ORDERS:
            v = self.votes.get(order, 0)
            share = 100 * v / self.n_decisive if self.n_decisive else 0
            spread = self.median_spread_mm.get(order, float("nan"))
            lines.append(
                f"  {order}: {v} phiếu ({share:.0f}%) · độ tán giữa các pha, trung vị = "
                f"{spread:.1f} mm"
            )
        lines.append("  (độ tán nhỏ = các pha chỉ về cùng một điểm ⇒ cách hiểu đúng)")
        if self.verdict == "inconclusive":
            lines.append("  → KHÔNG kết luận được. DỪNG, xác nhận bằng overlay trước khi crop.")
        return "\n".join(lines)


def resolve_axis_order(
    patient_ids: list[str],
    annotation: Annotation,
    image_index: ImageIndex,
    phase_config: list[dict[str, str]],
) -> AxisOrderVerdict:
    """Phán quyết thứ tự trục bằng độ hội tụ của tâm tổn thương giữa các pha.

    Chỉ đọc **affine trong header** (không nạp pixel) nên quét cả 498 ca rất nhanh.
    Bệnh nhân nào có dưới 2 pha đọc được thì bỏ qua (không có gì để so).
    """
    import nibabel as nib

    votes = dict.fromkeys(AXIS_ORDERS, 0)
    spreads: dict[str, list[float]] = {order: [] for order in AXIS_ORDERS}
    n_compared = n_decisive = 0

    for pid in patient_ids:
        key = normalize_pid(pid)
        affines: list[tuple[str, np.ndarray]] = []
        for phase in phase_config:
            path = image_index.get((key, phase["file"]))
            if path is None:
                continue
            try:
                affines.append((phase["name"], nib.load(str(path)).affine))
            except Exception:  # noqa: BLE001 — file hỏng thì bỏ qua ca đó
                continue
        if len(affines) < 2:
            continue

        per_order: dict[str, float] = {}
        for order in AXIS_ORDERS:
            centers: list[np.ndarray] = []
            for phase_name, affine in affines:
                try:
                    centers.append(lesion_center_world(annotation, pid, phase_name, affine, order))
                except (KeyError, ValueError):
                    continue
            if len(centers) >= 2:
                per_order[order] = _spread_mm(centers)

        if len(per_order) < len(AXIS_ORDERS):
            continue

        n_compared += 1
        for order, spread in per_order.items():
            spreads[order].append(spread)

        # Chỉ tính phiếu khi hai cách hiểu KHÁC nhau đủ rõ. Ca mà cả hai gần bằng
        # nhau không mang thông tin (xem DECISIVE_MARGIN_MM) — đếm vào chỉ thêm nhiễu.
        best, worst = sorted(per_order, key=lambda k: per_order[k])
        if per_order[worst] - per_order[best] < DECISIVE_MARGIN_MM:
            continue
        n_decisive += 1
        votes[best] += 1

    return AxisOrderVerdict(
        n_compared=n_compared,
        n_decisive=n_decisive,
        votes=votes,
        median_spread_mm={
            order: (statistics.median(v) if v else float("nan")) for order, v in spreads.items()
        },
    )
