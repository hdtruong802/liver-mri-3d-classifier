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

    def __init__(
        self,
        degrees: float = 10.0,
        prob: float = 1.0,
        order: int = 1,
        mode: str = "constant",
    ) -> None:
        self.degrees = degrees
        self.prob = prob
        self.order = order
        # `mode` quyết định lấp gì vào góc sau khi xoay.
        #
        # `constant` (mặc định, giữ hành vi của E0..E6b): lấp 0. Đo được là ~100% mẫu
        # train mang dải đen ở rìa còn mẫu val thì không — chính lệch phân bố mà E12
        # sinh ra để sửa.
        #
        # `nearest`: nhân bản voxel biên. Với cache có lề dư, đo trên khối 136 xoay
        # ±10° rồi cắt 112 ở mọi offset: `constant` để lọt tới **517** voxel bị lấp ở
        # offset biên, `nearest` để lọt **0**. Cắt giữa thì cả hai đều sạch, nên chỉ
        # `nearest` mới an toàn khi cắt NGẪU NHIÊN.
        self.mode = mode

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
            mode=self.mode,
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


class _Crop3D:
    """Nền chung cho cắt khối: kiểm kích thước, cắt theo offset do lớp con quyết."""

    def __init__(self, size: Sequence[int]) -> None:
        self.size = tuple(int(s) for s in size)
        if len(self.size) != 3 or any(s <= 0 for s in self.size):
            raise ValueError(f"size phải là 3 số dương, nhận {size!r}")

    def _offsets(self, room: tuple[int, int, int]) -> tuple[int, int, int]:
        raise NotImplementedError

    def __call__(self, item: dict[str, Any]) -> dict[str, Any]:
        image = item["image"]
        shape = tuple(int(s) for s in image.shape[1:])
        room = tuple(d - o for d, o in zip(shape, self.size, strict=True))
        if any(r < 0 for r in room):
            raise ValueError(
                f"{type(self).__name__}: khối vào {shape} nhỏ hơn kích thước cắt "
                f"{self.size}. Cache này không có lề dư — dùng cache build với "
                f"`crop_margin_voxels`, hoặc bỏ `data.crop_size` khỏi config."
            )
        start = self._offsets(room)  # type: ignore[arg-type]
        item["image"] = image[
            :,
            start[0] : start[0] + self.size[0],
            start[1] : start[1] + self.size[1],
            start[2] : start[2] + self.size[2],
        ]
        return item


class RandomCrop3D(_Crop3D):
    """Cắt ngẫu nhiên một khối `size` từ khối lớn hơn. **Không bao giờ đệm.**

    Đây là bản thay cho `RandomTranslate3D`, và khác biệt không nằm ở biên độ mà ở
    chỗ **lấy mô thật thay vì đệm 0**.

    `RandomTranslate3D` dịch ảnh rồi lấp phần trống bằng 0, nên gần như **100% mẫu
    train mang một dải đen ở rìa trong khi 0% mẫu val có nó** — một lệch phân bố
    train/val có hệ thống, xuất hiện ở mọi bước huấn luyện. Cắt từ cache có lề dư
    xoá hẳn dải đó: mọi voxel trong khối ra đều là mô đã đo được.

    Đây cũng là đúng cách của baseline official (resize 128² rồi cắt 112²) và của
    CGHNet (16×128×128 → 14×112×112). Ablation của CGHNet (Bảng 4) cho thấy bỏ
    random-crop mất **8,8 điểm**, là biến augmentation nặng nhất trong bảng của họ.

    ⚠️ Phải đặt **sau** `RandomRotateSmall` trong chuỗi. Phép xoay lấp góc bằng 0
    (`cval=0.0`); xoay trên khối lớn rồi mới cắt thì phần lấp đó nằm ngoài khối ra.
    Cắt trước rồi xoay sau sẽ đưa dải đen trở lại đúng thứ transform này xoá đi.
    """

    def _offsets(self, room: tuple[int, int, int]) -> tuple[int, int, int]:
        import torch

        return tuple(int(torch.randint(0, r + 1, (1,)).item()) if r else 0 for r in room)  # type: ignore[return-value]


class CenterCrop3D(_Crop3D):
    """Cắt giữa, tất định. Dùng cho val/test để đầu vào không phụ thuộc may rủi.

    Với lề dư chẵn, khối ra trùng đúng khối mà cache không-lề sẽ tạo ra (cùng tâm,
    cùng spacing). Nhờ vậy val của cache có lề **so trực tiếp được** với val của
    cache cũ, và phép so E12 với E4 chỉ khác đúng một biến: augmentation lúc train.
    """

    def _offsets(self, room: tuple[int, int, int]) -> tuple[int, int, int]:
        return tuple(r // 2 for r in room)  # type: ignore[return-value]


class Compose:
    """Chuỗi transform áp lần lượt lên item."""

    def __init__(self, transforms: Sequence[Callable[[dict], dict]]) -> None:
        self.transforms = list(transforms)

    def __call__(self, item: dict[str, Any]) -> dict[str, Any]:
        for transform in self.transforms:
            item = transform(item)
        return item


def build_val_transform(crop_size: Sequence[int] | None) -> Compose | None:
    """Transform cho val/test: chỉ cắt giữa, tất định. ``None`` khi cache không có lề.

    Val **không** được augment. Thứ duy nhất cần ở đây là đưa khối cache có lề dư
    về đúng kích thước đầu vào của model, và làm việc đó một cách tất định để hai
    lần chạy cho cùng kết quả.
    """
    if not crop_size:
        return None
    return Compose([CenterCrop3D(crop_size)])


def build_train_transform(
    config: dict[str, Any] | None, crop_size: Sequence[int] | None = None
) -> Compose | None:
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

    `crop_size` (từ ``data.crop_size``) bật chế độ **cắt ngẫu nhiên từ cache có lề
    dư** thay cho tịnh tiến-đệm-0. Nó được chèn **sau** phép xoay, vì xoay lấp góc
    bằng 0 và phép cắt sau đó vứt bỏ đúng phần lấp ấy. ``None`` = giữ hành vi cũ.
    """
    config = config or {}
    if crop_size and any(config.get("translate_voxels") or ()):
        raise ValueError(
            "bật cùng lúc `crop_size` và `translate_voxels` là nhân đôi phép dịch, "
            "và `RandomTranslate3D` sẽ đệm 0 trở lại đúng thứ `RandomCrop3D` vừa xoá. "
            "Dùng cache có lề dư thì đặt `translate_voxels: [0, 0, 0]`."
        )
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
                mode=str(config.get("rotate_mode", "constant")),
            )
        )
    # Sau xoay, trước mọi thứ còn lại: phần góc bị xoay lấp 0 nằm ngoài khối ra.
    if crop_size:
        transforms.append(RandomCrop3D(crop_size))
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
