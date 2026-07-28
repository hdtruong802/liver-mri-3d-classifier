"""Cửa sổ cắt **bám theo kích thước tổn thương**, thay cho cửa sổ mm cố định.

## Vì sao cần

Cache v0 dùng cửa sổ vật lý cố định 144×144×144mm cho mọi bệnh nhân. Hệ quả: một
tổn thương 20mm chỉ chiếm ~14% bề rộng khung, phần còn lại là gan lành và mô xung
quanh. Model phải tự học cách bỏ qua 86% khung hình, với chỉ 316 ca huấn luyện.

Baseline chính thức của LLD-MMRI2023 làm ngược lại: cắt bám sát tổn thương rồi
resize về 112×112×14. Ba đội đầu bảng đều xoay quanh việc định vị và căn tổn
thương chứ không phải backbone (hạng 2 dùng ResNet18 vẫn đạt macro-F1 0.8078).

## Cách làm

Giữ nguyên `target_size` (số voxel đầu ra không đổi), nhưng cho **spacing biến
thiên theo từng bệnh nhân**: cửa sổ vật lý = kích thước tổn thương × `margin_factor`,
kẹp trong `[min_fov_mm, max_fov_mm]`. Tổn thương do đó chiếm một tỉ lệ khung hình
gần như nhau ở mọi ca.

## Đánh đổi phải biết

Cách này **làm mất thông tin kích thước tuyệt đối** của tổn thương — vốn có ý nghĩa
chẩn đoán (nang 5mm khác hẳn HCC 50mm). Hai biện pháp giảm thiểu, đều bắt buộc:

1. `min_fov_mm` / `max_fov_mm` chặn hai đầu, nên mức phóng đại bị giới hạn chứ
   không tự do.
2. `build_cache` ghi `lesion_extent_mm` và `fov_mm` vào từng file cache, để model
   sau này dùng lại được kích thước thật làm đặc trưng phụ nếu cần. Thông tin bị
   crop bỏ đi vẫn được giữ lại ở cạnh, không mất hẳn.
"""

from __future__ import annotations

import numpy as np

from src.data.annotation import BBox3D
from src.preprocess.geometry import AXIS_ORDERS

__all__ = [
    "adaptive_spacing",
    "bbox_extent_voxel",
    "mask_center_extent_voxel",
]


def bbox_extent_voxel(box: BBox3D, axis_order: str) -> np.ndarray:
    """Kích thước bbox theo voxel, cùng quy ước trục với `bbox_center_voxel`.

    Trục 2 luôn là slice. Cộng 1 vì bbox tính theo chỉ số bao gồm cả hai đầu:
    từ voxel 10 đến voxel 12 là 3 voxel, không phải 2.
    """
    if axis_order not in AXIS_ORDERS:
        raise ValueError(f"axis_order phải thuộc {AXIS_ORDERS}, nhận {axis_order!r}")
    ex = box.x_max - box.x_min + 1.0
    ey = box.y_max - box.y_min + 1.0
    ez = box.z_max - box.z_min + 1.0
    return np.array([ex, ey, ez]) if axis_order == "xy" else np.array([ey, ex, ez])


def mask_center_extent_voxel(mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Tâm và kích thước của vùng khác 0 trong mask, theo voxel.

    Trả về ``(center, extent)`` trong hệ trục của **chính mảng mask**, nên không
    cần `axis_order` — mask nằm cùng lưới voxel với ảnh của pha đó.

    Raise `ValueError` nếu mask rỗng: một mask trống nghĩa là bước phân vùng đã
    hỏng ở ca này, và im lặng rơi về tâm ảnh sẽ tạo ra dữ liệu sai mà không ai
    biết.
    """
    nonzero = np.argwhere(np.asarray(mask) > 0)
    if nonzero.size == 0:
        raise ValueError("mask rỗng — không có voxel nào khác 0")
    lo = nonzero.min(axis=0).astype(float)
    hi = nonzero.max(axis=0).astype(float)
    center = (lo + hi) / 2.0
    extent = hi - lo + 1.0
    return center, extent


def adaptive_spacing(
    extent_mm: np.ndarray,
    size: tuple[int, int, int],
    margin_factor: float,
    min_fov_mm: tuple[float, float, float],
    max_fov_mm: tuple[float, float, float],
) -> tuple[tuple[float, float, float], np.ndarray]:
    """Suy ra spacing của lưới đích từ kích thước tổn thương.

    Trả về ``(spacing, fov_mm)``. `spacing` là mm/voxel trên mỗi trục sao cho
    `size` voxel phủ đúng `fov_mm` milimet.
    """
    extent_mm = np.asarray(extent_mm, dtype=float)
    if extent_mm.shape != (3,):
        raise ValueError(f"extent_mm phải có 3 phần tử, nhận {extent_mm.shape}")
    if margin_factor <= 0:
        raise ValueError(f"margin_factor phải dương, nhận {margin_factor}")

    lo = np.asarray(min_fov_mm, dtype=float)
    hi = np.asarray(max_fov_mm, dtype=float)
    if np.any(hi < lo):
        raise ValueError(f"max_fov_mm {hi} nhỏ hơn min_fov_mm {lo}")

    fov = np.clip(extent_mm * float(margin_factor), lo, hi)
    spacing = fov / np.asarray(size, dtype=float)
    return tuple(float(s) for s in spacing), fov
