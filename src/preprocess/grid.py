"""Lưới đích trong không gian mm — nơi 8 pha gặp nhau.

**Đây chính là bước căn chỉnh.** 8 pha có lưới voxel khác nhau nhưng chung hệ toạ độ
bệnh nhân (xem `src/preprocess/geometry.py`). Định nghĩa MỘT lưới trong không gian mm,
tâm tại tổn thương, rồi lấy mẫu cả 8 pha lên đó ⇒ chúng tự khớp nhau. Không cần
registration riêng ở v0 (đã chốt với người dùng; rigid registration là ablation W3
để bù nhịp thở).

Hướng của lưới lấy từ **pha tham chiếu** để giữ đúng chiều giải phẫu.
"""

from __future__ import annotations

import numpy as np


def target_origin(
    center_world: np.ndarray,
    direction: np.ndarray,
    spacing: tuple[float, float, float],
    size: tuple[int, int, int],
) -> np.ndarray:
    """Toạ độ mm của voxel (0,0,0) sao cho tâm lưới rơi đúng vào `center_world`.

    Với voxel chỉ số `i`: ``world(i) = origin + direction @ (spacing * i)``.
    Tâm lưới ở chỉ số ``(size - 1) / 2``, nên
    ``origin = center - direction @ (spacing * (size - 1) / 2)``.
    """
    half = np.asarray(spacing, dtype=float) * (np.asarray(size, dtype=float) - 1.0) / 2.0
    return (
        np.asarray(center_world, dtype=float)
        - np.asarray(direction, dtype=float).reshape(3, 3) @ half
    )


def make_reference_image(
    center_world: np.ndarray,
    direction: np.ndarray,
    spacing: tuple[float, float, float],
    size: tuple[int, int, int],
):
    """Dựng ảnh SimpleITK rỗng làm lưới đích cho `sitk.Resample`.

    Chỉ mang hình học (origin/spacing/direction), không mang dữ liệu ảnh.
    """
    import SimpleITK as sitk

    reference = sitk.Image([int(s) for s in size], sitk.sitkFloat32)
    reference.SetSpacing([float(s) for s in spacing])
    reference.SetDirection([float(v) for v in np.asarray(direction, dtype=float).ravel()])
    reference.SetOrigin([float(v) for v in target_origin(center_world, direction, spacing, size)])
    return reference
