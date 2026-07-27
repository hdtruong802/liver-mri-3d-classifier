"""Lập chỉ mục file ảnh NIfTI trong `lld/images/`.

Tên file: ``{patient}_{lesion}_{token}_0000.nii[.gz]`` (vd ``MR-391135_1_C+A_0000.nii``).
Lesion-suffix biến thiên theo bệnh nhân (1, 2, 6…) và ID có/không gạch nối, nên KHÔNG
dựng path bằng công thức — quét thư mục 1 lần rồi map ``(patient_key, token) -> path``.
Chỉ đọc `images/`; bỏ qua `labels/` (mask segmentation) và `.cache/`.

**Phải nhận cả `.nii` lẫn `.nii.gz`** (WORKLOG S-025): repo HuggingFace gốc lưu
`.nii.gz`, nhưng bản upload lên Kaggle đã **giải nén thành `.nii`** (đó là lý do
dataset phình lên 83.7GB). Chỉ tìm một đuôi ⇒ index rỗng ⇒ mọi bước sau bị bỏ qua
âm thầm, không báo lỗi.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from src.utils.ids import normalize_pid

ImageIndex = dict[tuple[str, str], Path]

# Thứ tự ưu tiên: nếu cùng một (bệnh nhân, pha) có cả hai, bản nén được chọn.
DEFAULT_IMAGE_SUFFIXES: tuple[str, ...] = ("_0000.nii.gz", "_0000.nii")


def scan_image_index(
    images_dir: str | Path,
    image_suffixes: str | Sequence[str] = DEFAULT_IMAGE_SUFFIXES,
) -> ImageIndex:
    """Quét thư mục ảnh -> map ``(patient_key, file_token) -> Path``.

    `patient_key` là ID đã chuẩn hoá chữ số (khớp annotation/split). `file_token`
    là token pha trong tên file (vd 'C+A', 'InPhase').

    `image_suffixes` nhận một chuỗi hoặc danh sách; mặc định thử cả `.nii.gz` và
    `.nii`. Glob hai đuôi không chồng lấn nhau (tên kết thúc bằng `.gz` không khớp
    pattern `*_0000.nii`), nên không sợ đếm trùng.
    """
    images_dir = Path(images_dir)
    suffixes = (image_suffixes,) if isinstance(image_suffixes, str) else tuple(image_suffixes)

    index: ImageIndex = {}
    for suffix in suffixes:
        for path in images_dir.glob(f"*{suffix}"):
            stem = path.name[: -len(suffix)]
            parts = stem.split("_")
            if len(parts) < 3:
                continue
            patient, token = parts[0], "_".join(parts[2:])
            index.setdefault((normalize_pid(patient), token), path)
    return index


def phase_paths(index: ImageIndex, patient_id: str, phase_tokens: list[str]) -> list[Path]:
    """Trả về path 8 pha (theo thứ tự `phase_tokens`) cho một bệnh nhân.

    Raise nếu thiếu pha — người gọi (EDA/manifest) quyết chiến lược xử lý thiếu pha.
    """
    key = normalize_pid(patient_id)
    paths: list[Path] = []
    missing: list[str] = []
    for token in phase_tokens:
        path = index.get((key, token))
        if path is None:
            missing.append(token)
        else:
            paths.append(path)
    if missing:
        raise FileNotFoundError(f"{patient_id}: thiếu pha {missing}")
    return paths
