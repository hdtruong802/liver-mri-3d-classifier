"""GATE GEOMETRY — xác minh ảnh thật khớp annotation trước khi tin ROI-crop.

**Vì sao bắt buộc** (docs/W2_plan.md T2.1): bản dữ liệu thực nhận là
`wanglab/LLD-MMRI-MedSAM2` — bản đóng gói lại cho segmentation. Nó *có thể* đã
resample/reorient ảnh trong khi `LLD_MMRI_Annotation.json` vẫn giữ toạ độ gốc.
Nếu vậy, crop theo bbox sẽ cắt nhầm chỗ và **mọi kết quả sau đó đều vô nghĩa**.
Thêm nữa, PDF challenge (p.9) xác nhận các thì chụp khác nhau (non-contrast
coronal, DWI matrix 132×116) → không được giả định 8 pha cùng geometry.

Gate kiểm 3 tầng, tăng dần độ chặt:
1. `spacing` trong NIfTI header khớp `pixel_spacing`/`slice_spacing` annotation?
2. bbox có nằm trong biên ảnh không (và theo trục nào — xác định axis order)?
3. (thủ công, trong notebook) overlay bbox lên slice → mắt người xác nhận trúng u.

Gate KHÔNG tự sửa dữ liệu. Nó báo cáo. Không đạt → dừng, không crop theo bbox.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from src.data.annotation import Annotation
from src.data.images import ImageIndex
from src.utils.ids import normalize_pid

# Sai số cho phép khi so spacing header vs annotation (mm). Nới tay vì annotation
# làm tròn 6 chữ số còn header NIfTI là float32.
SPACING_TOL_MM = 0.01


@dataclass
class PhaseCheck:
    """Kết quả kiểm một (bệnh nhân, pha)."""

    patient_id: str
    phase: str
    image_shape: tuple[int, ...]
    header_spacing: tuple[float, float, float]
    annotation_spacing: tuple[float, float, float]
    spacing_matches: bool
    bbox_in_bounds_xy: bool
    bbox_in_bounds_xy_swapped: bool
    bbox_z_in_bounds: bool
    notes: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """Đạt = spacing khớp, bbox nằm trong biên (theo ít nhất 1 axis order), z hợp lệ."""
        return (
            self.spacing_matches
            and (self.bbox_in_bounds_xy or self.bbox_in_bounds_xy_swapped)
            and self.bbox_z_in_bounds
        )


@dataclass
class GateReport:
    """Tổng hợp gate trên một nhóm bệnh nhân mẫu."""

    checks: list[PhaseCheck]

    @property
    def passed(self) -> bool:
        return bool(self.checks) and all(c.passed for c in self.checks)

    @property
    def n_failed(self) -> int:
        return sum(1 for c in self.checks if not c.passed)

    def axis_order_verdict(self) -> str:
        """Suy ra thứ tự trục ảnh từ việc bbox lọt biên theo cách nào.

        Trả về 'xy' (bbox.x ↔ shape[0]), 'yx' (bbox.x ↔ shape[1]),
        'ambiguous' (cả hai đều lọt — ảnh vuông, không phân biệt được),
        hoặc 'none' (không cách nào lọt → geometry lệch thật).
        """
        if not self.checks:
            return "none"
        direct = all(c.bbox_in_bounds_xy for c in self.checks)
        swapped = all(c.bbox_in_bounds_xy_swapped for c in self.checks)
        if direct and swapped:
            return "ambiguous"
        if direct:
            return "xy"
        if swapped:
            return "yx"
        return "none"

    def summary(self) -> str:
        """Báo cáo text gọn để in trong notebook."""
        lines = [
            f"GATE GEOMETRY: {'PASS' if self.passed else 'FAIL'} "
            f"({len(self.checks) - self.n_failed}/{len(self.checks)} phase-check đạt)",
            f"axis order: {self.axis_order_verdict()}",
            "",
        ]
        for c in self.checks:
            status = "OK  " if c.passed else "FAIL"
            lines.append(
                f"{status} {c.patient_id:<12} {c.phase:<10} shape={c.image_shape} "
                f"spacing_hdr={tuple(round(v, 3) for v in c.header_spacing)} "
                f"spacing_ann={tuple(round(v, 3) for v in c.annotation_spacing)}"
            )
            for note in c.notes:
                lines.append(f"       - {note}")
        return "\n".join(lines)


def _load_header(path: Path) -> tuple[tuple[int, ...], tuple[float, float, float]]:
    """Đọc shape + voxel spacing từ header NIfTI (không nạp toàn bộ pixel data)."""
    import nibabel as nib

    img = nib.load(str(path))
    shape = tuple(int(v) for v in img.shape)
    zooms = img.header.get_zooms()[:3]
    spacing = tuple(float(z) for z in zooms)
    while len(spacing) < 3:
        spacing = (*spacing, float("nan"))
    return shape, spacing  # type: ignore[return-value]


def check_phase(
    patient_id: str,
    phase_name: str,
    phase_token: str,
    annotation: Annotation,
    image_index: ImageIndex,
) -> PhaseCheck:
    """Kiểm geometry một (bệnh nhân, pha): spacing header vs annotation + bbox trong biên."""
    key = normalize_pid(patient_id)
    path = image_index.get((key, phase_token))
    if path is None:
        raise FileNotFoundError(f"{patient_id}: không có file pha {phase_token}")

    shape, header_spacing = _load_header(path)
    entry = annotation.phase_entry(patient_id, phase_name)
    ps = entry.get("pixel_spacing") or [float("nan"), float("nan")]
    ann_spacing = (
        float(ps[0]),
        float(ps[1]),
        float(entry.get("slice_spacing") or float("nan")),
    )

    notes: list[str] = []

    # 1) spacing: chỉ so 2 trục trong mặt phẳng (trục thứ 3 hay lệch giữa
    #    slice_spacing và slice_thickness nên không dùng làm tiêu chí cứng).
    spacing_matches = all(
        abs(header_spacing[i] - ann_spacing[i]) <= SPACING_TOL_MM for i in range(2)
    )
    if not spacing_matches:
        notes.append(
            f"pixel_spacing lệch: header={header_spacing[:2]} vs annotation={ann_spacing[:2]}"
            " → ảnh có thể đã bị resample so với lúc annotate"
        )
    if len(header_spacing) > 2 and abs(header_spacing[2] - ann_spacing[2]) > SPACING_TOL_MM:
        notes.append(
            f"slice spacing lệch: header={header_spacing[2]:.3f} vs "
            f"annotation={ann_spacing[2]:.3f} (cảnh báo, không tính FAIL)"
        )

    # 2) bbox trong biên — thử cả 2 axis order vì chưa biết ảnh là (x,y,z) hay (y,x,z).
    box = annotation.bbox3d(patient_id, phase_name)
    dim0, dim1 = (shape + (0, 0))[:2]

    def _fits(x_limit: int, y_limit: int) -> bool:
        """bbox có lọt trong biên (x_limit, y_limit) không."""
        return box.x_min >= 0 and box.x_max <= x_limit and box.y_min >= 0 and box.y_max <= y_limit

    bbox_in_bounds_xy = _fits(dim0, dim1)
    bbox_in_bounds_yx = _fits(dim1, dim0)
    if not (bbox_in_bounds_xy or bbox_in_bounds_yx):
        notes.append(
            f"bbox VƯỢT BIÊN theo cả 2 axis order: box x=[{box.x_min:.1f},{box.x_max:.1f}] "
            f"y=[{box.y_min:.1f},{box.y_max:.1f}] vs shape={shape}"
        )

    # 3) chỉ số slice hợp lệ.
    n_slices = shape[2] if len(shape) > 2 else 0
    bbox_z_in_bounds = box.z_min >= 0 and box.z_max < n_slices
    if not bbox_z_in_bounds:
        notes.append(
            f"slice_idx ngoài biên: z=[{box.z_min},{box.z_max}] vs n_slices={n_slices}"
            " → ảnh có thể đã bị cắt/resample theo trục z"
        )

    return PhaseCheck(
        patient_id=patient_id,
        phase=phase_name,
        image_shape=shape,
        header_spacing=header_spacing,
        annotation_spacing=ann_spacing,
        spacing_matches=spacing_matches,
        bbox_in_bounds_xy=bbox_in_bounds_xy,
        bbox_in_bounds_xy_swapped=bbox_in_bounds_yx,
        bbox_z_in_bounds=bbox_z_in_bounds,
        notes=notes,
    )


def run_gate(
    patient_ids: list[str],
    annotation: Annotation,
    image_index: ImageIndex,
    phase_config: list[dict[str, str]],
) -> GateReport:
    """Chạy gate trên một nhóm bệnh nhân mẫu, mọi pha trong `phase_config`.

    3–5 bệnh nhân là đủ để phát hiện lệch geometry hệ thống (T2.1). Bỏ qua
    (bệnh nhân, pha) thiếu file — việc thiếu pha do `missing_phase_report` lo.
    """
    checks: list[PhaseCheck] = []
    for pid in patient_ids:
        for phase in phase_config:
            try:
                checks.append(
                    check_phase(pid, phase["name"], phase["file"], annotation, image_index)
                )
            except (FileNotFoundError, KeyError):
                continue
    return GateReport(checks=checks)


def bbox_overlay_slice(
    patient_id: str,
    phase_name: str,
    phase_token: str,
    annotation: Annotation,
    image_index: ImageIndex,
) -> tuple:
    """Trả về (slice 2D ở giữa lesion, bbox 2D của slice đó) để vẽ overlay.

    Tầng 3 của gate là **mắt người**: notebook vẽ ảnh này ra và người xem xác
    nhận hộp trùng vùng tổn thương. Không có kiểm tự động nào thay thế được.
    """
    import nibabel as nib
    import numpy as np

    key = normalize_pid(patient_id)
    path = image_index[(key, phase_token)]
    box = annotation.bbox3d(patient_id, phase_name)
    mid = (box.z_min + box.z_max) // 2

    volume = np.asarray(nib.load(str(path)).dataobj)
    sl = volume[:, :, mid] if volume.ndim > 2 else volume
    return sl, box, mid
