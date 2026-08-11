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


# ---------------------------------------------------------------------------------------
# AUGMENTATION "APPEARANCE" — tái lập đội hạng 2 LLD-MMRI 2023 (NPUBXY, macro-F1 0.8078)
#
# Nguồn: https://github.com/ZHEGG/miccai2023 · `datasets/transforms.py` và
# `datasets/mp_liver_dataset.py::transforms`. `train.sh` của họ bật
# `--train_transform_list ... edge emboss filter`.
#
# ⚠️ VÌ SAO CHẨN ĐOÁN §5 KHÔNG LOẠI ĐƯỢC HỌ AUGMENTATION NÀY. AGENTS.md §5 ghi "thêm
# augmentation" đã bị loại, căn cứ là 74% lỗi trùng nhau giữa E4 và E6b. Nhưng E4/E6b chỉ khác
# augmentation **hình học** (biên độ xoay, tịnh tiến) và **scale cường độ**. Đây là họ khác
# hẳn: lọc không gian làm đổi *kết cấu* (gradient, nhấn biên, làm mờ). Chưa thí nghiệm nào của
# dự án chạm tới nó.
#
# ⚠️ BA CHỖ LỆCH SO VỚI HỌ, tất cả đều bắt buộc và đều phải ghi vào báo cáo:
#
# 1. **Thang giá trị.** Họ chuẩn hoá min-max về [0,1] rồi `emboss`/`sharpen` đi qua
#    `np.uint8(255*x)` → PIL → chia 255. Cache của ta là **z-score** (mean≈0, std≈1,
#    `src/preprocess/normalize.py`). Nên ta áp đúng kernel và đúng `scale` của PIL nhưng **bỏ
#    offset 128 và bỏ clip [0,255]** — hai thứ đó là hệ quả của việc lưu bằng uint8, không phải
#    của phép augment. Đổi lại ta cũng **không mất mát lượng tử hoá** như họ.
# 2. **RNG.** Họ dùng `random.random()`; ta dùng `torch.rand` để `set_seed` có tác dụng
#    (AGENTS.md §8). Cùng phân bố, khác nguồn.
# 3. **Vectorise.** Họ vòng lặp Python qua 8×Z lát rồi gọi cv2/PIL từng lát. Ta dùng
#    `ndimage.correlate` với kernel 4D dạng ``(1, 3, 3, 1)`` — **tương đương chính xác** một
#    phép 2D trên mặt phẳng (X, Y) cho từng (pha, lát), nhưng không có vòng lặp. `correlate`
#    chứ không `convolve`: cv2.filter2D và PIL đều KHÔNG lật kernel, mà `emboss` bất đối xứng
#    nên lật là ra kết quả khác.
# ---------------------------------------------------------------------------------------

# Kernel 3×3 của PIL `ImageFilter`, kèm `scale` — lấy từ `PIL/ImageFilter.py`. PIL tính
# ``out = sum(kernel * pixels) / scale + offset``; ta bỏ `offset` (xem ghi chú 1 ở trên).
_PIL_KERNELS_3X3: dict[str, tuple[tuple[float, ...], float]] = {
    # Kernel tổng = 0 ⇒ **xoá sạch thành phần DC**. Ảnh sau emboss không còn cường độ tuyệt
    # đối, chỉ còn nổi khối theo hướng chéo. Đây là phép mạnh nhất trong nhóm.
    "emboss": ((-1, 0, 0, 0, 1, 0, 0, 0, 0), 1.0),
    "sharpen": ((-2, -2, -2, -2, 32, -2, -2, -2, -2), 16.0),
    "detail": ((0, -1, 0, -1, 10, -1, 0, -1, 0), 10.0),
    "edge_enhance": ((-1, -1, -1, -1, 10, -1, -1, -1, -1), 2.0),
    "edge_enhance_more": ((-1, -1, -1, -1, 9, -1, -1, -1, -1), 1.0),
}

