"""Siamese đa pha: **một encoder dùng chung** chạy riêng cho từng thì, rồi hợp nhất.

Đây là bước v1 của trục fusion trong Spec Sheet §3, thay cho early-concat v0
(`src/models/densenet3d.py`, 8 pha vào như 8 kênh).

**Vì sao đổi.** Bảng so sánh trong SDR-Former (Lou et al., Neural Networks 2025,
đo trên đúng test-104 của LLD-MMRI) cho thấy bước nhảy lớn nhất không đến từ
backbone mà từ việc bọc backbone trong một Siamese Neural Network::

    ResNet-50 (early-fusion)     macro-F1 0.6898
    SNN-UniFormer-S              macro-F1 0.7639   <- +0.074 chỉ do đổi sang SNN
    SNN-H2Former                 macro-F1 0.7745
    SDR-Former (đủ bộ)           macro-F1 0.7910   <- +0.027 cho toàn bộ module lai

Hạng 2 của challenge dùng **ResNet18** và đạt 0.8078 nhờ registration tốt, tức
backbone không phải nút thắt. Cả ba đội đầu bảng đều thắng ở chỗ 8 thì được căn
và kết hợp thế nào.

*Ghi chú về mức tin cậy:* việc hàng ``ResNet-50`` là early-fusion còn ba hàng
``SNN-*`` là Siamese được **suy ra từ quy ước đặt tên** của bảng, chưa đối chiếu
phần setup của bài báo. Cần kiểm trước khi trích con số +0.074 vào report.

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

# DenseNet121-3D hạ mẫu 5 lần: conv0 /2, pool0 /2, rồi ba transition mỗi cái /2.
# Transition thứ ba dùng `AvgPool3d(kernel_size=2)`, nên đầu vào của nó phải ≥ 2 ở
# MỌI chiều — tức kích thước đưa vào encoder phải ≥ 32 ở mọi chiều. Dưới ngưỡng đó,
# MONAI ném `RuntimeError: input image ... smaller than kernel size` từ sâu trong
# mạng, không nói gì về nguyên nhân thật (WORKLOG S-063).
MIN_SPATIAL = 32


def build_siamese_fusion(
    num_phases: int = NUM_PHASES,
    num_classes: int = 7,
    embed_dim: int = 256,
    fusion: str = "attention",
    dropout_prob: float = 0.2,
    norm: str | Sequence[Any] = DEFAULT_NORM,
    phase_embedding: bool = True,
    input_downsample: int | Sequence[int] = (2, 2, 1),
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
    """
    # Kiểm tham số TRƯỚC khi import: cấu hình sai phải báo lỗi ngay cả trên máy
    # chưa cài deep-learning stack, để `pytest` ở local vẫn bắt được lỗi config.
    if fusion not in FUSIONS:
        raise ValueError(f"fusion phải thuộc {FUSIONS}, nhận {fusion!r}")
    factors = (
        (int(input_downsample),) * 3
        if isinstance(input_downsample, int)
        else tuple(int(f) for f in input_downsample)
    )
    if len(factors) != 3 or any(f < 1 for f in factors):
        raise ValueError(f"input_downsample phải là 1 số hoặc 3 số >= 1, nhận {input_downsample!r}")

    import torch
    from monai.networks.nets import DenseNet121
    from torch import nn

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
            self.encoder = DenseNet121(
                spatial_dims=SPATIAL_DIMS,
                in_channels=1,
                out_channels=embed_dim,
                dropout_prob=dropout_prob,
                norm=normalize_norm_spec(norm),
            )
            self.phase_embedding = (
                nn.Parameter(torch.zeros(num_phases, embed_dim)) if phase_embedding else None
            )
            if fusion == "attention":
                hidden = max(8, embed_dim // 4)
                self.attention = nn.Sequential(
                    nn.Linear(embed_dim, hidden), nn.Tanh(), nn.Linear(hidden, 1)
                )
                head_in = embed_dim
            elif fusion == "concat":
                head_in = embed_dim * num_phases
            else:
                head_in = embed_dim
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
            if any(d < MIN_SPATIAL for d in after):
                raise ValueError(
                    f"đầu vào {spatial} chia cho input_downsample "
                    f"{self.downsample_factors} còn {after}, mà DenseNet121-3D cần "
                    f">= {MIN_SPATIAL} ở mọi chiều. Giảm hệ số hạ mẫu, hoặc dùng "
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
