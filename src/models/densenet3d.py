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

from typing import Any

IN_CHANNELS = 8  # 8 pha MRI, thứ tự theo configs/data.yaml
SPATIAL_DIMS = 3


def build_densenet3d(
    in_channels: int = IN_CHANNELS,
    num_classes: int = 7,
    dropout_prob: float = 0.2,
) -> Any:
    """Dựng DenseNet121-3D nhận ``[B, in_channels, X, Y, Z]`` → logits ``[B, num_classes]``."""
    from monai.networks.nets import DenseNet121

    return DenseNet121(
        spatial_dims=SPATIAL_DIMS,
        in_channels=in_channels,
        out_channels=num_classes,
        dropout_prob=dropout_prob,
    )


def count_parameters(model: Any) -> int:
    """Số tham số huấn luyện được — log ra để đối chiếu giữa các biến thể."""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)
