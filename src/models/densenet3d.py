"""Baseline 3D-patch: DenseNet121-3D (MONAI), 8 pha vào như 8 kênh → 7 lớp.

Đây là **early-concat v0** của bài toán fusion: 8 pha MRI được ghép thành 8 kênh
đầu vào của một backbone 3D duy nhất. Cách này chỉ hợp lệ vì `build_cache` đã đưa
cả 8 pha về **cùng một lưới mm** — nếu không, ghép kênh sẽ trộn các vị trí giải
phẫu khác nhau (WORKLOG S-029/S-031). Các biến thể fusion tinh vi hơn
(per-phase encoder + phase-attention) là việc của W4.

Chọn DenseNet121 vì n≈500 bệnh nhân: transformer 3D quá lớn so với lượng dữ liệu
(Spec Sheet §3). `torch`/`monai` import lười để module vẫn nạp được khi chưa cài
deep-learning stack.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

IN_CHANNELS = 8  # 8 pha MRI, thứ tự theo configs/data.yaml
SPATIAL_DIMS = 3

# Mặc định của dự án. KHÔNG dùng chuỗi trần "instance": MONAI gọi
# `nn.InstanceNorm3d(num_features=C)` và PyTorch mặc định `affine=False`, nghĩa là
# mọi lớp norm mất scale/shift học được — DenseNet vốn dựa vào tham số affine của BN.
# nnU-Net cũng dùng InstanceNorm với affine=True vì lý do này.
DEFAULT_NORM: tuple[str, dict[str, Any]] = ("instance", {"affine": True})


def normalize_norm_spec(norm: str | Sequence[Any]) -> str | tuple[str, dict[str, Any]]:
    """Đưa `norm` từ YAML về dạng MONAI hiểu.

    YAML không có tuple: ``norm: [instance, {affine: true}]`` đọc ra **list**, còn
    MONAI ghi hợp đồng là ``str`` hoặc ``tuple``. Hàm này chuyển list → tuple để
    config vẫn viết được tự nhiên mà không phụ thuộc vào chuyện `split_args` của
    MONAI tình cờ unpack được list.
    """
    if isinstance(norm, str):
        return norm
    name, args = norm
    return str(name), dict(args)


def build_densenet3d(
    in_channels: int = IN_CHANNELS,
    num_classes: int = 7,
    dropout_prob: float = 0.2,
    norm: str | Sequence[Any] = DEFAULT_NORM,
) -> Any:
    """Dựng DenseNet121-3D nhận ``[B, in_channels, X, Y, Z]`` → logits ``[B, num_classes]``.

    ``norm`` mặc định là **instance (affine=True)**, không phải batch, và đây là lựa
    chọn có chủ ý. Khối 3D ``[8, 96, 96, 48]`` buộc batch phải nhỏ (2–4) vì VRAM;
    BatchNorm với batch 2 mẫu ước lượng thống kê cực nhiễu, nên running stats dùng lúc
    eval lệch hẳn so với thống kê batch dùng lúc train. Triệu chứng đã quan sát được ở
    lần chạy đầu (WORKLOG S-036): train loss giảm bình thường trong khi **val loss tăng
    30%**, dù model còn chưa fit nổi tập train. InstanceNorm không phụ thuộc kích thước
    batch — cùng lý do nnU-Net và phần lớn pipeline 3D y tế dùng nó.
    """
    from monai.networks.nets import DenseNet121

    return DenseNet121(
        spatial_dims=SPATIAL_DIMS,
        in_channels=in_channels,
        out_channels=num_classes,
        dropout_prob=dropout_prob,
        norm=normalize_norm_spec(norm),
    )


def count_parameters(model: Any) -> int:
    """Số tham số huấn luyện được — log ra để đối chiếu giữa các biến thể."""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)
