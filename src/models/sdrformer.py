"""SDR-Former — Siamese Dual-Resolution Transformer, tái lập từ bài báo.

Nguồn: Lou, Ying, Liu, Zhou, Zhang, Yu, *SDR-Former: A Siamese Dual-Resolution Transformer
for Liver Lesion Classification Using 3D Multi-Phase Imaging*, arXiv:2402.17246 (2024).
Bài đo trên **đúng nhánh MR 8 pha của LLD-MMRI** và báo macro-F1 **0.7910**, κ **0.7467**.

⚠️ Nhóm tác giả này **chính là nhóm phát hành LLD-MMRI** — bài giới thiệu dataset và
challenge MICCAI 2023. Nên mốc 0.7910 của họ đo trên test-104 với nhãn họ tự giữ, không
phải nộp qua leaderboard.

## ⭐ Vì sao hướng này KHÁC hai hướng vừa thất bại

UniFormer-Base (dung lượng lớn hơn) và UniFormerV2-B/16 (nguồn pretrain khác) đều **không**
vượt được `uniformer_s`. Hai trục đó coi như đã cạn. SDR-Former đổi một trục **thứ ba** mà
dự án chưa từng thử: **cách 8 pha được kết hợp**.

Hiện tại toàn bộ dự án dùng *image-level fusion* — 8 pha vào làm 8 kênh của conv đầu tiên.
SDR-Former dùng *Siamese*: **một encoder dùng chung** chạy riêng cho từng pha, rồi hợp nhất
bằng một module attention học được (APSM).

Bảng 1 của họ đo **đúng trục đó, một biến, trên sáu backbone khác nhau**, cùng dataset MR::

    backbone          image-level    Siamese     hiệu
    ResNet-50            0.6898      0.7168     +0.027
    DenseNet-121         0.7171      0.7394     +0.022
    MCSCNN               0.7089      0.7409     +0.032
    BoTNet-50            0.7139      0.7572     +0.043
    UniFormer-S          0.7123      0.7639     +0.052
    H2Former             0.7342      0.7745     +0.040

**Sáu trên sáu đều dương**, trung bình +0.036, và transformer hưởng lợi nhiều hơn CNN
(+0.045 so với +0.027). Đây là loại bằng chứng mà ba hướng bị dự án loại trước đó không có:
một hiệu ứng lặp lại trên nhiều backbone, không phải một con số đơn lẻ.

⚠️ Nhưng nó vẫn là bảng **của họ**, đo bằng protocol của họ (một split 316/78/104), không
phải phép đo của ta. Nó biện minh cho việc *thử*, không bảo đảm kết quả.

## ⚠️⚠️ ĐÁNH ĐỔI LỚN NHẤT: BỎ TRỌNG SỐ PRETRAINED

SDR-Former **train from scratch** — không có checkpoint công khai nào cho DR-Former.

Mà can thiệp duy nhất từng thắng có ý nghĩa thống kê trong dự án này chính là pretrained
Kinetics (+0.130, P < 0.001). Nên cấu hình này **cố ý vứt bỏ đòn bẩy đã biết là mạnh nhất**
để đổi lấy một đòn bẩy mới chưa kiểm chứng trên dữ liệu của ta.

Ba mốc từ-scratch để đặt kỳ vọng cho đúng::

    UniFormer-S from scratch, recipe ban tổ chức    0.6083   (baseline official)
    UniFormer-S from scratch, recipe của họ         0.7123   (Bảng 1)
    SDR-Former  from scratch, recipe của họ         0.7910   (Bảng 1)

So với `uniformer_s` + Kinetics của ta: **0.7682 trên test-104** (lần chạm 2), **0.8147
out-of-fold**. Tức 0.7910 của họ chỉ hơn ta **+0.023 trên test**, nằm gọn trong khoảng tin
cậy ±0.09 của ta. **Đây không phải một cấu hình chắc chắn tốt hơn** — nó là một phép thử
trục fusion, và giá trị chính của nó nằm ở chỗ đó.

## Kiến trúc — đọc kỹ ba mục, hai trong số đó là chỗ ta phải SUY

Nhãn dùng trong file này và trong `configs/sdrformer.yaml`:

    [BÀI]  trích trực tiếp, có mục dẫn nguồn
    [SUY]  bài không nói, ta suy — có ghi căn cứ
    [LỆCH] ta CỐ Ý làm khác — có ghi lý do

### DR-Former: hai nhánh, hai độ phân giải

[BÀI] Hình 2. Nhánh CNN nhận ảnh **đủ độ phân giải**, nhánh Transformer nhận ảnh **giảm
nửa trong mặt phẳng**. Lập luận của họ: conv là bộ lọc thông cao, self-attention là bộ lọc
thông thấp, nên giao đúng loại tín hiệu cho đúng nhánh.

Hình dạng khớp chính xác Hình 2 của bài (họ vẽ ở 16 lát trước khi cắt; ta cắt còn 14)::

    nhánh CNN          1x14x112x112 -> 16x14x56x56 -> 32x14x28x28 -> 64x7x14x14 -> 128x7x14x14
    nhánh Transformer  1x14x56x56   -> 16x14x28x28 -> 32x14x14x14 -> 64x7x7x7   -> 128x7x7x7

Ở **mọi** stage, nhánh CNN có đúng 2x số voxel trong mặt phẳng và **cùng số lát** — đó là
điều kiện BCIM cần (bài định nghĩa `F_v` là `C x D x H/2 x W/2`).

### BCIM: trao đổi hai chiều giữa hai nhánh

[BÀI] Eq. (1). Mỗi nhánh sinh một vector hệ số qua GAP + MLP + sigmoid, rồi **gating chéo**:
đặc trưng của nhánh kia được nhân với hệ số của **chính mình** trước khi nối vào::

    c = sigmoid(MLP(GAP(F_c)))          v = sigmoid(MLP(GAP(F_v)))
    D_c = Down(F_c)                     U_v = Up(F_v)
    D_c' = v * D_c                      U_v' = c * U_v
    F_c' = W3x3x3^2(concat(F_c, U_v'))  F_v' = W3x3x3^2(concat(F_v, D_c'))

### APSM: trọng số từng pha, học được

[BÀI] Eq. (2)-(3). Nối 8 pha theo kênh, ép về một descriptor toàn cục `M`, rồi 8 conv
1x1x1 song song sinh 8 descriptor riêng, softmax **trên trục pha** cho từng kênh.

Đây là chỗ khác hẳn `src/models/siamese_fusion.py`: bản kia chấm điểm mỗi pha bằng một
**scalar** trên vector đặc trưng đã pool. APSM cho mỗi pha một trọng số **riêng cho từng
kênh**, và làm việc đó trên feature map còn nguyên chiều không gian.

## ⚠️ SỐ THAM SỐ KHÔNG KHỚP BÀI — đọc trước khi diễn giải kết quả

Bảng 4 của bài: **19.34M** tham số, **40.26 GFLOPs** cho bản 8 pha. Bản tái lập này, dựng
đúng theo Hình 2 (một block mỗi stage, `W^2_3x3x3` đi 2C -> C -> C), cho **~12.7M**.

Thiếu ~6.6M, và bài **không** cho đủ thông tin để biết thiếu ở đâu. Hai chỗ khả dĩ nhất,
đã tính sẵn để ai muốn thử không phải nhẩm lại:

* `blocks_per_stage: 2` thay vì 1 — Hình 2 vẽ **một** hộp "Residual Block" mỗi stage, nhưng
  hộp trong sơ đồ thường ký hiệu một nhóm lặp. Thêm ~+1.2M.
* `bcim_hidden_mult: 2` — cho `W^2_3x3x3` đi 2C -> 2C -> C thay vì 2C -> C -> C. Thêm ~+3.5M.

Bật cả hai cho ~17.3M, vẫn chưa đúng 19.34M.

**Mặc định vẫn là bản literal (~12.7M), có lý do khoa học chứ không phải cho tiện:** dự án
vừa đo được rằng **tăng dung lượng làm TỆ ĐI** trên 312 ca train (UniFormer-Base thua
UniFormer-S). Một bản nhỏ hơn bài báo vì thế hợp với chẩn đoán hiện tại, không phải một
thiếu sót cần vá. Nhưng mọi báo cáo dùng con số của cấu hình này **bắt buộc** ghi rằng đây
là bản tái lập **nhỏ hơn** bài, và mốc 0.7910 vì thế chỉ là mốc định hướng.

⚠️ Bảng 4 còn một chỗ tự nó đã lạ, cần biết để không suy diễn sai: bản **3 pha** của họ có
**nhiều** tham số hơn bản 8 pha (28.52M so với 19.34M) và nhiều FLOPs hơn (102.30 so với
40.26). Cùng một kiến trúc mà thêm pha lại rẻ đi là không thể, nên gần như chắc chắn họ
dùng **hai cấu hình kích thước khác nhau** cho hai dataset — và bài không nói cấu hình nào.

## Bốn chỗ CỐ Ý lệch khỏi bài (đều phải vào báo cáo)

* **`random erasing`** — [LỆCH] §4.2 liệt kê "random rotations, erasing, and flips". Dự án
  không có `RandomErasing3D` và không cài thêm cho lần này. Chỗ thiếu duy nhất trong danh
  sách augmentation của họ.
* **`rotate_mode: nearest`** — [LỆCH] cùng lý do đã ghi ở `configs/uniformer_s.yaml`: lề
  cache chỉ 8 voxel, xoay `constant` để lọt voxel bị lấp 0 vào phép cắt biên (E12, S-111).
* **GSA là lựa chọn duy nhất được cài** — Bảng 5 của họ so bốn cơ chế attention
  (Swin / SRA / PSA / GSA) và **chốt GSA**. Ba cái kia không cài, vì chúng là phần *ablation
  chọn module* của bài, không phải cấu hình cuối.
* **Kích thước lưới GSA** — [SUY] bài không nói. Xem `DEFAULT_GRID`.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

NUM_PHASES = 8
SPATIAL_DIMS = 3

# Bảng 4, cột 8 pha. Cổng A của notebook in số tham số thật cạnh hai con số này.
PAPER_PARAMS_M = 19.34
PAPER_FLOPS_G = 40.26

# Bảng 1, hàng SDR-Former, phần "MR (8-phase)". Mốc đối chiếu của cả phép tái lập.
PAPER_MR = {"acc": 0.7885, "auc": 0.9536, "f1": 0.7910, "kappa": 0.7467}

# Bảng 1, phần MR: (image-level, Siamese) cho từng backbone. Đây là bằng chứng MỘT BIẾN cho
# trục fusion — thứ biện minh cho việc chạy cấu hình này, nên nó được neo lại bằng test.
SNN_GAIN_MR: dict[str, tuple[float, float]] = {
    "resnet50": (0.6898, 0.7168),
    "densenet121": (0.7171, 0.7394),
    "mcscnn": (0.7089, 0.7409),
    "botnet50": (0.7139, 0.7572),
    "uniformer_s": (0.7123, 0.7639),
    "h2former": (0.7342, 0.7745),
}

# [BÀI] Hình 2. Kênh sau stem, rồi ba stage. Nhánh CNN và nhánh Transformer dùng CÙNG bộ số.
DEFAULT_STEM_CHANNELS = 16
DEFAULT_STAGE_CHANNELS = (32, 64, 128)

# [BÀI] Hình 2: MaxPool 1x2x2 sau stage 1, MaxPool 2x2x2 sau stage 2, không pool sau stage 3.
# Thứ tự (D, H, W) theo quy ước của MODEL.
STAGE_POOL = ((1, 2, 2), (2, 2, 2), None)

# [SUY] Bài chốt GSA (Bảng 5) nhưng KHÔNG nói kích thước lưới. 7x7 trong mặt phẳng là mặc
# định của MaxViT — nơi GSA ra đời — và nó chia hết cho cả ba kích thước mà nhánh Transformer
# đi qua (28, 14, 7). Trục lát lấy 2 vì D chỉ còn 14 rồi 7; lấy lớn hơn thì mỗi nhóm gần như
# chỉ còn một lát và attention mất hết ngữ cảnh giữa các lát.
#
# GSA lấy token theo bước nhảy (không phải cửa sổ liền kề), nên mỗi nhóm attention trải
# khắp khối — "sparse token-linking strategy that broadens its range to a global scale".
DEFAULT_GRID = (2, 7, 7)

# Chỉ GSA được cài. Ba cái kia nằm trong Bảng 5 (phần chọn module) chứ không phải cấu hình cuối.
ATTENTION_SCHEMES = ("gsa",)

__all__ = [
    "ATTENTION_SCHEMES",
    "DEFAULT_GRID",
    "DEFAULT_STAGE_CHANNELS",
    "DEFAULT_STEM_CHANNELS",
    "NUM_PHASES",
    "PAPER_FLOPS_G",
    "PAPER_MR",
    "PAPER_PARAMS_M",
    "SNN_GAIN_MR",
    "STAGE_POOL",
    "build_sdrformer",
    "stage_shapes",
]


def stage_shapes(
    input_size: Sequence[int],
    stem_channels: int = DEFAULT_STEM_CHANNELS,
    stage_channels: Sequence[int] = DEFAULT_STAGE_CHANNELS,
) -> list[tuple[str, int, tuple[int, int, int], tuple[int, int, int]]]:
    """Hình dạng ``(D, H, W)`` của **cả hai nhánh** sau từng stage, để cổng B đối chiếu.

    `input_size` là ``(D, H, W)`` theo thứ tự của MODEL (D = trục lát), **không** phải thứ tự
    ``[X, Y, Z]`` của cache. Trả về một hàng cho stem và một hàng cho mỗi stage, mỗi hàng là
    ``(tên, số kênh, hình nhánh CNN, hình nhánh Transformer)``.

    Tồn tại vì một mạng chạy ở kích thước sai **không nổ và không cảnh báo** — nó vẫn hội tụ,
    chỉ là thấp hơn đáng lẽ (E2 chạy suốt ở 48 in-plane thay vì 96, WORKLOG S-065). Và ở
    riêng kiến trúc này còn một bất biến nữa phải giữ: nhánh CNN luôn có **đúng 2x** số voxel
    trong mặt phẳng và **cùng số lát** với nhánh Transformer, nếu không BCIM ghép sai.
    """
    d, h, w = (int(v) for v in input_size)
    if h % 2 or w % 2:
        raise ValueError(f"cạnh trong mặt phẳng phải chẵn để nhánh thấp lấy nửa, nhận {(h, w)}")

    def _pool(shape: tuple[int, int, int], factor: tuple[int, int, int]) -> tuple[int, int, int]:
        return (shape[0] // factor[0], shape[1] // factor[1], shape[2] // factor[2])

    # Stem: conv 3x3x3 giữ nguyên kích thước, rồi MaxPool 1x2x2.
    cnn = _pool((d, h, w), (1, 2, 2))
    trans = _pool((d, h // 2, w // 2), (1, 2, 2))
    rows = [("stem", int(stem_channels), cnn, trans)]

    for i, ch in enumerate(stage_channels):
        # Block giữ nguyên kích thước không gian, chỉ đổi số kênh; pool nằm SAU BCIM.
        pool = STAGE_POOL[i] if i < len(STAGE_POOL) else None
        if pool is not None:
            cnn, trans = _pool(cnn, pool), _pool(trans, pool)
        rows.append((f"stage{i + 1}", int(ch), cnn, trans))
    return rows


def build_sdrformer(
    num_phases: int = NUM_PHASES,
    num_classes: int = 7,
    stem_channels: int = DEFAULT_STEM_CHANNELS,
    stage_channels: Sequence[int] = DEFAULT_STAGE_CHANNELS,
    blocks_per_stage: int = 1,
    num_heads: int = 4,
    mlp_ratio: float = 4.0,
    grid_size: Sequence[int] = DEFAULT_GRID,
    attention: str = "gsa",
    bcim_hidden_mult: int = 1,
    bcim_reduction: int = 4,
    dropout_prob: float = 0.2,
    use_bcim: bool = True,
    use_apsm: bool = True,
) -> Any:
    """Dựng SDR-Former nhận ``[B, num_phases, X, Y, Z]`` -> logits ``[B, num_classes]``.

    Tham số:
        blocks_per_stage: số block mỗi stage ở **cả hai** nhánh. Mặc định 1 = đọc literal
            Hình 2. Xem mục "SỐ THAM SỐ KHÔNG KHỚP BÀI" ở docstring module trước khi đổi.
        grid_size: lưới GSA ``(gd, gh, gw)``. Feature map được đệm lên bội của lưới rồi cắt
            lại, nên giá trị không chia hết vẫn chạy — chỉ tốn thêm chút tính toán.
        bcim_hidden_mult: chiều trung gian của ``W^2_3x3x3`` trong BCIM, tính theo bội của C.
            1 = ``2C -> C -> C`` (literal). 2 = ``2C -> 2C -> C``.
        use_bcim, use_apsm: tắt để dựng lại **đúng ba hàng ablation Bảng 3** của bài
            (Baseline / +BCIM / +APSM / đủ bộ). Tắt BCIM thì hai nhánh chạy song song không
            trao đổi; tắt APSM thì 8 pha được gộp bằng trung bình.

            ⚠️ Đây là ablation **kiến trúc**, mỗi lần chạy tốn đủ một fold. Đừng bật nó cho
            tới khi bản đủ bộ có kết quả 5 fold — nếu không sẽ lặp lại đúng lỗi đã mắc ba
            lần: sàng cỡ nhỏ trên nhiều nhánh rồi chọn nhánh thắng.
    """
    # Kiểm tham số TRƯỚC khi import torch: config sai phải nổ ngay cả trên máy chưa cài
    # deep-learning stack, để `pytest` ở local vẫn bắt được.
    if attention not in ATTENTION_SCHEMES:
        raise ValueError(
            f"attention phải thuộc {ATTENTION_SCHEMES}, nhận {attention!r}. Bảng 5 của bài so "
            "Swin/SRA/PSA/GSA và chốt GSA; ba cái kia là phần chọn module, không cài."
        )
    channels = tuple(int(c) for c in stage_channels)
    if len(channels) != len(STAGE_POOL):
        raise ValueError(
            f"stage_channels phải có đúng {len(STAGE_POOL)} phần tử theo Hình 2, "
            f"nhận {len(channels)}"
        )
    if any(c <= 0 for c in channels) or int(stem_channels) <= 0:
        raise ValueError("số kênh phải dương")
    for c in channels:
        if c % int(num_heads):
            raise ValueError(f"số kênh {c} phải chia hết cho num_heads={num_heads}")
    grid = tuple(int(g) for g in grid_size)
    if len(grid) != SPATIAL_DIMS or any(g < 1 for g in grid):
        raise ValueError(f"grid_size phải là 3 số >= 1, nhận {grid_size!r}")
    if int(blocks_per_stage) < 1:
        raise ValueError(f"blocks_per_stage phải >= 1, nhận {blocks_per_stage}")
    if int(bcim_hidden_mult) < 1:
        raise ValueError(f"bcim_hidden_mult phải >= 1, nhận {bcim_hidden_mult}")
    if int(num_phases) < 1:
        raise ValueError(f"num_phases phải >= 1, nhận {num_phases}")

    n_blocks = int(blocks_per_stage)
    n_heads = int(num_heads)
    stem_ch = int(stem_channels)
    n_phases = int(num_phases)

    import torch
    from torch import nn
    from torch.nn import functional as F

    def conv_bn_relu(cin: int, cout: int, kernel: int = 3, stride: Any = 1) -> Any:
        pad = kernel // 2
        return nn.Sequential(
            nn.Conv3d(cin, cout, kernel, stride=stride, padding=pad, bias=False),
            nn.BatchNorm3d(cout),
            nn.ReLU(inplace=True),
        )

    class LayerNorm3d(nn.Module):
        """LayerNorm trên trục KÊNH của tensor ``[B, C, D, H, W]``."""

        def __init__(self, dim: int) -> None:
            super().__init__()
            self.norm = nn.LayerNorm(dim, eps=1e-6)

        def forward(self, x: Any) -> Any:
            return self.norm(x.permute(0, 2, 3, 4, 1)).permute(0, 4, 1, 2, 3)

    class ResidualBlock3D(nn.Module):
        """[BÀI] §3.2: "each block containing two 3x3x3 convolutional layers linked by a
        shortcut connection". Hình 2 vẽ Conv-Norm-ReLU-Conv-Norm, tức post-norm kiểu ResNet."""

        def __init__(self, cin: int, cout: int) -> None:
            super().__init__()
            self.conv1 = nn.Conv3d(cin, cout, 3, padding=1, bias=False)
            self.bn1 = nn.BatchNorm3d(cout)
            self.conv2 = nn.Conv3d(cout, cout, 3, padding=1, bias=False)
            self.bn2 = nn.BatchNorm3d(cout)
            self.act = nn.ReLU(inplace=True)
            self.shortcut = (
                nn.Sequential(nn.Conv3d(cin, cout, 1, bias=False), nn.BatchNorm3d(cout))
                if cin != cout
                else nn.Identity()
            )

        def forward(self, x: Any) -> Any:
            out = self.act(self.bn1(self.conv1(x)))
            out = self.bn2(self.conv2(out))
            return self.act(out + self.shortcut(x))

    def grid_partition(x: Any, g: tuple[int, int, int]) -> tuple[Any, tuple[int, int, int]]:
        """Chia ``[B, C, D, H, W]`` thành các nhóm token **thưa** theo lưới ``g``.

        Khác cửa sổ liền kề (Swin): tách ``D -> (gd, nd)`` rồi lấy **gd** làm trục token nghĩa
        là các token trong một nhóm cách nhau ``nd`` voxel, tức mỗi nhóm trải khắp khối. Đó
        chính là "sparse token-linking strategy" mà §5.2.3 mô tả.

        Feature map được đệm lên bội của lưới; `grid_reverse` cắt lại.
        """
        b, c, d, h, w = x.shape
        gd, gh, gw = g
        pd, ph, pw = (-d) % gd, (-h) % gh, (-w) % gw
        if pd or ph or pw:
            x = F.pad(x, (0, pw, 0, ph, 0, pd))
        nd, nh, nw = (d + pd) // gd, (h + ph) // gh, (w + pw) // gw
        x = x.view(b, c, gd, nd, gh, nh, gw, nw)
        x = x.permute(0, 3, 5, 7, 2, 4, 6, 1).contiguous()
        return x.view(b * nd * nh * nw, gd * gh * gw, c), (nd, nh, nw)

    def grid_reverse(
        tokens: Any,
        cells: tuple[int, int, int],
        g: tuple[int, int, int],
        shape: tuple[int, int, int, int, int],
    ) -> Any:
        b, c, d, h, w = shape
        gd, gh, gw = g
        nd, nh, nw = cells
        x = tokens.view(b, nd, nh, nw, gd, gh, gw, c)
        x = x.permute(0, 7, 4, 1, 5, 2, 6, 3).contiguous()
        x = x.view(b, c, gd * nd, gh * nh, gw * nw)
        return x[:, :, :d, :h, :w]

    class GridSelfAttention3D(nn.Module):
        """GSA — Grid Self-attention 3D (Tu và cs., MaxViT), bản chuyển sang 3 chiều.

        [BÀI] §5.2.3 chốt GSA trong bốn cơ chế vì nó **giữ nguyên** q/k/v (không hạ mẫu như
        SRA/PSA nên không mất thông tin) mà vẫn có tầm nhìn toàn cục (khác Swin, vốn chỉ nhìn
        cửa sổ liền kề).
        """

        def __init__(self, dim: int, heads: int, g: tuple[int, int, int]) -> None:
            super().__init__()
            self.heads = heads
            self.grid = g
            self.qkv = nn.Linear(dim, dim * 3, bias=True)
            self.proj = nn.Linear(dim, dim)

        def forward(self, x: Any) -> Any:
            shape = x.shape
            tokens, cells = grid_partition(x, self.grid)
            nb, n, c = tokens.shape
            qkv = self.qkv(tokens).reshape(nb, n, 3, self.heads, c // self.heads)
            q, k, v = qkv.permute(2, 0, 3, 1, 4)
            # SDPA: cùng phép toán, không dựng ma trận (n x n) trong bộ nhớ. Với lưới mặc
            # định n chỉ 98 nên không bắt buộc, nhưng nó rẻ hơn và không có lý do không dùng
            # (UniFormer-Base OOM đúng vì dựng ma trận đó tường minh ở stage 3).
            out = F.scaled_dot_product_attention(q, k, v)
            out = out.transpose(1, 2).reshape(nb, n, c)
            return grid_reverse(self.proj(out), cells, self.grid, shape)

    class AttentionBlock3D(nn.Module):
        """[BÀI] Hình 2: Norm -> Self-attention -> Norm -> FC -> GELU -> FC, tức pre-norm.

        Đổi số kênh bằng conv 1x1x1 + norm đặt TRƯỚC block — đúng hộp "Conv 1x1x1 / Norm"
        mà Hình 2 vẽ ở nhánh Transformer.
        """

        def __init__(self, cin: int, cout: int, heads: int, g: tuple[int, int, int]) -> None:
            super().__init__()
            self.proj_in = (
                nn.Sequential(nn.Conv3d(cin, cout, 1, bias=False), nn.BatchNorm3d(cout))
                if cin != cout
                else nn.Identity()
            )
            self.norm1 = LayerNorm3d(cout)
            self.attn = GridSelfAttention3D(cout, heads, g)
            self.norm2 = LayerNorm3d(cout)
            hidden = int(cout * mlp_ratio)
            self.mlp = nn.Sequential(
                nn.Conv3d(cout, hidden, 1), nn.GELU(), nn.Conv3d(hidden, cout, 1)
            )

        def forward(self, x: Any) -> Any:
            x = self.proj_in(x)
            x = x + self.attn(self.norm1(x))
            return x + self.mlp(self.norm2(x))

    class BCIM(nn.Module):
        """[BÀI] Eq. (1) — Bilateral Cross-resolution Integration Module.

        ⚠️ Gating là **chéo**: `U_v` (từ nhánh Transformer, đã phóng to) được nhân với `c`
        (hệ số của nhánh CNN) rồi mới nối vào nhánh CNN. Tức mỗi nhánh tự quyết định nó muốn
        lấy bao nhiêu từ nhánh kia. Viết ngược lại vẫn chạy và vẫn hội tụ.
        """

        def __init__(self, dim: int) -> None:
            super().__init__()
            hidden = max(1, dim // int(bcim_reduction))
            self.mlp_c = nn.Sequential(
                nn.Linear(dim, hidden), nn.ReLU(inplace=True), nn.Linear(hidden, dim)
            )
            self.mlp_v = nn.Sequential(
                nn.Linear(dim, hidden), nn.ReLU(inplace=True), nn.Linear(hidden, dim)
            )
            mid = dim * int(bcim_hidden_mult)
            self.fuse_c = nn.Sequential(conv_bn_relu(2 * dim, mid), conv_bn_relu(mid, dim))
            self.fuse_v = nn.Sequential(conv_bn_relu(2 * dim, mid), conv_bn_relu(mid, dim))

        @staticmethod
        def _coeff(mlp: Any, feat: Any) -> Any:
            pooled = feat.mean(dim=(2, 3, 4))
            return torch.sigmoid(mlp(pooled))[:, :, None, None, None]

        def forward(self, fc: Any, fv: Any) -> tuple[Any, Any]:
            c = self._coeff(self.mlp_c, fc)
            v = self._coeff(self.mlp_v, fv)
            # Down giữ nguyên trục lát, chỉ hạ mặt phẳng — nhánh thấp khác nhánh cao ĐÚNG
            # ở mặt phẳng, cùng số lát (định nghĩa F_v trong bài).
            d_c = F.avg_pool3d(fc, kernel_size=(1, 2, 2))
            u_v = F.interpolate(fv, size=fc.shape[2:], mode="trilinear", align_corners=False)
            fc_out = self.fuse_c(torch.cat([fc, c * u_v], dim=1))
            fv_out = self.fuse_v(torch.cat([fv, v * d_c], dim=1))
            return fc_out, fv_out

    class APSM(nn.Module):
        """[BÀI] Eq. (2)-(3) — Adaptive Phase Selection Module.

        Softmax chạy **trên trục pha**, riêng cho từng kênh: mỗi kênh tự phân bổ 8 pha một
        cách khác nhau. Đây là điểm khác `siamese_fusion.py`, nơi mỗi pha chỉ có một scalar.
        """

        def __init__(self, dim: int, phases: int) -> None:
            super().__init__()
            self.phases = phases
            self.reduce = nn.Conv3d(dim * phases, dim, 1)
            self.split = nn.ModuleList([nn.Conv3d(dim, dim, 1) for _ in range(phases)])
            self.fuse = conv_bn_relu(dim * phases, dim)
            # Trọng số của lần forward gần nhất, `[B, P, C]`. Đây là thứ Hình 7 của bài vẽ
            # ra, và là bằng chứng trực tiếp nhất rằng APSM có thật sự phân biệt các pha —
            # trọng số phẳng đều 1/P nghĩa là module không học được gì. Cổng F đọc nó.
            self.last_weights: Any = None

        def forward(self, feats: Any) -> Any:
            """feats: ``[B, P, C, D, H, W]`` -> ``[B, C, D, H, W]``."""
            b, p, c, d, h, w = feats.shape
            stacked = feats.reshape(b, p * c, d, h, w)
            m = self.reduce(stacked).mean(dim=(2, 3, 4), keepdim=True)  # [B, C, 1, 1, 1]
            descriptors = torch.stack([conv(m) for conv in self.split], dim=1)  # [B, P, C,1,1,1]
            weights = descriptors.softmax(dim=1)
            self.last_weights = weights.detach().reshape(b, p, c)
            weighted = (feats * weights).reshape(b, p * c, d, h, w)
            return self.fuse(weighted)

    class DRFormer(nn.Module):
        """Encoder **dùng chung** cho cả 8 pha — chính là "weight-sharing network" của SNN.

        Dùng chung trọng số là điều làm cho hướng này khả thi: chi phí tham số y hệt một
        encoder đơn, chỉ chi phí *tính toán* nhân lên theo số pha. Với 312 ca train, tám
        encoder riêng gần như chắc chắn overfit.
        """

        def __init__(self) -> None:
            super().__init__()
            self.stem_c = nn.Sequential(conv_bn_relu(1, stem_ch), nn.MaxPool3d((1, 2, 2)))
            self.stem_v = nn.Sequential(conv_bn_relu(1, stem_ch), nn.MaxPool3d((1, 2, 2)))

            self.cnn_stages = nn.ModuleList()
            self.attn_stages = nn.ModuleList()
            self.bcims = nn.ModuleList()
            self.pools = []
            cin = stem_ch
            for i, cout in enumerate(channels):
                self.cnn_stages.append(
                    nn.Sequential(
                        *[ResidualBlock3D(cin if j == 0 else cout, cout) for j in range(n_blocks)]
                    )
                )
                self.attn_stages.append(
                    nn.Sequential(
                        *[
                            AttentionBlock3D(cin if j == 0 else cout, cout, n_heads, grid)
                            for j in range(n_blocks)
                        ]
                    )
                )
                self.bcims.append(BCIM(cout) if use_bcim else None)
                self.pools.append(STAGE_POOL[i])
                cin = cout
            self.out_channels = cin

        def forward(self, x: Any) -> tuple[Any, Any]:
            """x: ``[B, 1, D, H, W]`` -> (đặc trưng nhánh CNN, đặc trưng nhánh Transformer)."""
            low = F.interpolate(
                x, scale_factor=(1.0, 0.5, 0.5), mode="trilinear", align_corners=False
            )
            fc, fv = self.stem_c(x), self.stem_v(low)
            for cnn, attn, bcim, pool in zip(
                self.cnn_stages, self.attn_stages, self.bcims, self.pools, strict=True
            ):
                fc, fv = cnn(fc), attn(fv)
                if bcim is not None:
                    fc, fv = bcim(fc, fv)
                if pool is not None:
                    fc = F.max_pool3d(fc, kernel_size=pool)
                    fv = F.max_pool3d(fv, kernel_size=pool)
            return fc, fv

    class SDRFormer(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.num_phases = n_phases
            self.encoder = DRFormer()
            dim = self.encoder.out_channels
            self.use_apsm = use_apsm
            if use_apsm:
                self.apsm_c = APSM(dim, n_phases)
                self.apsm_v = APSM(dim, n_phases)
            # [SUY] Hình 1 ghi "Conv 3x3x3 Stride=2" ở nhánh cao trước khi Concat. Stride phải
            # là (1,2,2), KHÔNG phải 2 đều: hai nhánh chỉ khác nhau ở mặt phẳng và luôn cùng
            # số lát, nên stride 2 đều sẽ làm lệch trục lát và phép Concat không ghép được.
            self.down = conv_bn_relu(dim, dim, 3, stride=(1, 2, 2))
            self.head = nn.Sequential(nn.Dropout(dropout_prob), nn.Linear(dim * 2, num_classes))
            # Trọng số APSM của lần forward gần nhất, để soi phase-importance (Hình 7 của
            # bài). Không tham gia đồ thị đạo hàm.
            self.last_phase_weights: Any = None
            self._init_weights()

        def _init_weights(self) -> None:
            for m in self.modules():
                if isinstance(m, nn.Conv3d):
                    nn.init.kaiming_normal_(m.weight, mode="fan_out", nonlinearity="relu")
                    if m.bias is not None:
                        nn.init.constant_(m.bias, 0)
                elif isinstance(m, nn.BatchNorm3d):
                    nn.init.constant_(m.weight, 1.0)
                    nn.init.constant_(m.bias, 0)
                elif isinstance(m, nn.Linear):
                    nn.init.trunc_normal_(m.weight, std=0.02)
                    if m.bias is not None:
                        nn.init.constant_(m.bias, 0)

        def forward(self, x: Any) -> Any:
            if x.ndim != 5:
                raise ValueError(f"cần đầu vào [B, P, X, Y, Z], nhận {tuple(x.shape)}")
            if x.shape[1] != self.num_phases:
                raise ValueError(f"cần {self.num_phases} pha, nhận {x.shape[1]}")
            # [N, P, X, Y, Z] -> [N, P, Z, X, Y]: trục lát của cache vào vai trục D của model,
            # cùng quy ước với `uniformer3d.py` và `cghnet.py`.
            x = x.permute(0, 1, 4, 2, 3).contiguous()
            b, p = x.shape[0], x.shape[1]

            # Gộp trục batch và trục pha để encoder chạy MỘT lượt trên B*P mẫu. Đây chính là
            # chỗ chi phí tính toán nhân lên gấp P so với early-fusion — xem cổng C.
            merged = x.reshape(b * p, 1, *x.shape[2:])
            fc, fv = self.encoder(merged)
            fc = fc.reshape(b, p, *fc.shape[1:])
            fv = fv.reshape(b, p, *fv.shape[1:])

            if self.use_apsm:
                vc, vv = self.apsm_c(fc), self.apsm_v(fv)
                # Trung bình hai nhánh, lấy trung bình trên kênh -> `[B, P]`, tức "pha nào
                # quan trọng" ở dạng đọc được. Chi tiết từng kênh vẫn còn ở `apsm_*.last_weights`.
                self.last_phase_weights = (
                    self.apsm_c.last_weights + self.apsm_v.last_weights
                ).mean(dim=2) / 2.0
            else:
                vc, vv = fc.mean(dim=1), fv.mean(dim=1)
                self.last_phase_weights = None

            fused = torch.cat([self.down(vc), vv], dim=1)
            return self.head(fused.mean(dim=(2, 3, 4)))

    return SDRFormer()
