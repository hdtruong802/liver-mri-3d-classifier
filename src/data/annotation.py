"""Đọc `LLD_MMRI_Annotation.json` (annotation phân loại gốc).

Cấu trúc đã xác minh trên 498 bệnh nhân (xem docs/W2_plan.md §0):
- `Category_info`: map tên lớp -> chỉ số (0..6), kèm nhóm Benign/Malignant.
- `Annotation_info[pid]`: list 8 phase-entry; mỗi entry có `phase`, metadata hình học,
  và `annotation.lesion["0"]` = {category, bbox.2D_box[]}.
- Mỗi bệnh nhân đúng 1 lesion; category nhất quán qua 8 pha; `3D_box` = null nên
  phải gộp `2D_box` per-slice thành ROI 3D.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.data.taxonomy import MALIGNANT_INDICES
from src.utils.io import load_json


@dataclass(frozen=True)
class BBox3D:
    """ROI 3D (voxel index) gộp từ các hộp 2D theo slice, cho một (bệnh nhân, pha)."""

    x_min: float
    y_min: float
    z_min: int
    x_max: float
    y_max: float
    z_max: int


class Annotation:
    """Truy vấn annotation phân loại LLD-MMRI."""

    def __init__(self, path: str | Path) -> None:
        data = load_json(path)
        self._info: dict = data["Annotation_info"]
        raw_cat: dict = data["Category_info"]
        # Chỉ giữ các entry tên_lớp -> int (bỏ khoá "Benign"/"Malignant" là list).
        self.class_to_index: dict[str, int] = {
            k: v for k, v in raw_cat.items() if isinstance(v, int)
        }
        self.index_to_class: dict[int, str] = {v: k for k, v in self.class_to_index.items()}

    def patient_ids(self) -> list[str]:
        """Danh sách patient_id (key annotation, giữ nguyên hình thức gốc)."""
        return list(self._info.keys())

    def __len__(self) -> int:
        return len(self._info)

    def _lesion(self, patient_id: str) -> dict:
        # category nhất quán qua các pha nên lấy lesion của phase-entry đầu tiên.
        return self._info[patient_id][0]["annotation"]["lesion"]["0"]

    def category_of(self, patient_id: str) -> int:
        """Chỉ số lớp (0..6) của bệnh nhân."""
        return int(self._lesion(patient_id)["category"])

    def is_malignant(self, patient_id: str) -> bool:
        """True nếu lớp thuộc nhóm ác (ICC/di căn/HCC)."""
        return self.category_of(patient_id) in MALIGNANT_INDICES

    def phases_of(self, patient_id: str) -> list[str]:
        """Tên các pha có mặt (theo annotation, vd 'In Phase')."""
        return [entry["phase"] for entry in self._info[patient_id]]

    def raw_entries(self, patient_id: str) -> list[dict]:
        """Toàn bộ phase-entry thô của một bệnh nhân (cho EDA/geometry gate)."""
        return self._info[patient_id]

    def phase_entry(self, patient_id: str, phase_name: str) -> dict:
        """Phase-entry thô của một (bệnh nhân, pha); raise KeyError nếu không có."""
        for entry in self._info[patient_id]:
            if entry["phase"] == phase_name:
                return entry
        raise KeyError(f"không có pha {phase_name!r} cho {patient_id!r}")

    def bbox3d(self, patient_id: str, phase_name: str) -> BBox3D:
        """Gộp `2D_box` theo `slice_idx` -> ROI 3D cho (bệnh nhân, pha).

        Dùng để crop lesion từ full-volume (bản dữ liệu không có patch cắt sẵn).
        """
        entry = self.phase_entry(patient_id, phase_name)
        boxes = entry["annotation"]["lesion"]["0"]["bbox"]["2D_box"]
        if not boxes:
            raise ValueError(f"2D_box rỗng: {patient_id} / {phase_name}")
        return BBox3D(
            x_min=min(b["x_min"] for b in boxes),
            y_min=min(b["y_min"] for b in boxes),
            z_min=min(int(b["slice_idx"]) for b in boxes),
            x_max=max(b["x_max"] for b in boxes),
            y_max=max(b["y_max"] for b in boxes),
            z_max=max(int(b["slice_idx"]) for b in boxes),
        )
