"""Siamese đa pha: **một encoder dùng chung** chạy riêng cho từng thì, rồi hợp nhất.

Đây là bước v1 của trục fusion trong Spec Sheet §3, thay cho early-concat v0
(`src/models/densenet3d.py`, 8 pha vào như 8 kênh).

**Vì sao đổi.** Bảng 1 của SDR-Former (Lou và cs., arXiv:2402.17246) cho thấy bọc
một backbone vào Siamese Neural Network nâng macro-F1 trên **cả sáu** backbone họ
thử, cùng dataset MR 8 pha::

    backbone        image-level   Siamese    hiệu
    ResNet-50          0.6898     0.7168    +0.027
    DenseNet-121       0.7171     0.7394    +0.022
    MCSCNN             0.7089     0.7409    +0.032
    BoTNet-50          0.7139     0.7572    +0.043
    UniFormer-S        0.7123     0.7639    +0.052
    H2Former           0.7342     0.7745    +0.040
    SDR-Former (đủ bộ)             0.7910   <- +0.027 nữa cho DR-Former + BCIM + APSM

Trung bình +0.036, và transformer hưởng lợi hơn CNN (+0.045 so với +0.027).

⚠️ **ĐÍNH CHÍNH 2026-08-17 (đã đọc bài gốc).** Bản trước của docstring này viết
*"+0.074 chỉ do đổi sang SNN"*, lấy hiệu giữa ``ResNet-50`` (0.6898) và
``SNN-UniFormer-S`` (0.7639). **Sai** — hai hàng đó khác nhau **cả backbone lẫn
fusion**, nên con số ấy gộp hai biến. Hiệu một biến thật nằm trong khoảng
**+0.022 đến +0.052**. Đừng trích con số cũ.

✅ Phần *nghi ngờ* của bản trước thì **đã giải quyết được**: §5.1 nói thẳng rằng các
hàng ``SNN-*`` là chính những backbone đó *"integrated into the SDR-Former's
weight-sharing network framework"*. Suy luận từ quy ước đặt tên là đúng.

⚠️ Một đính chính nữa: bản trước viết *"hạng 2 của challenge dùng ResNet18"*. Sai —
hạng 2 (`NPUBXY`) dùng **UniFormer-S + trọng số Kinetics**; xem AGENTS.md §5 và
``configs/uniformer_s.yaml``.

**Bản tái lập đầy đủ SDR-Former nằm ở** ``src/models/sdrformer.py``. Module này là
bản Siamese *tối giản* (một scalar mỗi thì, trên vector đã pool); bản kia có APSM
cho trọng số riêng **từng kênh**, hai độ phân giải, và BCIM nối hai nhánh.

**Vì sao dùng chung trọng số.** 316 mẫu train. Tám encoder riêng là tám lần số
tham số và gần như chắc chắn overfit. Dùng chung trọng số giữ nguyên số tham số
so với early-concat, và ép model học một bộ đặc trưng tổn thương *bất biến theo
thì* — thứ có nghĩa lâm sàng, vì cùng một tổn thương phải là cùng một vật thể ở
cả 8 thì.

**Hệ quả: mất danh tính thì.** Trọng số dùng chung nên encoder không phân biệt
được arterial với T2WI. Đó là lý do có `phase_embedding`: một vector học được
cho mỗi thì, cộng vào đặc trưng của thì đó. Không có nó, fusion kiểu ``mean``
hoàn toàn không biết thứ tự thì, mà động học ngấm thuốc (arterial
hyperenhancement, washout theo LI-RADS) chính là tín hiệu chẩn đoán mạnh nhất.

**Chi phí tính toán, đọc kỹ trước khi chạy.** Backbone chạy 8 lượt thay vì 1 nên
FLOPs tăng ~8 lần: chỉ tầng conv đầu khác nhau giữa 1 kênh và 8 kênh, còn toàn
bộ thân mạng giống hệt. E1 mất 4.09h/fold, nên E2 nguyên bản sẽ khoảng 30h+ —
vượt xa cả session 12h lẫn quota tuần. Xem `input_downsample`.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from src.models.densenet3d import DEFAULT_NORM, SPATIAL_DIMS, normalize_norm_spec

NUM_PHASES = 8  # thứ tự theo configs/data.yaml
FUSIONS = ("attention", "mean", "concat")
ENCODERS = ("densenet121_3d", "resnet3d")

# DenseNet121-3D hạ mẫu 5 lần: conv0 /2, pool0 /2, rồi ba transition mỗi cái /2.
# Transition thứ ba dùng `AvgPool3d(kernel_size=2)`, nên đầu vào của nó phải ≥ 2 ở
# MỌI chiều — tức kích thước đưa vào encoder phải ≥ 32 ở mọi chiều. Dưới ngưỡng đó,
# MONAI ném `RuntimeError: input image ... smaller than kernel size` từ sâu trong
# mạng, không nói gì về nguyên nhân thật (WORKLOG S-063).
MIN_SPATIAL = 32

# ResNet-3D hạ mẫu 16 lần với `conv1_stride=1` (maxpool /2, rồi layer2/3/4 mỗi cái /2)
# và kết thúc bằng adaptive average pooling, nên chỉ cần mỗi chiều còn ≥ 1 voxel.
# Ngưỡng của DenseNet **không** áp cho nhánh này; dùng chung một hằng số là chỗ đã
# buộc E2 phải hạ mẫu xuống 48 in-plane và làm hỏng cả thí nghiệm (WORKLOG S-065).
MIN_SPATIAL_RESNET = 16

# Số chiều đặc trưng sau adaptive-pool của ResNet-3D, bằng ``block_inplanes[3] *
# expansion``. BasicBlock (resnet10/18/34) expansion 1; Bottleneck (50+) expansion 4.
RESNET_FEATURE_DIM: dict[int, int] = {10: 512, 18: 512, 34: 512, 50: 2048, 101: 2048}


def resnet_feature_dim(depth: int) -> int:
    """Số chiều đặc trưng của ResNet-3D độ sâu này khi chạy ``feed_forward=False``."""
    if depth not in RESNET_FEATURE_DIM:
        raise ValueError(f"chưa biết số chiều của resnet{depth}. Có: {sorted(RESNET_FEATURE_DIM)}")
    return RESNET_FEATURE_DIM[depth]


def build_shared_encoder(
    encoder: str,
    depth: int,
    feature_dim: int,
    dropout_prob: float,
    norm: str | Sequence[Any],
    shortcut_type: str,
    bias_downsample: bool,
    pretrained_path: str | None,
    conv1_stride: int | Sequence[int],
) -> Any:
    """Dựng encoder **một kênh** dùng chung cho cả 8 thì.

    Nhánh resnet nạp trọng số MedicalNet bằng đúng lớp kiểm đã có ở
    `src/models/resnet3d.py`. Hai điểm khác hẳn early-concat của E8, và cả hai đều là
    lợi thế:

    1. ``in_channels=1`` nên `adapt_first_conv` **không phải làm gì** — conv đầu được
       dùng đúng như lúc nó được học, không nhân bản ra 8 kênh rồi chia cho 8.
    2. ``feed_forward=False`` nên encoder không có `fc`, tức **không khoá nào bị
       thiếu**. Cổng `unexpected_missing_keys` vì thế đòi khớp *tuyệt đối*, chặt hơn
       trường hợp early-concat (ở đó `fc.*` được miễn).
    """
    from monai.networks.nets import DenseNet121

    if encoder == "densenet121_3d":
        return DenseNet121(
            spatial_dims=SPATIAL_DIMS,
            in_channels=1,
            out_channels=feature_dim,
            dropout_prob=dropout_prob,
            norm=normalize_norm_spec(norm),
        )

    from monai.networks.nets import resnet as monai_resnet

    from src.models.resnet3d import (
        load_medicalnet_weights,
        medicalnet_args,
        resolve_pretrained_path,
    )

    norm_spec = normalize_norm_spec(norm)
    weights = resolve_pretrained_path(pretrained_path)
    if weights is not None:
        if norm_spec != "batch":
            raise ValueError(
                f"norm={norm!r} không dùng được với trọng số MedicalNet — checkpoint mang "
                "running_mean/running_var của BatchNorm."
            )
        need = medicalnet_args(depth)
        got = (str(shortcut_type), bool(bias_downsample))
        if got != need:
            raise ValueError(
                f"resnet{depth} + trọng số MedicalNet cần shortcut_type={need[0]!r}, "
                f"bias_downsample={need[1]}, nhận {got[0]!r}/{got[1]}."
            )

    factory = getattr(monai_resnet, f"resnet{depth}", None)
    if factory is None:
        raise ValueError(f"MONAI không có resnet{depth}")

    stride = (
        int(conv1_stride) if isinstance(conv1_stride, int) else tuple(int(s) for s in conv1_stride)
    )
    module = factory(
        spatial_dims=SPATIAL_DIMS,
        n_input_channels=1,
        shortcut_type=shortcut_type,
        bias_downsample=bias_downsample,
        conv1_t_stride=stride,
        norm=norm_spec,
        # Bỏ lớp phân loại: ta cần ĐẶC TRƯNG, còn phần phân loại nằm ở `head` sau khi
        # hợp nhất 8 thì. MONAI đặt `self.fc = None` và `forward` trả về vector đã
        # flatten sau adaptive-pool.
        feed_forward=False,
    )

    if weights is None:
        print(
            "⚠ encoder Siamese KHÔNG có trọng số pretrained (config trống và "
            "LLDMMRI_PRETRAINED_PATH chưa đặt) — đang train FROM SCRATCH."
        )
        return module

    report = load_medicalnet_weights(module, weights, in_channels=1)
    print(
        f"MedicalNet -> encoder Siamese: khớp {report['matched']}/{report['total']} khoá "
        f"({report['fraction']:.0%}), thiếu {len(report['missing'])} khoá, "
        f"conv đầu KHÔNG cần thích ứng (1 kênh) · đặc trưng {feature_dim} chiều"
    )
    return module


def build_siamese_fusion(
    num_phases: int = NUM_PHASES,
    num_classes: int = 7,
    embed_dim: int | None = None,
    fusion: str = "attention",
    dropout_prob: float = 0.2,
    norm: str | Sequence[Any] = DEFAULT_NORM,
    phase_embedding: bool = True,
    input_downsample: int | Sequence[int] = (2, 2, 1),
    encoder: str = "densenet121_3d",
    encoder_depth: int = 18,
    shortcut_type: str = "A",
    bias_downsample: bool = True,
    pretrained_path: str | None = None,
    conv1_stride: int | Sequence[int] = 1,
) -> Any:
    """Dựng mạng Siamese đa pha nhận ``[B, num_phases, X, Y, Z]`` → logits ``[B, num_classes]``.

    Tham số:
        embed_dim: số chiều đặc trưng mỗi thì. Lấy thẳng từ ``out_channels`` của
            DenseNet121 (API công khai), không đụng vào nội tại của MONAI.
        fusion: cách gộp 8 vector đặc trưng.

            - ``attention`` — chấm điểm từng thì rồi softmax trên trục thì. Trả
              thêm **trọng số từng thì**, dùng được luôn cho ablation
              phase-importance ở W4 và để đối chiếu với LI-RADS.
            - ``mean`` — trung bình. Đơn giản nhất, dùng làm mốc so.
            - ``concat`` — nối 8 vector. Giữ danh tính thì mà không cần
              `phase_embedding`, đổi lại tầng phân loại to gấp 8.

        input_downsample: hệ số average-pool đặt **trước** encoder. Một số cho cả
            ba trục, hoặc ba số ``(x, y, z)``.

            Mặc định ``(2, 2, 1)``: **chỉ hạ mẫu trong mặt phẳng, giữ nguyên trục
            Z**. Hạ mẫu đều ``2`` nghe hợp lý nhưng **sập trên dữ liệu thật**:
            96×96×48 thành 48×48×24, và 24 không sống nổi qua 5 lần hạ mẫu của
            DenseNet (WORKLOG S-063). Trục Z chỉ có 48 voxel ngay từ đầu, không
            còn gì để cắt.

            Vì sao hạ mẫu trong mặt phẳng thì an toàn: cache lesion-tight có trung
            vị fov 53.8mm trên 96 voxel, tức ~0.56mm/voxel, trong khi pha động chỉ
            có độ phân giải gốc ~0.78mm (WORKLOG S-029) — khoảng một nửa dataset
            **đang được nội suy vượt quá** thứ máy chụp ghi được. Cắt đôi trong mặt
            phẳng chỉ trả lại phần nội suy đó.

            Chi phí: ``(2, 2, 1)`` giảm voxel **4 lần**, không phải 8. Với 8 lượt
            forward, E2 tốn khoảng **2× E1**, tức ~8h/fold. Vẫn lọt session 12h.

            ⚠️ Đây là **biến gây nhiễu**: E2 so với E1 là so *Siamese ở nửa độ phân
            giải trong mặt phẳng* với *early-concat ở đủ độ phân giải*, không phải
            so thuần kiến trúc. E2 thắng thì kết luận mạnh (thắng dù bị thiệt). E2
            thua thì **không kết luận được**, phải chạy thêm E1 với cùng
            ``input_downsample`` làm đối chứng.

        encoder: backbone dùng chung cho 8 thì.

            - ``densenet121_3d`` — bản gốc của E2. Hạ mẫu 5 lần nên buộc mọi chiều
              đưa vào phải ≥ 32, và chính ràng buộc đó đẩy E2 xuống 48 in-plane.
            - ``resnet3d`` — hạ mẫu 16 lần rồi adaptive-pool, nên **chạy được ở đủ
              112×112×32 mà không cần `input_downsample`**. Đây là biến thể duy nhất
              có trọng số MedicalNet, và nó khớp Siamese một cách tự nhiên: trọng số
              đó dành cho ảnh **một kênh**, mà ở chế độ Siamese encoder cũng nhìn
              đúng một thì mỗi lượt. Không phải nhân bản conv đầu ra 8 kênh rồi chia
              cho 8 như early-concat buộc phải làm (`src/models/resnet3d.py`).

        embed_dim: số chiều đặc trưng mỗi thì.

            ``None`` nghĩa là *suy từ encoder*: 256 cho DenseNet121 (giá trị E2 đã
            dùng), 512 cho ResNet18. Với nhánh resnet đây **không phải** tham số tự
            do — encoder chạy `feed_forward=False` nên số chiều do kiến trúc quyết
            định, và truyền một giá trị khác vào sẽ bị từ chối thay vì bỏ qua âm thầm.

        pretrained_path: trọng số MedicalNet cho nhánh resnet. Để trống thì đọc env
            ``LLDMMRI_PRETRAINED_PATH``; không có cả hai thì train from scratch và in
            cảnh báo. `shortcut_type`/`bias_downsample` bị đối chiếu với
            `MEDICALNET_ARGS` và từ chối chạy nếu lệch.
    """
    # Kiểm tham số TRƯỚC khi import: cấu hình sai phải báo lỗi ngay cả trên máy
    # chưa cài deep-learning stack, để `pytest` ở local vẫn bắt được lỗi config.
    if fusion not in FUSIONS:
        raise ValueError(f"fusion phải thuộc {FUSIONS}, nhận {fusion!r}")
    if encoder not in ENCODERS:
        raise ValueError(f"encoder phải thuộc {ENCODERS}, nhận {encoder!r}")
    factors = (
        (int(input_downsample),) * 3
        if isinstance(input_downsample, int)
        else tuple(int(f) for f in input_downsample)
    )
    if len(factors) != 3 or any(f < 1 for f in factors):
        raise ValueError(f"input_downsample phải là 1 số hoặc 3 số >= 1, nhận {input_downsample!r}")

    # Số chiều đặc trưng: với resnet nó do kiến trúc quyết định, không phải lựa chọn.
    if encoder == "resnet3d":
        derived = resnet_feature_dim(encoder_depth)
        if embed_dim is not None and int(embed_dim) != derived:
            raise ValueError(
                f"encoder resnet{encoder_depth} chạy feed_forward=False nên đặc trưng "
                f"cố định {derived} chiều, không nhận embed_dim={embed_dim}. Bỏ khoá "
                "`embed_dim` khỏi config."
            )
        feature_dim = derived
        min_spatial = MIN_SPATIAL_RESNET
    else:
        feature_dim = 256 if embed_dim is None else int(embed_dim)
        min_spatial = MIN_SPATIAL

    import torch
    from torch import nn

    shared_encoder = build_shared_encoder(
        encoder=encoder,
        depth=encoder_depth,
        feature_dim=feature_dim,
        dropout_prob=dropout_prob,
        norm=norm,
        shortcut_type=shortcut_type,
        bias_downsample=bias_downsample,
        pretrained_path=pretrained_path,
        conv1_stride=conv1_stride,
    )

    class SiameseMultiPhaseNet(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.num_phases = num_phases
            self.fusion = fusion
            # Giữ trọng số attention của lần forward gần nhất để soi
            # phase-importance. Không tham gia vào đồ thị đạo hàm.
            self.last_phase_weights: Any = None

            self.downsample_factors = factors
            self.pre_pool = (
                nn.AvgPool3d(kernel_size=factors) if any(f > 1 for f in factors) else nn.Identity()
            )
            # in_channels=1: encoder nhìn MỘT thì mỗi lượt, và dùng chung cho cả 8.
            self.encoder = shared_encoder
            self.encoder_name = encoder
            self.embed_dim = feature_dim
            self.min_spatial = min_spatial
            self.phase_embedding = (
                nn.Parameter(torch.zeros(num_phases, feature_dim)) if phase_embedding else None
            )
            if fusion == "attention":
                hidden = max(8, feature_dim // 4)
                self.attention = nn.Sequential(
                    nn.Linear(feature_dim, hidden), nn.Tanh(), nn.Linear(hidden, 1)
                )
                head_in = feature_dim
            elif fusion == "concat":
                head_in = feature_dim * num_phases
            else:
                head_in = feature_dim
            self.head = nn.Sequential(nn.Dropout(dropout_prob), nn.Linear(head_in, num_classes))

        def forward(self, x: Any) -> Any:
            if x.ndim != 5:
                raise ValueError(f"cần đầu vào [B, P, X, Y, Z], nhận {tuple(x.shape)}")
            batch, phases = x.shape[0], x.shape[1]
            if phases != self.num_phases:
                raise ValueError(f"cần {self.num_phases} thì, nhận {phases}")

            # Chặn ở đây thay vì để MONAI ném RuntimeError từ sâu trong transition
            # layer, nơi thông báo không hé lộ nguyên nhân thật (WORKLOG S-063).
            spatial = tuple(x.shape[2:])
            after = tuple(d // f for d, f in zip(spatial, self.downsample_factors, strict=True))
            if any(d < self.min_spatial for d in after):
                raise ValueError(
                    f"đầu vào {spatial} chia cho input_downsample "
                    f"{self.downsample_factors} còn {after}, mà {self.encoder_name} cần "
                    f">= {self.min_spatial} ở mọi chiều. Giảm hệ số hạ mẫu, hoặc dùng "
                    f"khối đầu vào lớn hơn."
                )

            # Gộp trục batch và trục thì để encoder chạy MỘT lượt trên B*P mẫu —
            # nhanh hơn nhiều so với vòng lặp python qua từng thì.
            merged = x.reshape(batch * phases, 1, *x.shape[2:])
            features = self.encoder(self.pre_pool(merged)).reshape(batch, phases, -1)

            if self.phase_embedding is not None:
                features = features + self.phase_embedding

            if self.fusion == "attention":
                scores = self.attention(features)  # [B, P, 1]
                weights = scores.softmax(dim=1)
                self.last_phase_weights = weights.detach().squeeze(-1)
                fused = (features * weights).sum(dim=1)
            elif self.fusion == "concat":
                fused = features.reshape(batch, -1)
            else:
                fused = features.mean(dim=1)
            return self.head(fused)

    return SiameseMultiPhaseNet()
