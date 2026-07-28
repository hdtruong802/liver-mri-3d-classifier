"""Lập chỉ mục file NIfTI trong `lld/images/` và `lld/labels/`.

Bộ dữ liệu theo quy ước nnU-Net, và **hai thư mục đặt tên khác nhau**::

    lld/images/MR-391135_1_C+V_0000.nii    ảnh   — có hậu tố kênh _0000
    lld/labels/MR-391135_1_C+V.nii         mask  — KHÔNG có _0000

Quét mask bằng danh sách đuôi của ảnh sẽ khớp **0 file**, và vì `build_cache` có
đường lui về bbox nên cả mẻ vẫn chạy xong mà không ai biết mask chưa từng được
dùng (WORKLOG S-059). Dùng `DEFAULT_LABEL_SUFFIXES` cho `lld/labels/`.

Lesion-suffix biến thiên theo bệnh nhân (1, 2, 6…) và ID có/không gạch nối, nên KHÔNG
dựng path bằng công thức — quét thư mục 1 lần rồi map ``(patient_key, token) -> path``.
Luôn bỏ qua `.cache/` (rác tải về của HuggingFace).

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

# Mask không mang hậu tố kênh `_0000` (quy ước nnU-Net). Đuôi dài đặt trước để
# `*.nii` không nuốt mất `*.nii.gz`.
DEFAULT_LABEL_SUFFIXES: tuple[str, ...] = (".nii.gz", ".nii")


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
