"""Lấy mẫu một pha lên lưới đích (SimpleITK).

Điểm mấu chốt: dùng **phép biến đổi đồng nhất (Identity)** trong không gian thế giới.
Mỗi voxel của lưới đích được quy ra toạ độ mm, rồi lấy mẫu ảnh nguồn tại đúng điểm mm
đó. Vì cả 8 pha chung hệ toạ độ bệnh nhân, thao tác này vừa đổi spacing/kích thước,
vừa **căn chỉnh** chúng với nhau — không cần registration riêng ở v0.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

_INTERPOLATORS = {
    "linear": "sitkLinear",
    "nearest": "sitkNearestNeighbor",
    "bspline": "sitkBSpline",
}


def read_image(path: str | Path):
    """Đọc ảnh y tế giữ nguyên hình học (origin/spacing/direction)."""
    import SimpleITK as sitk

    return sitk.ReadImage(str(path))


def resample_to_grid(image, reference, interpolator: str = "linear"):
    """Lấy mẫu `image` lên hình học của `reference`. Vùng ngoài ảnh nguồn = 0."""
    import SimpleITK as sitk

    if interpolator not in _INTERPOLATORS:
        raise ValueError(f"interpolator phải thuộc {sorted(_INTERPOLATORS)}, nhận {interpolator!r}")
    return sitk.Resample(
        image,
        reference,
        sitk.Transform(),  # Identity: ánh xạ theo toạ độ thế giới
        getattr(sitk, _INTERPOLATORS[interpolator]),
        0.0,
        sitk.sitkFloat32,
    )


def to_numpy(image) -> np.ndarray:
    """Đổi ảnh SimpleITK sang numpy theo thứ tự trục (x, y, z).

    SimpleITK trả mảng theo (z, y, x) nên phải chuyển vị — nếu quên, khối dữ liệu sẽ
    bị hoán trục âm thầm và mọi thứ phía sau đều sai.
    """
    import SimpleITK as sitk

    return sitk.GetArrayFromImage(image).transpose(2, 1, 0)
