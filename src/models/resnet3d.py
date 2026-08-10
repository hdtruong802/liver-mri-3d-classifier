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

import os
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

from src.models.densenet3d import normalize_norm_spec

IN_CHANNELS = 8
SPATIAL_DIMS = 3

# Dưới ngưỡng này thì gần như chắc chắn sai file trọng số hoặc sai biến thể ResNet.
MIN_MATCH_FRACTION = 0.5

# Đầu phân loại là khoá DUY NHẤT được phép thiếu: MedicalNet là model segmentation
# (`conv_seg`), không có `fc`, và 7 lớp của ta cũng không nhận được đầu cũ dù có.
CLASSIFIER_PREFIX = "fc."

# Biến thể ResNet sinh ra từng file trọng số MedicalNet. KHÔNG tự chọn được — lấy từ
# `monai.networks.nets.resnet.get_medicalnet_pretrained_resnet_args`, và khớp với
# README của Tencent/MedicalNet ("resnet_18_23dataset.pth ... resnet_shortcut A").
#
# Vì sao bảng này phải tồn tại thay vì để người viết config tự điền: shortcut "A" là
# avg-pool cộng đệm 0 và **không có tham số nào**, còn "B" dựng thêm conv 1×1 + norm ở
# ba chỗ nối tầng. Đặt "B" cho resnet18 thì ~18 khoá không có đối tác trong file trọng
# số và khởi tạo ngẫu nhiên, trong khi tỉ lệ khớp vẫn báo ~85% — dư sức qua ngưỡng 50%.
# Đó là lý do `load_medicalnet_weights` kiểm theo *khoá nào thiếu*, không chỉ theo tỉ lệ.
MEDICALNET_ARGS: dict[int, tuple[str, bool]] = {
    10: ("B", False),
    18: ("A", True),
    34: ("A", True),
    50: ("B", False),
    101: ("B", False),
    152: ("B", False),
    200: ("B", False),
}

__all__ = [
    "MEDICALNET_ARGS",
    "adapt_first_conv",
    "build_resnet3d",
    "load_medicalnet_weights",
    "medicalnet_args",
    "resolve_pretrained_path",
    "unexpected_missing_keys",
]


def medicalnet_args(depth: int) -> tuple[str, bool]:
    """``(shortcut_type, bias_downsample)`` bắt buộc cho trọng số MedicalNet độ sâu này."""
    if depth not in MEDICALNET_ARGS:
        raise ValueError(f"MedicalNet không có resnet{depth}. Có: {sorted(MEDICALNET_ARGS)}")
    return MEDICALNET_ARGS[depth]


def unexpected_missing_keys(missing: Iterable[str]) -> list[str]:
    """Khoá bị thiếu mà KHÔNG phải đầu phân loại, tức dấu hiệu lệch kiến trúc.

    Tách ra thành hàm thuần để test được mà không cần torch: đây là cổng chặn thật,
    và một cổng chặn không có test thì hỏng thầm lặng đúng lúc không ai nhìn.
    """
    return sorted(k for k in missing if not k.startswith(CLASSIFIER_PREFIX))