# cv2.BORDER_* → mode của scipy. BORDER_REFLECT nhân đôi voxel biên (``fedcba|abcdef``), đúng
# bằng `reflect` của scipy; BORDER_REPLICATE là `nearest`.
_SOBEL_BORDER_MODES = ("reflect", "nearest", "constant")
# Xác suất của họ: seed>0.2 REFLECT, >0.1 REPLICATE, >0.0 CONSTANT ⇒ [0.8, 0.1, 0.1].
_SOBEL_BORDER_WEIGHTS = (0.8, 0.1, 0.1)


def _plane_kernel(values: Sequence[float], scale: float = 1.0) -> Any:
    """Kernel 3×3 trong mặt phẳng (X, Y), dạng 4D ``(1, 3, 3, 1)`` để áp cho từng (pha, lát)."""
    import numpy as np

    return (np.asarray(values, dtype=np.float32).reshape(1, 3, 3, 1) / float(scale)).copy()


def sobel_magnitude(image: Any, border_mode: str = "reflect") -> Any:
    """``sqrt(Gx² + Gy²)`` trên mặt phẳng cắt ngang — bản `edge()` của họ.

    ⚠️ Phép này **thay ảnh bằng biên độ gradient của nó**, nên cường độ tuyệt đối biến mất
    hoàn toàn. Với chẩn đoán u gan — vốn dựa vào kiểu ngấm thuốc, tức cường độ *tương đối giữa
    các pha* — đây là một biến đổi rất mạnh. Họ áp nó cho **10%** mẫu train.
    """
    import numpy as np
    from scipy import ndimage

    arr = np.asarray(image, dtype=np.float32)
    gx = ndimage.correlate(arr, _plane_kernel((-1, 0, 1, -2, 0, 2, -1, 0, 1)), mode=border_mode)
    gy = ndimage.correlate(arr, _plane_kernel((-1, -2, -1, 0, 0, 0, 1, 2, 1)), mode=border_mode)
    return np.sqrt(gx * gx + gy * gy, dtype=np.float32)


def pil_kernel_filter(image: Any, name: str) -> Any:
    """Áp một kernel 3×3 của PIL (`emboss`, `sharpen`, `detail`, `edge_enhance`...).

    Biên dùng ``nearest``: PIL để nguyên hàng/cột ngoài cùng, không có mode nào của scipy khớp
    đúng điều đó, và `nearest` là xấp xỉ gần nhất. Sai lệch chỉ ở một voxel viền của khối 112².
    """
    import numpy as np
    from scipy import ndimage

    if name not in _PIL_KERNELS_3X3:
        raise ValueError(f"kernel PIL phải thuộc {sorted(_PIL_KERNELS_3X3)}, nhận {name!r}")
    values, scale = _PIL_KERNELS_3X3[name]
    arr = np.asarray(image, dtype=np.float32)
    return ndimage.correlate(arr, _plane_kernel(values, scale), mode="nearest")


def unsharp_mask(
    image: Any,
    sigma_near: float = 1.0,
    sigma_far: float = 3.0,
    amount: float = 6.0,
    spatial_only: bool = False,
) -> Any:
    """Bản `mask()` của họ: ``g₃ + amount·(g₃ − g₁)`` với gᵢ là gaussian σ=i.

    ⚠️ Đây **không phải** unsharp mask chuẩn (thường là ``x + a·(x − g)``). Họ lấy chênh giữa
    *hai* mức làm mờ rồi khuếch đại 6 lần. Giữ nguyên vì đó là recipe đã cho 0.8078.
    """
    import numpy as np
    from scipy import ndimage

    arr = np.asarray(image, dtype=np.float32)
    sig_near = _sigma_4d(sigma_near, spatial_only)
    sig_far = _sigma_4d(sigma_far, spatial_only)
    near = ndimage.gaussian_filter(arr, sigma=sig_near)
    far = ndimage.gaussian_filter(arr, sigma=sig_far)
    return (far + amount * (far - near)).astype(np.float32)


