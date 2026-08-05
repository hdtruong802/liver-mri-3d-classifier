"""ResNet-3D nạp trọng số MedicalNet, thích ứng từ 1 kênh sang 8 kênh.

## Vì sao thử pretrained

316 ca train là rất ít cho một mạng 3D train from scratch. Baseline official của
challenge cũng train from scratch và chỉ đạt 0.6083 — tức là ngưỡng đó không phải giới
hạn của kiến trúc mà một phần là giới hạn của lượng dữ liệu. MedicalNet được train
trên 23 bộ dữ liệu ảnh y tế 3D, nên đặc trưng tầng thấp (bờ, kết cấu, mạch) gần như
chắc chắn dùng lại được.

## Bài toán 1 kênh → 8 kênh, và vì sao phải CHIA

Trọng số MedicalNet dành cho ảnh **một kênh**; ta có 8 thì MRI. Conv đầu tiên có
trọng số dạng ``[C_out, 1, k, k, k]``, cần thành ``[C_out, 8, k, k, k]``.

Nhân bản trọng số ra 8 kênh là đúng hướng, nhưng **phải chia cho 8**. Conv cộng theo
chiều kênh đầu vào; nhân bản mà không chia thì tiền kích hoạt lớn gấp ~8 lần (8 thì
MRI của cùng một ca có thống kê gần nhau, không triệt tiêu nhau). Toàn bộ BatchNorm
phía sau đã học `running_mean`/`running_var` cho thang cũ, nên sai thang 8 lần làm hỏng
đúng thứ khiến pretrained có giá trị. Chia cho `C_in` giữ nguyên kỳ vọng độ lớn kích
hoạt — cùng thủ thuật "inflation" của I3D, áp cho chiều kênh thay vì chiều thời gian.

## Chế độ hỏng nguy hiểm nhất: nạp trúng 0 khoá

`load_state_dict(strict=False)` **không báo lỗi** khi không khoá nào khớp. Khi đó model
vẫn chạy, vẫn train, vẫn ra số — chỉ là nó khởi tạo ngẫu nhiên hoàn toàn, và cả thí
nghiệm "có pretrained" trở thành một thí nghiệm "không pretrained" mà không ai biết.
Vì vậy `load_medicalnet_weights` **đo tỉ lệ khoá khớp và từ chối chạy nếu quá thấp**.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

IN_CHANNELS = 8
SPATIAL_DIMS = 3

# Dưới ngưỡng này thì gần như chắc chắn sai file trọng số hoặc sai biến thể ResNet.
MIN_MATCH_FRACTION = 0.5

__all__ = ["adapt_first_conv", "build_resnet3d", "load_medicalnet_weights"]


def adapt_first_conv(weight: Any, in_channels: int) -> Any:
    """Đưa trọng số conv đầu từ 1 kênh sang `in_channels` kênh, GIỮ NGUYÊN thang.

    `weight` dạng ``[C_out, 1, kx, ky, kz]`` → ``[C_out, in_channels, kx, ky, kz]``.
    Xem docstring module về lý do chia cho `in_channels`.
    """
    if weight.ndim != 5:
        raise ValueError(f"cần trọng số conv3d 5 chiều, nhận {tuple(weight.shape)}")
    source_channels = int(weight.shape[1])
    if source_channels == in_channels:
        return weight
    if source_channels != 1:
        raise ValueError(
            f"chỉ thích ứng được từ 1 kênh, trọng số có {source_channels} kênh. "
            "Trọng số này không phải MedicalNet một kênh."
        )
    return weight.repeat(1, in_channels, 1, 1, 1) / float(in_channels)


def load_medicalnet_weights(
    model: Any,
    checkpoint_path: str | Path,
    in_channels: int = IN_CHANNELS,
    min_match: float = MIN_MATCH_FRACTION,
) -> dict[str, Any]:
    """Nạp trọng số MedicalNet vào `model`, trả về báo cáo khớp khoá.

    Trả về ``{"matched", "total", "fraction", "missing", "unexpected", "adapted_conv"}``.
    **Nổ nếu tỉ lệ khớp < `min_match`** — xem docstring module về vì sao im lặng ở đây
    là chế độ hỏng tệ nhất.
    """
    import torch

    path = Path(checkpoint_path)
    if not path.exists():
        raise FileNotFoundError(
            f"không thấy trọng số ở {path}. Trên Kaggle phải mount thành dataset "
            "(không có internet để tải lúc chạy — AGENTS.md §7)."
        )

    raw = torch.load(path, map_location="cpu")
    state = raw.get("state_dict", raw) if isinstance(raw, dict) else raw
    # MedicalNet lưu từ `nn.DataParallel` nên mọi khoá có tiền tố `module.`.
    state = {k.removeprefix("module."): v for k, v in state.items()}

    target = model.state_dict()
    adapted_conv = None
    usable: dict[str, Any] = {}
    for name, tensor in state.items():
        if name not in target:
            continue
        if tensor.shape != target[name].shape:
            # Chỉ conv đầu được phép lệch hình dạng, và chỉ ở chiều kênh vào.
            if tensor.ndim == 5 and tensor.shape[1] == 1 and target[name].shape[1] == in_channels:
                usable[name] = adapt_first_conv(tensor, in_channels)
                adapted_conv = name
            continue
        usable[name] = tensor

    missing, unexpected = model.load_state_dict(usable, strict=False)
    matched, total = len(usable), len(target)
    fraction = matched / max(total, 1)

    if fraction < min_match:
        raise ValueError(
            f"chỉ khớp {matched}/{total} khoá ({fraction:.0%}) từ {path.name} — dưới "
            f"ngưỡng {min_match:.0%}. Gần như chắc chắn sai file hoặc sai biến thể "
            "ResNet. Nạp tiếp sẽ cho một model khởi tạo ngẫu nhiên đội lốt pretrained."
        )
    if adapted_conv is None and in_channels != 1:
        raise ValueError(
            f"không tầng conv nào được thích ứng sang {in_channels} kênh. Conv đầu "
            "của model có thể đã có sẵn đúng số kênh, hoặc tên khoá không khớp — "
            "kiểm lại trước khi chạy, vì đây là chỗ pretrained dễ mất tác dụng nhất."
        )

    return {
        "matched": matched,
        "total": total,
        "fraction": fraction,
        "missing": list(missing),
        "unexpected": list(unexpected),
        "adapted_conv": adapted_conv,
    }


def build_resnet3d(
    depth: int = 18,
    in_channels: int = IN_CHANNELS,
    num_classes: int = 7,
    pretrained_path: str | None = None,
    shortcut_type: str = "B",
    bias_downsample: bool = False,
    dropout_prob: float = 0.0,
) -> Any:
    """ResNet-3D của MONAI, tuỳ chọn nạp MedicalNet.

    `shortcut_type` và `bias_downsample` phải khớp biến thể sinh ra file trọng số, nếu
    không phần lớn khoá sẽ lệch hình dạng và `load_medicalnet_weights` sẽ nổ — đó là
    hành vi mong muốn, không phải phiền toái.

    `dropout_prob` mặc định 0: ResNet của MONAI không có dropout, và MC-dropout của dự
    án (`src/eval/mc_dropout.py`) cần ít nhất một lớp Dropout để hoạt động. Đặt > 0 sẽ
    chèn dropout trước lớp phân loại.
    """
    import torch.nn as nn
    from monai.networks.nets import resnet as monai_resnet

    factory = getattr(monai_resnet, f"resnet{depth}", None)
    if factory is None:
        available = [n for n in dir(monai_resnet) if n.startswith("resnet") and n[6:].isdigit()]
        raise ValueError(f"MONAI không có resnet{depth}. Có: {sorted(available)}")

    model = factory(
        spatial_dims=SPATIAL_DIMS,
        n_input_channels=in_channels,
        num_classes=num_classes,
        shortcut_type=shortcut_type,
        bias_downsample=bias_downsample,
    )

    if pretrained_path:
        report = load_medicalnet_weights(model, pretrained_path, in_channels)
        print(
            f"MedicalNet: khớp {report['matched']}/{report['total']} khoá "
            f"({report['fraction']:.0%}), conv đầu thích ứng: {report['adapted_conv']}"
        )

    if dropout_prob > 0:
        model.fc = nn.Sequential(nn.Dropout(p=float(dropout_prob)), model.fc)
    return model
