"""Đọc volume NIfTI và render lát ra PNG.

Đây là **ảnh thật của bệnh nhân thật**, không phải ảnh sinh ra bằng thuật toán. Bản
bolt có một module 308 dòng dựng ảnh bụng giả trông như thật; nó đã bị bỏ. `PRODUCT.md`
gọi dữ liệu giả trông như thật là rủi ro nghiêm trọng nhất của dự án, và một ảnh MRI
giả còn nguy hiểm hơn một con số giả vì không ai kiểm chứng được bằng mắt.

Chuẩn hoá cường độ dùng percentile 0.5–99.5 trên **toàn volume**, khớp với
`configs/preprocess_e4.yaml` (`normalize.clip_percentile`, `scope: volume`). Dùng
min-max thô sẽ để một voxel nhiễu duy nhất dìm toàn ảnh thành đen.
"""

from __future__ import annotations

import io
from collections import OrderedDict
from pathlib import Path

import nibabel as nib
import numpy as np
from PIL import Image

from webapp.backend.config import SLICE_CACHE_SIZE
from webapp.backend.phases import PHASES, Phase

_CLIP_PERCENTILE: tuple[float, float] = (0.5, 99.5)

# Cache PNG đã render, khoá theo (đường dẫn file, chỉ số lát). LRU thủ công vì
# `functools.lru_cache` không cho biết kích thước bytes đang giữ.
_slice_cache: OrderedDict[tuple[str, int], bytes] = OrderedDict()

# Cache header (shape, spacing) — rẻ, và tránh mở lại file cho mỗi request lát.
_geometry_cache: dict[str, tuple[tuple[int, int, int], tuple[float, float, float]]] = {}


class VolumeNotFoundError(FileNotFoundError):
    """Không tìm thấy file volume cho ca và thì được yêu cầu."""


def find_phase_files(case_dir: Path, case_id: str) -> dict[str, Path]:
    """Map `file_token -> path` cho một ca trong thư mục dữ liệu.

    Tên file LLD-MMRI: `{patient}_{lesion}_{phase_token}_0000.nii`. Chấp nhận cả
    `.nii` và `.nii.gz` vì repo gốc lưu `.gz` còn bản trên Kaggle đã giải nén
    (`configs/data.yaml`).
    """
    if not case_dir.is_dir():
        return {}
    found: dict[str, Path] = {}
    for phase in PHASES:
        for suffix in (".nii", ".nii.gz"):
            for path in case_dir.glob(f"{case_id}_{phase.file_token}*{suffix}"):
                found.setdefault(phase.file_token, path)
    return found


def read_geometry(path: Path) -> tuple[tuple[int, int, int], tuple[float, float, float]]:
    """Shape và spacing mm, đọc từ header — không nạp mảng dữ liệu vào bộ nhớ."""
    key = str(path)
    if key not in _geometry_cache:
        img = nib.load(str(path))
        shape = tuple(int(v) for v in img.shape[:3])
        zooms = tuple(float(v) for v in img.header.get_zooms()[:3])
        _geometry_cache[key] = (shape, zooms)  # type: ignore[assignment]
    return _geometry_cache[key]


def n_slices(path: Path) -> int:
    """Số lát theo trục Z (trục 2 của mảng NIfTI)."""
    shape, _ = read_geometry(path)
    return shape[2]


def _normalize(slab: np.ndarray) -> np.ndarray:
    """Cửa sổ cường độ theo percentile rồi trải về 0–255.

    MRI không có đơn vị chuẩn như HU của CT, nên phải chuẩn hoá theo từng chuỗi.
    """
    finite = slab[np.isfinite(slab)]
    if finite.size == 0:
        return np.zeros(slab.shape, dtype=np.uint8)
    lo, hi = np.percentile(finite, _CLIP_PERCENTILE)
    if hi <= lo:
        return np.zeros(slab.shape, dtype=np.uint8)
    clipped = np.clip(slab, lo, hi)
    return (((clipped - lo) / (hi - lo)) * 255.0).astype(np.uint8)


def render_slice_png(path: Path, z: int) -> bytes:
    """Render lát `z` của một volume ra PNG thang xám.

    Ảnh được xoay để trục hàng của mảng nằm ngang, khớp quy ước hiển thị axial thông
    thường. Không lật trái phải — lật nhầm bên trên ảnh y tế là lỗi nghiêm trọng, nên
    tuyệt đối không "sửa cho đẹp" ở đây.
    """
    key = (str(path), z)
    cached = _slice_cache.get(key)
    if cached is not None:
        _slice_cache.move_to_end(key)
        return cached

    img = nib.load(str(path))
    total = int(img.shape[2])
    if not 0 <= z < total:
        raise IndexError(f"lát {z} ngoài khoảng [0, {total - 1}]")

    slab = np.asarray(img.dataobj[:, :, z], dtype=np.float32)
    normalized = _normalize(slab)
    # `.T` đưa trục 0 (x) thành cột; `[::-1]` đặt gốc toạ độ lên trên như ảnh axial.
    picture = Image.fromarray(normalized.T[::-1], mode="L")

    buffer = io.BytesIO()
    picture.save(buffer, format="PNG", optimize=True)
    payload = buffer.getvalue()

    _slice_cache[key] = payload
    while len(_slice_cache) > SLICE_CACHE_SIZE:
        _slice_cache.popitem(last=False)
    return payload


def phase_of_token(token: str) -> Phase | None:
    for phase in PHASES:
        if phase.file_token == token:
            return phase
    return None
