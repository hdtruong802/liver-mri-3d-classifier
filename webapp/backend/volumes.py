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

# Cache "lát nào có tổn thương" theo đường dẫn mask. Tính nó phải đọc nguyên khối
# (~19MB mỗi thì), nên không được tính lại cho mỗi request.
_mask_flags_cache: dict[str, tuple[bool, ...]] = {}


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


def find_mask_files(case_dir: Path, case_id: str) -> dict[str, Path]:
    """Map `file_token -> path` cho mask tổn thương của một ca.

    Mask nằm ở thư mục con `labels/` và **không** mang hậu tố kênh `_0000` (quy ước
    nnU-Net) — dùng nhầm quy ước đặt tên của ảnh sẽ khớp 0 file và mọi thứ lặng lẽ
    chạy tiếp không có mask (đã xảy ra một lần ở pipeline train, WORKLOG S-059).

    ⚠️ Đây là **nhãn segmentation official của LLD-MMRI**, không phải đầu ra của model.
    Dự án này không làm segmentation (AGENTS.md §3.9). Mọi chỗ hiển thị mask phải nói
    rõ điều đó, nếu không người xem sẽ tưởng model tự khoanh được tổn thương.
    """
    labels_dir = case_dir / "labels"
    if not labels_dir.is_dir():
        return {}
    found: dict[str, Path] = {}
    for phase in PHASES:
        for suffix in (".nii", ".nii.gz"):
            for path in labels_dir.glob(f"{case_id}_{phase.file_token}{suffix}"):
                found.setdefault(phase.file_token, path)
    return found


def mask_slice_flags(mask_path: Path) -> tuple[bool, ...]:
    """Lát nào của mask có ít nhất một voxel tổn thương. Độ dài = số lát của khối.

    Dùng để đánh dấu trên thanh trượt những lát đáng nhìn. Không có nó, người đọc
    phải kéo qua cả 84 lát để tìm chỗ tổn thương xuất hiện.

    **Không hạ mẫu để chạy nhanh hơn.** Đọc `dataobj[::4, ::4]` sẽ nhanh gấp 16 lần
    nhưng có thể bỏ sót lát chỉ chứa vài voxel tổn thương — và hệ quả là dẫn người
    đọc đi qua đúng chỗ cần nhìn. Chi phí thật được trả một lần rồi cache.

    ⚠️ Đây là **nhãn của người chú giải** trong bộ dữ liệu, không phải đầu ra của
    model (AGENTS.md §3.9).
    """
    key = str(mask_path)
    if key not in _mask_flags_cache:
        volume = np.asarray(nib.load(key).dataobj)
        _mask_flags_cache[key] = tuple(bool(v) for v in (volume > 0).any(axis=(0, 1)))
    return _mask_flags_cache[key]


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


def overlay_annotation(gray: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Phủ mask lên ảnh xám: viền đặc + ruột mờ, trả về mảng RGB.

    Viền đặc chứ không tô kín: bác sĩ cần **nhìn thấy pixel bên dưới** để tự đánh giá,
    và một mảng màu kín sẽ che đúng chỗ đang cần đọc. Ruột chỉ nhuộm 25% để vẫn thấy
    được cấu trúc mà không mất dấu vùng.

    Màu `#E879F9` (token `annotation` trong `tailwind.config.js`) nằm **ngoài** cả bảng
    bảy lớp lẫn bảng trạng thái, có chủ ý: mask không phải một lớp và không phải một
    trạng thái. Dùng màu lớp cho nó — ví dụ `#38BDF8` của "nang" — sẽ khiến người xem
    đọc vùng khoanh thành một chẩn đoán.
    """
    rgb = np.stack([gray, gray, gray], axis=-1).astype(np.float32)
    binary = mask > 0
    if not binary.any():
        return rgb.astype(np.uint8)

    # Biên = pixel thuộc mask mà có ít nhất một hàng xóm 4-liên thông không thuộc mask.
    padded = np.pad(binary, 1, mode="constant", constant_values=False)
    interior = padded[:-2, 1:-1] & padded[2:, 1:-1] & padded[1:-1, :-2] & padded[1:-1, 2:] & binary
    edge = binary & ~interior

    colour = np.array([232, 121, 249], dtype=np.float32)  # #E879F9, token `annotation`
    rgb[binary] = rgb[binary] * 0.75 + colour * 0.25
    rgb[edge] = colour
    return np.clip(rgb, 0, 255).astype(np.uint8)


def render_slice_png(path: Path, z: int, mask_path: Path | None = None) -> bytes:
    """Render lát `z` của một volume ra PNG. Có `mask_path` thì phủ mask lên.

    Ảnh được xoay để trục hàng của mảng nằm ngang, khớp quy ước hiển thị axial thông
    thường. Không lật trái phải — lật nhầm bên trên ảnh y tế là lỗi nghiêm trọng, nên
    tuyệt đối không "sửa cho đẹp" ở đây.
    """
    key = (f"{path}|{mask_path or ''}", z)
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
    oriented = normalized.T[::-1]

    if mask_path is None:
        picture = Image.fromarray(oriented, mode="L")
    else:
        mask_img = nib.load(str(mask_path))
        if tuple(int(v) for v in mask_img.shape[:3]) != tuple(int(v) for v in img.shape[:3]):
            # Mask lệch hình học so với ảnh thì phủ lên là sai chỗ. Thà không phủ.
            raise ValueError(
                f"mask {mask_path.name} có shape {tuple(mask_img.shape[:3])} "
                f"khác ảnh {tuple(int(v) for v in img.shape[:3])}"
            )
        mask_slab = np.asarray(mask_img.dataobj[:, :, z]).T[::-1]
        picture = Image.fromarray(overlay_annotation(oriented, mask_slab), mode="RGB")

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
