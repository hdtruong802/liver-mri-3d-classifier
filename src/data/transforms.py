"""Augmentation cho patch đã cache — thao tác trên dict ``{"image": tensor[8,X,Y,Z], ...}``.

Ba ràng buộc định hình bộ transform này:

1. **Không đụng trục Z một cách tuỳ tiện.** Trục Z là hướng đầu-chân và độ dày lát
   cắt lớn hơn nhiều (3.0mm so với 1.5mm trong mặt phẳng); lật/xoay quanh Z tạo ra
   giải phẫu không tồn tại. Chỉ xoay 90° **trong mặt phẳng** (trục 0-1).
2. **Cùng một phép biến đổi cho cả 8 pha.** 8 kênh là 8 pha đã căn chỉnh của cùng
   một tổn thương; augment lệch nhau giữa các kênh sẽ phá vỡ chính thứ mà model
   phải học (biến đổi tín hiệu theo thì).
3. **Không có tham số học từ dữ liệu.** Mọi phép ở đây là ngẫu nhiên thuần, không
   ước lượng thống kê từ tập nào — nên không có đường leakage (AGENTS.md §3.3).

Viết bằng torch thuần thay vì MONAI transform: ít phụ thuộc, và ba phép này quá
đơn giản để cần tới máy móc dict-transform của MONAI.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

# Trục không gian trong tensor [C, X, Y, Z] (kênh là trục 0).
_AXIS_X, _AXIS_Y, _AXIS_Z = 1, 2, 3


class RandomFlip:
    """Lật ngẫu nhiên theo các trục cho trước (mặc định: hai trục trong mặt phẳng)."""

    def __init__(self, prob: float = 0.5, axes: Sequence[int] = (_AXIS_X, _AXIS_Y)) -> None:
        self.prob = prob
        self.axes = tuple(axes)

    def __call__(self, item: dict[str, Any]) -> dict[str, Any]:
        import torch

        image = item["image"]
        for axis in self.axes:
            if self.prob > 0 and torch.rand(1).item() < self.prob:
                image = torch.flip(image, dims=(axis,))
        item["image"] = image
        return item


class RandomRot90InPlane:
    """Xoay 0/90/180/270° trong mặt phẳng cắt ngang. Không xoay ngoài mặt phẳng.

    Nếu mặt phẳng **không vuông**, xoay 90°/270° sẽ hoán vị hai chiều và đổi shape —
    batch sau đó không collate được, và lỗi chỉ nổ giữa epoch. Trường hợp đó chỉ xoay
    180°, phép duy nhất giữ nguyên shape. Hiện crop là 96×96 nên nhánh này chưa chạm
    tới, nhưng kill-switch VRAM trong plan có ghi phương án hạ crop.
    """

    def __init__(self, prob: float = 0.5) -> None:
        self.prob = prob

    def __call__(self, item: dict[str, Any]) -> dict[str, Any]:
        import torch

        if self.prob > 0 and torch.rand(1).item() < self.prob:
            image = item["image"]
            square = image.shape[_AXIS_X] == image.shape[_AXIS_Y]
            k = int(torch.randint(1, 4, (1,)).item()) if square else 2
            item["image"] = torch.rot90(image, k, dims=(_AXIS_X, _AXIS_Y))
        return item


class RandomIntensity:
    """Nhiễu cường độ nhẹ: ``x * (1 + s) + b``, **riêng cho từng pha**.

    Ở đây lệch giữa các kênh là *cố ý*: nó mô phỏng dao động khuếch đại/độ lệch nền
    giữa các lần chụp của cùng một bệnh nhân, thứ máy MRI thật vẫn tạo ra. Khác với
    biến đổi hình học — cái đó phải đồng nhất giữa các pha.
    """

    def __init__(self, shift: float = 0.1, scale: float = 0.1, prob: float = 0.5) -> None:
        self.shift = shift
        self.scale = scale
        self.prob = prob

    def __call__(self, item: dict[str, Any]) -> dict[str, Any]:
        import torch

        if self.prob <= 0 or torch.rand(1).item() >= self.prob:
            return item
        image = item["image"]
        per_channel = (image.shape[0], 1, 1, 1)
        scale = 1.0 + (torch.rand(per_channel) * 2 - 1) * self.scale
        shift = (torch.rand(per_channel) * 2 - 1) * self.shift
        item["image"] = image * scale + shift
        return item


class Compose:
    """Chuỗi transform áp lần lượt lên item."""

    def __init__(self, transforms: Sequence[Callable[[dict], dict]]) -> None:
        self.transforms = list(transforms)

    def __call__(self, item: dict[str, Any]) -> dict[str, Any]:
        for transform in self.transforms:
            item = transform(item)
        return item


def build_train_transform(config: dict[str, Any] | None) -> Compose | None:
    """Dựng transform train từ khối ``data.augment:`` của config; ``None`` = không augment.

    Ví dụ khối config::

        augment:
          flip_prob: 0.5
          rot90_prob: 0.5
          intensity_prob: 0.5
          intensity_shift: 0.1
          intensity_scale: 0.1
    """
    if not config:
        return None
    transforms: list[Callable[[dict], dict]] = []
    if config.get("flip_prob", 0):
        transforms.append(RandomFlip(prob=float(config["flip_prob"])))
    if config.get("rot90_prob", 0):
        transforms.append(RandomRot90InPlane(prob=float(config["rot90_prob"])))
    if config.get("intensity_prob", 0):
        transforms.append(
            RandomIntensity(
                shift=float(config.get("intensity_shift", 0.0)),
                scale=float(config.get("intensity_scale", 0.0)),
                prob=float(config["intensity_prob"]),
            )
        )
    return Compose(transforms) if transforms else None
