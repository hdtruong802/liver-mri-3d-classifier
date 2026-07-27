"""Augmentation cho patch đã cache — thao tác trên dict ``{"image": tensor[8,X,Y,Z], ...}``.

**Bộ transform này bám theo recipe của baseline official LLD-MMRI2023**
(`LMMMEng/LLD-MMRI2023`, `main/datasets/transforms.py`), thứ đạt macro-F1 0.6083 trên
test-104. Trước đó ta tự chọn `rot90` (xoay 90/180/270°) và nhiễu cường độ — official
không dùng cả hai, mà dùng **xoay ±10°** cùng random-crop tịnh tiến. Xoay 90° trên lát
cắt ngang bụng không phải biến đổi giải phẫu hợp lệ; đây là một trong các khác biệt
protocol đã được ghi nhận (WORKLOG S-043).

Hai ràng buộc vẫn giữ nguyên:

1. **Cùng một phép biến đổi hình học cho cả 8 pha.** 8 kênh là 8 pha đã căn chỉnh của
   cùng một tổn thương; augment lệch nhau giữa các kênh sẽ phá vỡ chính thứ mà model
   phải học (biến đổi tín hiệu theo thì).
2. **Không có tham số học từ dữ liệu.** Mọi phép ở đây là ngẫu nhiên thuần, không ước
   lượng thống kê từ tập nào — nên không có đường leakage (AGENTS.md §3.3).

Riêng ràng buộc "không đụng trục Z" thì **đã bỏ**: official lật cả trục z (p=0.5). Đây
là quyết định theo recipe, không phải vì lập luận giải phẫu ở S-034 đã sai; nó nằm
trong danh sách ablate ở W4.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

# Trục không gian trong tensor [C, X, Y, Z] (kênh là trục 0).
_AXIS_X, _AXIS_Y, _AXIS_Z = 1, 2, 3

_AXIS_BY_NAME = {"x": _AXIS_X, "y": _AXIS_Y, "z": _AXIS_Z}


def resolve_axes(names: Sequence[str] | None) -> tuple[int, ...]:
    """Đổi tên trục trong config (``["x", "y", "z"]``) thành chỉ số tensor."""
    if not names:
        return (_AXIS_X, _AXIS_Y)
    unknown = [n for n in names if str(n).lower() not in _AXIS_BY_NAME]
    if unknown:
        raise ValueError(f"trục không hợp lệ {unknown}; chỉ nhận {sorted(_AXIS_BY_NAME)}")
    return tuple(_AXIS_BY_NAME[str(n).lower()] for n in names)


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


class RandomRotateSmall:
    """Xoay một góc nhỏ ngẫu nhiên **trong mặt phẳng**, giữ nguyên shape.

    Bản tương ứng của `rotate(image, angle=10)` trong baseline official: góc lấy đều
    trong ``[-degrees, +degrees]``, quay quanh trục z, áp **đồng nhất cho cả 8 pha**.

    Hai sai khác có chủ ý so với official, ghi rõ để sau này ablate được:

    - ``reshape=False`` (official dùng ``reshape=True`` rồi center-crop lại). Kết quả
      hình học tương đương, nhưng ta không phải cắt lại nên không đổi shape giữa chừng.
    - ``order=1`` (nội suy tuyến tính) thay vì mặc định ``order=3`` của scipy. Đây là
      đánh đổi **tốc độ**: khối [8,96,96,48] lớn gấp 2,5 lần khối của official, mà
      augmentation chạy trên CPU trong DataLoader worker và nằm trên đường tới hạn của
      thời gian mỗi epoch.
    """

    def __init__(self, degrees: float = 10.0, prob: float = 1.0, order: int = 1) -> None:
        self.degrees = degrees
        self.prob = prob
        self.order = order

    def __call__(self, item: dict[str, Any]) -> dict[str, Any]:
        import numpy as np
        import torch
        from scipy import ndimage

        if self.degrees <= 0 or self.prob <= 0 or torch.rand(1).item() >= self.prob:
            return item

        angle = float((torch.rand(1).item() * 2 - 1) * self.degrees)
        image = item["image"]
        rotated = ndimage.rotate(
            image.numpy(),
            angle=angle,
            axes=(_AXIS_X, _AXIS_Y),
            reshape=False,
            order=self.order,
            mode="constant",
            cval=0.0,
        )
        item["image"] = torch.from_numpy(np.ascontiguousarray(rotated))
        return item


class RandomTranslate3D:
    """Dịch ngẫu nhiên vài voxel, đệm 0 — giữ nguyên shape.

    Đây là bản tương đương của `random_crop` trong official (họ resize về 128² rồi cắt
    ngẫu nhiên 112², tức là một phép tịnh tiến). Ta giữ nguyên kích thước thay vì cắt
    nhỏ đi, nên **không phát sinh chuyện train và val khác kích thước đầu vào** — val
    đơn giản là không dịch.

    Biên độ theo z nhỏ hơn trong mặt phẳng vì voxel z dày gấp đôi (3.0mm so với 1.5mm),
    nên cùng một số voxel tương ứng với quãng đường thật lớn gấp đôi.
    """

    def __init__(self, max_shift: Sequence[int] = (8, 8, 4), prob: float = 1.0) -> None:
        self.max_shift = tuple(int(s) for s in max_shift)
        self.prob = prob

    def __call__(self, item: dict[str, Any]) -> dict[str, Any]:
        import torch

        if self.prob <= 0 or torch.rand(1).item() >= self.prob:
            return item
        if not any(self.max_shift):
            return item

        image = item["image"]
        out = torch.zeros_like(image)
        # Lát cắt nguồn và đích cho từng trục không gian: dịch dương lấy phần đầu của
        # nguồn đặt vào phần sau của đích, phần trống còn lại giữ 0.
        src: list[slice] = [slice(None)]
        dst: list[slice] = [slice(None)]
        for axis, limit in enumerate(self.max_shift, start=1):
            size = image.shape[axis]
            shift = int(torch.randint(-limit, limit + 1, (1,)).item()) if limit else 0
            shift = max(-size, min(size, shift))
            if shift >= 0:
                src.append(slice(0, size - shift))
                dst.append(slice(shift, size))
            else:
                src.append(slice(-shift, size))
                dst.append(slice(0, size + shift))
        out[tuple(dst)] = image[tuple(src)]
        item["image"] = out
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

    Khối config theo recipe official (xem `configs/baseline_3dpatch.yaml`)::

        augment:
          flip_prob: 0.5
          flip_axes: [x, y, z]
          rotate_degrees: 10
          translate_voxels: [8, 8, 4]
          rot90_prob: 0          # tắt — official không dùng
          intensity_prob: 0      # tắt — official không dùng

    `rot90` và nhiễu cường độ vẫn giữ trong module để ablate ở W4, chỉ cần bật lại
    khoá tương ứng trong config.
    """
    if not config:
        return None
    transforms: list[Callable[[dict], dict]] = []
    if config.get("flip_prob", 0):
        transforms.append(
            RandomFlip(
                prob=float(config["flip_prob"]),
                axes=resolve_axes(config.get("flip_axes")),
            )
        )
    if config.get("rotate_degrees", 0):
        transforms.append(
            RandomRotateSmall(
                degrees=float(config["rotate_degrees"]),
                prob=float(config.get("rotate_prob", 1.0)),
                order=int(config.get("rotate_order", 1)),
            )
        )
    if any(config.get("translate_voxels") or ()):
        transforms.append(
            RandomTranslate3D(
                max_shift=config["translate_voxels"],
                prob=float(config.get("translate_prob", 1.0)),
            )
        )
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
