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

# Mặc định của dự án — hiện là "batch" vì đó là lựa chọn DUY NHẤT có số thật
# (macro-F1 val 0.2725, WORKLOG S-036). InstanceNorm đã được thử và **sập**: đuôi
# DenseNet là norm5 -> relu -> global average pooling, mà InstanceNorm ép mean từng
# kênh của từng mẫu về 0 đúng cái mean pooling sẽ đọc (S-039).
#
# Nếu đổi sang "instance"/"group", PHẢI viết dạng tuple kèm affine=True: MONAI gọi
# `nn.InstanceNorm3d(num_features=C)` còn PyTorch mặc định `affine=False`, bỏ mất
# scale/shift học được ở mọi lớp norm.
DEFAULT_NORM: str | tuple[str, dict[str, Any]] = "batch"


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

    Về lựa chọn ``norm``, đây là chỗ đã sai hai lần nên ghi lại cho rõ:

    - ``batch`` — số thật duy nhất đang có (macro-F1 val 0.2725). Điểm yếu trên lý
      thuyết: batch 2 mẫu (ràng buộc VRAM của khối 3D) làm running stats rất nhiễu.
    - ``instance`` — nghe hợp lý vì nnU-Net dùng nó, nhưng **sập** ở bài toán này:
      nnU-Net làm segmentation, không có global average pooling. DenseNet thì có, và
      InstanceNorm ép mean từng kênh của từng mẫu về 0 — đúng đại lượng mà pooling
      đọc ra làm đặc trưng phân loại (WORKLOG S-039).
    - ``group`` — không có nhược điểm đó (chuẩn hoá theo *nhóm* kênh nên mean từng
      kênh vẫn khác nhau), nhưng **chưa có số**.

    Đo bằng mục 1b của notebook 03 (~30 giây/phương án) thay vì suy luận tiếp.
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