def _sigma_4d(sigma: float, spatial_only: bool) -> tuple[float, float, float, float]:
    """σ cho từng trục của khối ``[C, X, Y, Z]``.

    ⚠️ **Đây là chỗ dễ hiểu sai nhất trong cả nhóm này.** Họ gọi
    ``ndimage.gaussian_filter(image, sigma=1)`` trên mảng **4 chiều** ``[8, Z, H, W]``, và scipy
    broadcast σ ra **mọi** trục — nên nó làm mờ **cả trục pha**, tức trộn 8 pha vào nhau. Gần
    như chắc chắn là ngoài ý định của họ, nhưng nó nằm trong recipe đạt 0.8078.

    `spatial_only=False` (mặc định) tái lập đúng hành vi đó. `spatial_only=True` chỉ làm mờ
    trong không gian — một ablation **một khoá** cho giả thuyết đã tốn kém nhất của dự án
    (E6/S-102: xáo cường độ độc lập từng pha làm ICC −0.085 và di căn −0.111, vì chẩn đoán dựa
    vào cường độ *tương đối giữa các pha*).
    """
    return (0.0 if spatial_only else sigma, sigma, sigma, sigma)


class RandomAppearance:
    """Một trong các phép lọc không gian, **loại trừ nhau**, đúng cây quyết định của họ.

    `mp_liver_dataset.py::transforms` của họ:

    .. code-block:: python

        seed = random.random()
        if   seed > 0.9:  edge                      # 10%
        elif seed > 0.8:  emboss                    # 10%
        elif seed > 0.4:                            # 40% vào nhánh filter
            seed2 = random.random()
            if   seed2 > 0.8: blur                  #  8% tổng
            elif seed2 > 0.6: sharpen               #  8% tổng
            elif seed2 > 0.5: unsharp mask          #  4% tổng
            #  seed2 <= 0.5 -> KHÔNG làm gì         # 20% tổng

    Tức **60% mẫu train không bị phép nào** — nhẹ hơn nhiều so với "bật cả ba". Vì chúng loại
    trừ nhau, gộp vào **một** lớp là cách duy nhất giữ đúng phân bố; ba lớp độc lập ghép nối
    tiếp sẽ cho một phân bố khác (có mẫu bị hai phép cùng lúc).

    Mọi phép đều áp **cùng một tham số cho cả 8 pha** — đúng như họ (`seed1` vẽ **một lần**
    ngoài vòng lặp pha). Đây cũng là ràng buộc số 1 ở đầu module này.
    """

    def __init__(
        self,
        # ⚠️ Ba khoá này mặc định **0.0 = TẮT**, KHÔNG phải giá trị của repo hạng 2
        # (0.10 / 0.10 / 0.40). Giá trị trung thực nằm ở `configs/uniformer_s.yaml`.
        # Lý do: đây là hàm mà MỌI thí nghiệm của dự án đi qua, và một mặc định "bật" sẽ
        # lặng lẽ đổi hành vi của mọi config cũ — làm mọi con số cũ mất tính so sánh mà
        # không có gì báo. Tắt phải là **thuộc tính cấu trúc**, không phải quy ước của
        # người gọi. (`tests/test_appearance.py` bắt được đúng lỗi này.)
        edge_prob: float = 0.0,
        emboss_prob: float = 0.0,
        filter_prob: float = 0.0,
        # Ba khoá trong nhánh filter giữ giá trị của họ: chúng chỉ có tác dụng khi
        # `filter_prob > 0`, nên không có đường lặng lẽ bật.
        blur_prob: float = 0.20,
        sharpen_prob: float = 0.20,
        unsharp_prob: float = 0.10,
        filter_spatial_only: bool = False,
    ) -> None:
        for name, value in (
            ("edge_prob", edge_prob),
            ("emboss_prob", emboss_prob),
            ("filter_prob", filter_prob),
            ("blur_prob", blur_prob),
            ("sharpen_prob", sharpen_prob),
            ("unsharp_prob", unsharp_prob),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} phải trong [0, 1], nhận {value}")
        if edge_prob + emboss_prob + filter_prob > 1.0 + 1e-9:
            raise ValueError(
                "edge_prob + emboss_prob + filter_prob phải ≤ 1 — ba nhánh LOẠI TRỪ NHAU, "
                f"nhận {edge_prob} + {emboss_prob} + {filter_prob}"
            )
        if blur_prob + sharpen_prob + unsharp_prob > 1.0 + 1e-9:
            raise ValueError(
                "blur/sharpen/unsharp cũng loại trừ nhau trong nhánh filter, tổng phải ≤ 1"
            )
        self.edge_prob = edge_prob
        self.emboss_prob = emboss_prob
        self.filter_prob = filter_prob
        self.blur_prob = blur_prob
        self.sharpen_prob = sharpen_prob
        self.unsharp_prob = unsharp_prob
        self.filter_spatial_only = filter_spatial_only

    @property
    def enabled(self) -> bool:
        return bool(self.edge_prob or self.emboss_prob or self.filter_prob)

    def _blur(self, arr: Any) -> Any:
        """gaussian σ=1 (20%) · median size=2 (40%) · wiener size=3 (40%) — của họ."""
        import numpy as np
        import torch
        from scipy import ndimage, signal

        seed = float(torch.rand(1).item())
        if seed < 0.2:
            return ndimage.gaussian_filter(arr, sigma=_sigma_4d(1.0, self.filter_spatial_only))
        if seed < 0.6:
            size = (1, 2, 2, 2) if self.filter_spatial_only else 2
            return ndimage.median_filter(arr, size=size)
        size = (1, 3, 3, 3) if self.filter_spatial_only else 3
        # `wiener` trả về float64 và sinh NaN nếu phương sai cục bộ bằng 0 (vùng phẳng).
        return np.nan_to_num(signal.wiener(arr, mysize=size), nan=0.0).astype(np.float32)

    def _sharpen(self, arr: Any) -> Any:
        """Một trong 4 kernel nhấn biên của PIL, xác suất [0.3, 0.3, 0.2, 0.2] như họ."""
        import torch

        seed = float(torch.rand(1).item())
        if seed < 0.3:
            name = "edge_enhance_more"
        elif seed < 0.6:
            name = "edge_enhance"
        elif seed < 0.8:
            name = "detail"
        else:
            name = "sharpen"
        return pil_kernel_filter(arr, name)

    def __call__(self, item: dict[str, Any]) -> dict[str, Any]:
        import numpy as np
        import torch

        if not self.enabled:
            return item

        seed = float(torch.rand(1).item())
        arr = item["image"].numpy()

        if seed < self.edge_prob:
            mode_idx = int(torch.multinomial(torch.tensor(_SOBEL_BORDER_WEIGHTS), 1).item())
            out = sobel_magnitude(arr, _SOBEL_BORDER_MODES[mode_idx])
        elif seed < self.edge_prob + self.emboss_prob:
            out = pil_kernel_filter(arr, "emboss")
        elif seed < self.edge_prob + self.emboss_prob + self.filter_prob:
            inner = float(torch.rand(1).item())
            if inner < self.blur_prob:
                out = self._blur(arr)
            elif inner < self.blur_prob + self.sharpen_prob:
                out = self._sharpen(arr)
            elif inner < self.blur_prob + self.sharpen_prob + self.unsharp_prob:
                out = unsharp_mask(arr, spatial_only=self.filter_spatial_only)
            else:
                return item  # nhánh 50% "không làm gì" bên trong filter — của họ
        else:
            return item

        item["image"] = torch.from_numpy(np.ascontiguousarray(np.asarray(out, dtype=np.float32)))
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
    # Cuối chuỗi: lọc không gian phải chạy trên đúng khối mà model nhận, sau khi mọi phép hình
    # học đã xong. Chạy nó trước `RandomCrop3D` thì kernel liếm vào phần lề sẽ bị cắt bỏ.
    appearance = RandomAppearance(
        edge_prob=float(config.get("edge_prob", 0.0)),
        emboss_prob=float(config.get("emboss_prob", 0.0)),
        filter_prob=float(config.get("filter_prob", 0.0)),
        blur_prob=float(config.get("blur_prob", 0.20)),
        sharpen_prob=float(config.get("sharpen_prob", 0.20)),
        unsharp_prob=float(config.get("unsharp_prob", 0.10)),
        filter_spatial_only=bool(config.get("filter_spatial_only", False)),
    )
    if appearance.enabled:
        transforms.append(appearance)
    return Compose(transforms) if transforms else None
