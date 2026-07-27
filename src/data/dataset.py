"""Dataset reader LLD-MMRI: 8 pha + nhãn 7 lớp + bbox3D cho mỗi bệnh nhân.

Tách hai tầng:
- `load_sample()`: thuần numpy/nibabel, không phụ thuộc torch — dùng được ở
  EDA/manifest/script kiểm tra nhanh (T1.2 DoD).
- `LLDMMRIDataset`: wrapper `torch.utils.data.Dataset`, import torch **lười**
  (trong `__init__`) để module này import được cả khi chưa cài torch.

Chỉ đọc `images/` + annotation JSON. KHÔNG đụng `lld/labels/` (mask segmentation)
hay `lld/.cache/` — sai bài toán (AGENTS.md §3.9: không làm segmentation).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from src.data.annotation import Annotation, BBox3D
from src.data.images import (
    DEFAULT_IMAGE_SUFFIXES,
    ImageIndex,
    phase_paths,
    scan_image_index,
)
from src.utils.ids import normalize_pid


@dataclass(frozen=True)
class Sample:
    """Một mẫu: 8 volume pha (chưa resample/crop) + nhãn + bbox3D (pha đầu)."""

    patient_id: str
    phases: list[np.ndarray]  # mỗi phần tử: array 3D thô từ NIfTI, geometry gốc
    label: int
    bbox3d: BBox3D


def _load_nifti(path: Path) -> np.ndarray:
    import nibabel as nib

    return np.asarray(nib.load(str(path)).get_fdata())


def load_sample(
    patient_id: str,
    annotation: Annotation,
    image_index: ImageIndex,
    phase_config: list[dict[str, str]],
) -> Sample:
    """Nạp 1 bệnh nhân: đọc 8 file NIfTI thô + nhãn + bbox3D (pha đầu tiên).

    `phase_config`: list các dict {"name": <tên annotation>, "file": <token file>},
    đúng thứ tự `configs/data.yaml: phases`.
    """
    tokens = [p["file"] for p in phase_config]
    paths = phase_paths(image_index, patient_id, tokens)
    phases = [_load_nifti(p) for p in paths]

    label = annotation.category_of(patient_id)
    first_phase_name = phase_config[0]["name"]
    bbox = annotation.bbox3d(patient_id, first_phase_name)

    return Sample(patient_id=patient_id, phases=phases, label=label, bbox3d=bbox)


class LLDMMRIDataset:
    """`torch.utils.data.Dataset` cho LLD-MMRI (import torch lười trong __init__).

    Trả về (theo T1.2 DoD): dict {"phases": tensor[8,...], "label": int,
    "patient_id": str, "bbox3d": BBox3D}. Resample/crop/z-score thuộc
    `src/preprocess/` (W2 ngày 3), KHÔNG nằm ở đây — dataset này chỉ đọc thô.
    """

    def __init__(
        self,
        patient_ids: list[str],
        data_root: str | Path,
        annotation_rel: str,
        images_rel: str,
        phase_config: list[dict[str, str]],
        image_suffixes: str | Sequence[str] = DEFAULT_IMAGE_SUFFIXES,
        transform: Any | None = None,
    ) -> None:
        try:
            import torch  # noqa: F401
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "LLDMMRIDataset cần torch. Dùng load_sample() trực tiếp nếu chưa cài."
            ) from exc

        data_root = Path(data_root)
        self.patient_ids = patient_ids
        self.annotation = Annotation(data_root / annotation_rel)
        self.image_index = scan_image_index(data_root / images_rel, image_suffixes)
        self.phase_config = phase_config
        self.transform = transform

    def __len__(self) -> int:
        return len(self.patient_ids)

    def __getitem__(self, idx: int) -> dict[str, Any]:
        import torch

        pid = self.patient_ids[idx]
        sample = load_sample(pid, self.annotation, self.image_index, self.phase_config)
        phases_np = np.stack(sample.phases, axis=0)  # [8, H, W, D] geometry gốc, có thể lệch nhau
        item = {
            "phases": torch.from_numpy(phases_np).float(),
            "label": sample.label,
            "patient_id": normalize_pid(pid),
            "bbox3d": sample.bbox3d,
        }
        if self.transform is not None:
            item = self.transform(item)
        return item