def resolve_pretrained_path(value: str | Path | None) -> Path | None:
    """Đường dẫn trọng số: env ``LLDMMRI_PRETRAINED_PATH`` thắng, sau đó config.

    Cùng quy ước với ``LLDMMRI_CACHE_DIR``/``LLDMMRI_OUTPUT_DIR``. Config **không nên**
    ghi cứng đường dẫn mount: Kaggle để dataset ở ``/kaggle/input/datasets/<user>/<slug>/``
    chứ không phải ``/kaggle/input/<slug>/``, và giả định về hình dạng đường dẫn đó là
    lớp lỗi đã phải sửa bốn lần (WORKLOG S-081 → S-084).
    """
    env = os.environ.get("LLDMMRI_PRETRAINED_PATH")
    if env:
        return Path(env)
    return Path(value) if value else None


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

    # Cổng thật nằm ở ĐÂY, không ở `min_match`. Tỉ lệ khớp là đại lượng thô: đặt
    # `shortcut_type: B` cho resnet18 (đúng ra phải là "A") vẫn cho ~85% vì "B" chỉ
    # thêm conv+norm ở ba chỗ nối tầng. Ba chỗ đó nằm trên đường tắt của 3/4 stage,
    # khởi tạo ngẫu nhiên, và không có gì trong kết quả tố cáo điều đó.
    unexpected_missing = unexpected_missing_keys(missing)
    if unexpected_missing:
        raise ValueError(
            f"{len(unexpected_missing)} khoá của model KHÔNG có đối tác trong "
            f"{path.name} và không thuộc đầu phân loại — kiến trúc dựng ra không phải "
            f"biến thể sinh ra file trọng số này. Tỉ lệ khớp {fraction:.0%} nên ngưỡng "
            f"{min_match:.0%} không bắt được.\n"
            f"  Kiểm `shortcut_type`/`bias_downsample`: MedicalNet resnet18/34 cần "
            f"('A', True), các độ sâu khác cần ('B', False).\n"
            f"  Thiếu (10 khoá đầu): {unexpected_missing[:10]}"
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
    conv1_stride: int | Sequence[int] = 1,
    norm: str | Sequence[Any] = "batch",
) -> Any:
    """ResNet-3D của MONAI, tuỳ chọn nạp MedicalNet.

    `norm` tồn tại ở đây vì mọi config của dự án đều mang khoá đó (kế thừa từ
    `baseline_3dpatch.yaml`), và một tham số bị *bỏ qua âm thầm* thì tệ hơn một tham
    số không tồn tại. **Với trọng số MedicalNet chỉ `batch` là hợp lệ**: checkpoint
    mang `running_mean`/`running_var` của BatchNorm, đổi sang norm khác thì những khoá
    đó không còn đối tác và một phần thống kê đã học biến mất.

    `shortcut_type` và `bias_downsample` phải khớp biến thể sinh ra file trọng số.
    Khi có `pretrained_path`, hàm này **đối chiếu với `MEDICALNET_ARGS` và từ chối
    chạy nếu lệch**, thay vì để lỗi trôi xuống lớp nạp trọng số: sai cặp này không
    làm hỏng hình dạng khoá nào, nó chỉ khiến một phần mạng lặng lẽ ngẫu nhiên.

    `dropout_prob` mặc định 0: ResNet của MONAI không có dropout, và MC-dropout của dự
    án (`src/eval/mc_dropout.py`) cần ít nhất một lớp Dropout để hoạt động. Đặt > 0 sẽ
    chèn dropout trước lớp phân loại.

    ## `conv1_stride` — và ba chỗ MONAI khác Med3D mà trọng số vẫn nạp được

    Mạng sinh ra file trọng số (Tencent/MedicalNet, `models/resnet.py`) là mạng
    **segmentation**, và nó khác ResNet phân loại của MONAI ở ba chỗ::

                     Med3D (nơi trọng số được học)   MONAI mặc định
        conv1        stride (2, 2, 2)                stride (1, 1, 1)
        layer3       stride 1, dilation 2            stride 2, dilation 1
        layer4       stride 1, dilation 4            stride 2, dilation 1

    **Không chỗ nào trong ba chỗ đó đổi hình dạng trọng số**, nên chúng nạp trót lọt và
    tỉ lệ khớp vẫn ~97%. Nhưng mọi bộ lọc ở layer3/layer4 được học để nhìn một trường
    tiếp nhận *giãn* ở độ phân giải cao, còn ở đây chúng nhìn trường đặc ở 1/4 độ phân
    giải. Đây là giới hạn cố hữu của việc dùng trọng số segmentation cho backbone phân
    loại; MONAI cũng chấp nhận đúng như vậy ở đường `pretrained=True` của họ, và
    `_make_layer` của MONAI không nhận `dilation` nên **không khớp lại được**.

    Hệ quả cho việc đọc kết quả: E8 null thì "pretrained không giúp" *không phải* lời
    giải thích duy nhất. Phải ghi điều này vào báo cáo.

    Chỗ duy nhất chỉnh được là `conv1_stride`, và nó cũng là chỗ đắt nhất:

    - ``1`` (mặc định MONAI) — nhân 7×7×7 chạy ở nguyên độ phân giải đầu vào. Riêng
      tầng này nặng hơn cả phần thân mạng. Với khối 112×112×32 thì bản đồ cuối là
      7×7×2, hợp với dữ liệu mỏng theo z của dự án.
    - ``[1, 2, 2]`` — hạ mẫu trong mặt phẳng như Med3D, **giữ nguyên trục z**. Rẻ hơn
      4 lần, bản đồ cuối 4×4×2. Đây là phương án đáng thử nếu cổng ngân sách báo GPU
      thành nút thắt.
    - ``2`` — khớp Med3D hoàn toàn, nhưng z 32 voxel bị hạ mẫu 32 lần còn **đúng 1
      lát**, mất sạch cấu trúc theo z ở block cuối. Không nên dùng với hình học này.
    """
    import torch.nn as nn
    from monai.networks.nets import resnet as monai_resnet

    factory = getattr(monai_resnet, f"resnet{depth}", None)
    if factory is None:
        available = [n for n in dir(monai_resnet) if n.startswith("resnet") and n[6:].isdigit()]
        raise ValueError(f"MONAI không có resnet{depth}. Có: {sorted(available)}")

    norm_spec = normalize_norm_spec(norm)

    weights = resolve_pretrained_path(pretrained_path)
    if weights is not None:
        if norm_spec != "batch":
            raise ValueError(
                f"norm={norm!r} không dùng được với trọng số MedicalNet. Checkpoint mang "
                "running_mean/running_var của BatchNorm; đổi norm thì những khoá đó mất "
                "đối tác và một phần thống kê đã học biến mất — trong khi tỉ lệ khớp vẫn "
                "trông cao. Đổi norm là một thí nghiệm riêng, chạy from-scratch."
            )
        need = medicalnet_args(depth)
        got = (str(shortcut_type), bool(bias_downsample))
        if got != need:
            raise ValueError(
                f"resnet{depth} + trọng số MedicalNet cần shortcut_type={need[0]!r}, "
                f"bias_downsample={need[1]}, nhận {got[0]!r}/{got[1]}. Sai cặp này KHÔNG "
                "làm hỏng hình dạng khoá nào — nó chỉ để một phần mạng khởi tạo ngẫu "
                "nhiên trong khi tỉ lệ khớp vẫn trông cao."
            )

    stride = (
        int(conv1_stride) if isinstance(conv1_stride, int) else tuple(int(s) for s in conv1_stride)
    )
    model = factory(
        spatial_dims=SPATIAL_DIMS,
        n_input_channels=in_channels,
        num_classes=num_classes,
        shortcut_type=shortcut_type,
        bias_downsample=bias_downsample,
        conv1_t_stride=stride,
        norm=norm_spec,
    )

    if weights is not None:
        report = load_medicalnet_weights(model, weights, in_channels)
        print(
            f"MedicalNet: khớp {report['matched']}/{report['total']} khoá "
            f"({report['fraction']:.0%}), conv đầu thích ứng: {report['adapted_conv']}, "
            f"thiếu {len(report['missing'])} khoá (đầu phân loại)"
        )
    else:
        print(
            "⚠ KHÔNG có trọng số pretrained (config trống và LLDMMRI_PRETRAINED_PATH "
            "chưa đặt) — đang train FROM SCRATCH. Đây là phép so kiến trúc, không phải "
            "phép thử pretrained."
        )

    if dropout_prob > 0:
        model.fc = nn.Sequential(nn.Dropout(p=float(dropout_prob)), model.fc)
    return model
