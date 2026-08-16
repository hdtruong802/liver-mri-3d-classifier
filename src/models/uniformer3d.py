"""UniFormer-3D nạp trọng số **Kinetics video**, tái lập recipe đội hạng 2 LLD-MMRI 2023.

## Vì sao kiến trúc này, và vì sao nó là phép so một biến đẹp nhất của bài toán

**Baseline official của challenge CHÍNH LÀ UniFormer-S 3D, train from scratch, 300 epoch →
macro-F1 0.6083** trên test-104. Đội hạng 2 (`NPUBXY`, 0.8078) dùng **đúng kiến trúc đó** và
khác ở một chỗ đọc được ngay trong `train.sh` của họ: `--pretrained`, nạp
``uniformer_small_k400_16x8.pth`` — trọng số học trên **video Kinetics-400**.

    0.6083  UniFormer-S, from scratch      (baseline official)
    0.8078  UniFormer-S/B + Kinetics + cb_loss + sqrt sampling + smoothing + drop-path

Không mốc đối chiếu nào khác trong văn liệu của dataset này tách được một cụm biến với biên độ
~0.20. Nguồn: https://github.com/ZHEGG/miccai2023 (repo của họ), leaderboard official
https://github.com/LMMMEng/LLD-MMRI2023/blob/main/assets/test_leaderboard.md.

⚠️ Chênh 0.20 đó **không phải phép thử một biến sạch** — nó gộp pretrained với 4 thứ khác.
Ta tái lập cả cụm và chỉ được quy kết cho **cả cụm**.

## Trục thời gian của model video = trục lát của ta

Kiến trúc gốc nhận ``(N, C, D, H, W)`` với `D` là trục thời gian. Ta đưa **8 pha MRI vào làm
kênh** `C` và **trục lát Z vào làm `D`**.

⚠️ **Toàn mạng gần như bất biến với thứ tự trục** — `pos_embed` là conv 3×3×3 depthwise, `attn`
của CBlock là conv 5×5×5 depthwise, `norm` là BatchNorm3d, và SABlock thì làm phẳng thành token.
Chỗ **duy nhất** trục có ý nghĩa là stride của `patch_embed`. Nhưng "gần như" không phải "hoàn
toàn": kernel 3×3×3 học trên (T, H, W) mà đem áp lên (X, Y, Z) thì lát kernel ứng với thời gian
sẽ rơi vào trục X. Vì vậy `forward` **hoán vị** ``[N,8,X,Y,Z] → [N,8,Z,X,Y]`` để các kernel
pretrained thấy đúng vai trò trục mà chúng đã học. Nhờ đó `patch_size` trong file này viết
nguyên văn ``(1, 2, 2)`` như code của họ, không phải dịch sang quy ước ``[X,Y,Z]`` của dự án —
lớp dịch đó là chỗ đã sinh lỗi ở E13 (WORKLOG S-120).

## Ngân sách: trục Z KHÔNG được hạ mẫu, nên đắt hơn bản pretrained

``patch_embed1`` của họ có stride ``(1, 2, 2)`` — giữ nguyên số lát. Bản pretrained thì
``(2, 4, 4)``. Hệ quả trên đầu vào ``14×112×112``:

    stage           bản pretrained (16×224×224)   của ta (14×112×112)
    patch_embed1    8×56×56                      14×56×56
    stage 3 (SA×8)  8×14×14 = 1568 token         14×14×14 = 2744 token
    stage 4 (SA×3)  8×7×7   =  392 token         14×7×7   =  686 token

Token nhiều gấp **1.75×**, và `SABlock` là attention toàn cục ⇒ chi phí stage 3 khoảng **3×**.
Nghĩa là cấu hình này **đắt hơn** CGHNet (209 GFLOPs, đo thật 1.6 h/fold), không rẻ hơn.

`patch_embed1_stride` là khoá thoát: đặt ``[1, 2, 2] → [2, 2, 2]`` thì Z 14→7, gần bản
pretrained (T=8) hơn và cắt ~2× ở stage conv, ~4× ở stage attention.

⚠️ **Đo s/epoch thật trước khi cam kết fold nào.** E13 phát hiện 79 s/epoch *sau khi* đã cam
kết và mất cả một session (WORKLOG S-120). Không suy giờ từ GFLOPs — AGENTS.md §6 đã ghi rõ
con số GFLOPs của CGHNet không dùng để suy giờ được.

## Chế độ hỏng nguy hiểm nhất, và cổng chặn nó

``load_state_dict(strict=False)`` **không báo lỗi khi không khoá nào khớp**. Model vẫn chạy,
vẫn ra số, chỉ là "có pretrained" lặng lẽ thành "không pretrained". Tệ hơn: E8 đặt sai
``shortcut_type`` mà tỉ lệ khớp vẫn ~85% — **dư sức qua một ngưỡng phần trăm** (WORKLOG S-118).

Vì vậy `unexpected_missing_keys` kiểm **khoá NÀO thiếu**, không kiểm tỉ lệ. Hai tiền tố duy
nhất được phép thiếu:

* ``patch_embed1.`` — 8 kênh MRI ≠ 3 kênh RGB, và stride cũng khác. Họ cũng bỏ nó.
* ``head.`` — 7 lớp ≠ 400 lớp Kinetics.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from typing import Any

from src.models.resnet3d import resolve_pretrained_path

IN_CHANNELS = 8
NUM_CLASSES = 7

# Hai tiền tố này KHÔNG khớp được về mặt hình học, nên thiếu chúng là bình thường. Mọi khoá
# khác mà thiếu đều là dấu hiệu lệch kiến trúc — xem docstring module.
DROPPED_PREFIXES = ("patch_embed1.", "head.")

# Biến thể "original" của repo hạng 2 (`models/uniformer.py::uniformer_*_original`). Các con số
# này khớp `uniformer_small()` / `uniformer_base()` của Sense-X, tức khớp file trọng số.
#   https://huggingface.co/Sense-X/uniformer_video
UNIFORMER_VARIANTS: dict[str, dict[str, Any]] = {
    "small": {"depth": (3, 4, 8, 3), "embed_dim": (64, 128, 320, 512), "head_dim": 64},
    "base": {"depth": (5, 8, 20, 7), "embed_dim": (64, 128, 320, 512), "head_dim": 64},
}

# Tên file trọng số tương ứng trên HuggingFace `Sense-X/uniformer_video`.
# ⚠️ `base` chỉ có bản 32x4 trên HF; bản 16x8 mà repo hạng 2 dùng CHỈ có trên Google Drive.
# Số frame lúc pretrain KHÔNG đổi shape tham số nào (đã kiểm), nên 32x4 nạp được — nhưng đó
# là một chỗ lệch so với họ và phải ghi vào báo cáo.
PRETRAINED_FILENAMES: dict[str, str] = {
    "small": "uniformer_small_k400_16x8.pth",
    "base": "uniformer_base_k600_32x4.pth",
}

HF_BASE_URL = "https://huggingface.co/Sense-X/uniformer_video/resolve/main/"

__all__ = [
    "DROPPED_PREFIXES",
    "HF_BASE_URL",
    "PRETRAINED_FILENAMES",
    "UNIFORMER_VARIANTS",
    "build_uniformer3d",
    "load_kinetics_weights",
    "stage_token_counts",
    "strip_state_dict",
    "unexpected_missing_keys",
    "variant_spec",
]


def variant_spec(variant: str) -> dict[str, Any]:
    """Tham số kiến trúc của một biến thể; nổ nếu tên sai thay vì im lặng chọn mặc định."""
    if variant not in UNIFORMER_VARIANTS:
        raise ValueError(f"model.variant phải thuộc {sorted(UNIFORMER_VARIANTS)}, nhận {variant!r}")
    return dict(UNIFORMER_VARIANTS[variant])


def unexpected_missing_keys(missing: Iterable[str]) -> list[str]:
    """Khoá thiếu mà KHÔNG thuộc `DROPPED_PREFIXES`, tức dấu hiệu lệch kiến trúc.

    Hàm **thuần**, không cần torch — cổng chặn phải test được, vì một cổng chặn không có test
    thì hỏng thầm lặng đúng lúc không ai nhìn. Xem docstring module về vụ E8.
    """
    return sorted(k for k in missing if not k.startswith(DROPPED_PREFIXES))


def strip_state_dict(raw: dict[str, Any]) -> dict[str, Any]:
    """Bóc checkpoint về ``state_dict`` phẳng, không tiền tố.

    Checkpoint Kinetics của Sense-X có thể là dict phẳng, hoặc bọc trong ``model_state`` /
    ``state_dict`` / ``model``, và có thể còn tiền tố ``module.`` của DataParallel. Code của
    repo hạng 2 giả định luôn là dict phẳng; giả định đó đúng với **một** file và sẽ hỏng
    lặng lẽ với file khác — tỉ lệ khớp về 0 mà `strict=False` không nói gì.
    """
    state = raw
    for wrapper in ("model_state", "state_dict", "model"):
        if isinstance(state, dict) and wrapper in state and isinstance(state[wrapper], dict):
            state = state[wrapper]
            break
    if not isinstance(state, dict):
        raise TypeError(f"checkpoint không phải dict sau khi bóc, nhận {type(state).__name__}")
    return {k.removeprefix("module."): v for k, v in state.items()}


def stage_token_counts(
    input_size: Sequence[int], patch_embed1_stride: Sequence[int]
) -> list[tuple[int, int, int]]:
    """Hình dạng ``(D, H, W)`` vào từng stage, để cổng B của notebook đối chiếu.

    `input_size` là ``(D, H, W)`` **theo thứ tự của model** (D = trục lát), không phải thứ tự
    ``[X, Y, Z]`` của cache. `patch_embed2..4` đều stride ``(1, 2, 2)``.

    Tồn tại vì E2 chạy suốt ở 48 in-plane thay vì 96 mà **không có gì báo** (WORKLOG S-065):
    số token phải in ra và đối chiếu bằng tay trước khi cam kết GPU.
    """
    d, h, w = (int(v) for v in input_size)
    sd, sh, sw = (int(v) for v in patch_embed1_stride)
    shapes = [(d // sd, h // sh, w // sw)]
    for _ in range(3):
        d0, h0, w0 = shapes[-1]
        shapes.append((d0, h0 // 2, w0 // 2))
    return shapes


def _drop_path(x: Any, drop_prob: float, training: bool) -> Any:
    """Stochastic depth theo mẫu (Huang và cs. 2016), bản của timm.

    Tự cài vì `timm` không nằm trong `requirements.txt` và thêm nó chỉ để lấy 10 dòng này là
    thêm dependency nặng cho một lý do nhẹ (AGENTS.md §10).

    Không `import torch`: mọi thao tác đi qua chính `x` (`new_empty`, `bernoulli_`), nên hàm
    chạy được mà không chạm namespace torch.
    """
    if drop_prob <= 0.0 or not training:
        return x
    keep = 1.0 - drop_prob
    # shape (N, 1, 1, ...) — một quyết định giữ/bỏ cho mỗi mẫu trong batch.
    shape = (x.shape[0],) + (1,) * (x.ndim - 1)
    mask = x.new_empty(shape).bernoulli_(keep)
    return x * mask.div_(keep)


def build_uniformer3d(
    variant: str = "small",
    in_channels: int = IN_CHANNELS,
    num_classes: int = NUM_CLASSES,
    patch_embed1_stride: Sequence[int] = (1, 2, 2),
    patch_embed1_kernel: Sequence[int] | None = None,
    mlp_ratio: float = 4.0,
    qkv_bias: bool = True,
    drop_rate: float = 0.0,
    attn_drop_rate: float = 0.0,
    drop_path_rate: float = 0.1,
    head_dropout: float = 0.0,
    memory_efficient_attn: bool = False,
    pretrained_path: str | None = None,
    require_pretrained: bool = False,
) -> Any:
    """Dựng UniFormer-3D cho MRI gan 8 pha.

    Args:
        variant: ``small`` hoặc ``base``. Xem `UNIFORMER_VARIANTS`.
        patch_embed1_stride: ``(D, H, W)`` **theo thứ tự model**. ``(1, 2, 2)`` là của repo
            hạng 2 (giữ nguyên số lát); ``(2, 2, 2)`` hạ nửa số lát và rẻ hơn nhiều.
        patch_embed1_kernel: mặc định bằng stride, đúng như họ (`stride=None → patch_size`).
        memory_efficient_attn: dùng `scaled_dot_product_attention` thay vì dựng ma trận
            attention ``(n × n)``. **Cùng phép toán**, chỉ khác cách xếp phép cộng, nên đây là
            khoá **vận hành** chứ không phải khoá khoa học. Mặc định ``False`` để nhánh đã
            chạy ra 0.8147 không đổi một bit nào.

            ⚠️ Biến thể ``base`` **cần** nó: stage 3 có 20 block trên 2744 token, và riêng một
            ma trận attention fp16 đã ~300 MB mỗi block ⇒ OOM trên T4 16GB ngay ở batch 4.
            Bật nó rẻ hơn hẳn hai lối thoát kia: giảm batch làm BatchNorm thấy ít mẫu hơn (đổi
            động học thật), còn ``patch_embed1_stride [2,2,2]`` là đổi kiến trúc.
        drop_rate: dropout trong Mlp và `pos_drop`. **Repo hạng 2 để 0.0** (factory của họ
            không truyền `drop_rate`, và `--drop` của timm mặc định 0). Giữ 0 để trung thực.
        drop_path_rate: ``--drop-path 0.1`` của họ.
        head_dropout: **bổ sung của dự án, không có ở họ.** `src/eval/mc_dropout.py` cần ít
            nhất một lớp `Dropout` để có bất định epistemic. Mặc định 0.0 để bản tái lập
            trung thực; đặt > 0 ở một config riêng nếu muốn MC-dropout.
            ⚠️ Với 0.0 thì model **không có lớp Dropout nào** và MC-dropout sẽ trả K lượt
            giống hệt nhau — vô nghĩa nhưng không nổ. Đừng chạy notebook 08 trên nó.
        require_pretrained: `True` thì thiếu file trọng số là **nổ**, không phải cảnh báo.
            Notebook đặt `True`: một run "pretrained" mà lặng lẽ chạy from scratch là đúng
            cái lỗi mà cả thí nghiệm này tồn tại để tránh.
    """
    import torch
    from torch import nn

    spec = variant_spec(variant)
    depth: tuple[int, ...] = spec["depth"]
    embed_dim: tuple[int, ...] = spec["embed_dim"]
    head_dim: int = spec["head_dim"]

    stride = tuple(int(v) for v in patch_embed1_stride)
    kernel = stride if patch_embed1_kernel is None else tuple(int(v) for v in patch_embed1_kernel)
    if len(stride) != 3 or len(kernel) != 3:
        raise ValueError(f"patch_embed1 stride/kernel phải 3 chiều, nhận {stride}/{kernel}")
    if any(v <= 0 for v in stride + kernel):
        raise ValueError(f"patch_embed1 stride/kernel phải > 0, nhận {stride}/{kernel}")
    if not 0.0 <= head_dropout < 1.0:
        raise ValueError(f"head_dropout phải trong [0, 1), nhận {head_dropout}")

    class DropPath(nn.Module):
        def __init__(self, p: float) -> None:
            super().__init__()
            self.p = float(p)

        def forward(self, x: Any) -> Any:
            return _drop_path(x, self.p, self.training)

    class Mlp(nn.Module):
        """Mlp trên token (Linear) — dùng trong SABlock."""

        def __init__(self, dim: int, hidden: int, drop: float) -> None:
            super().__init__()
            self.fc1 = nn.Linear(dim, hidden)
            self.act = nn.GELU()
            self.fc2 = nn.Linear(hidden, dim)
            self.drop = nn.Dropout(drop)

        def forward(self, x: Any) -> Any:
            return self.drop(self.fc2(self.drop(self.act(self.fc1(x)))))

    class CMlp(nn.Module):
        """Mlp trên lưới (conv 1×1×1) — dùng trong CBlock. Tên khoá `fc1`/`fc2` phải giữ
        nguyên để khớp checkpoint, dù chúng là Conv3d chứ không phải Linear."""

        def __init__(self, dim: int, hidden: int, drop: float) -> None:
            super().__init__()
            self.fc1 = nn.Conv3d(dim, hidden, 1)
            self.act = nn.GELU()
            self.fc2 = nn.Conv3d(hidden, dim, 1)
            self.drop = nn.Dropout(drop)

        def forward(self, x: Any) -> Any:
            return self.drop(self.fc2(self.drop(self.act(self.fc1(x)))))

    class Attention(nn.Module):
        def __init__(
            self, dim: int, num_heads: int, qkv_bias_: bool, attn_drop: float, proj_drop: float
        ) -> None:
            super().__init__()
            self.num_heads = num_heads
            self.scale = (dim // num_heads) ** -0.5
            self.qkv = nn.Linear(dim, dim * 3, bias=qkv_bias_)
            self.attn_drop = nn.Dropout(attn_drop)
            self.proj = nn.Linear(dim, dim)
            self.proj_drop = nn.Dropout(proj_drop)

        def forward(self, x: Any) -> Any:
            b, n, c = x.shape
            qkv = self.qkv(x).reshape(b, n, 3, self.num_heads, c // self.num_heads)
            q, k, v = qkv.permute(2, 0, 3, 1, 4)
            if memory_efficient_attn:
                # Cùng phép toán, nhưng KHÔNG dựng ma trận (n × n) trong bộ nhớ. Với
                # `patch_embed1_stride [1,2,2]` thì stage 3 có 2744 token, và riêng một ma
                # trận attention fp16 đã là ~300 MB mỗi block — nhân số block là hết VRAM.
                # Biến thể `base` có 20 block ở stage 3 và OOM ngay ở cổng C vì chỗ này.
                #
                # ⚠️ Kết quả **không bit-identical** với nhánh dưới: phép cộng dồn được sắp
                # xếp lại nên sai khác ở vài chữ số cuối của fp16. Về mặt toán học là một.
                out = torch.nn.functional.scaled_dot_product_attention(
                    q, k, v, dropout_p=self.attn_drop.p if self.training else 0.0
                )
            else:
                attn = (q @ k.transpose(-2, -1)) * self.scale
                attn = self.attn_drop(attn.softmax(dim=-1))
                out = attn @ v
            return self.proj_drop(self.proj(out.transpose(1, 2).reshape(b, n, c)))

    class CBlock(nn.Module):
        """Stage 1–2: MHRA cục bộ, hoàn toàn bằng conv. `attn` là conv 5×5×5 depthwise."""

        def __init__(self, dim: int, drop: float, attn_drop: float, drop_path: float) -> None:
            super().__init__()
            self.pos_embed = nn.Conv3d(dim, dim, 3, padding=1, groups=dim)
            self.norm1 = nn.BatchNorm3d(dim)
            self.conv1 = nn.Conv3d(dim, dim, 1)
            self.conv2 = nn.Conv3d(dim, dim, 1)
            self.attn = nn.Conv3d(dim, dim, 5, padding=2, groups=dim)
            self.drop_path = DropPath(drop_path) if drop_path > 0 else nn.Identity()
            self.norm2 = nn.BatchNorm3d(dim)
            self.mlp = CMlp(dim, int(dim * mlp_ratio), drop)
            del attn_drop  # CBlock không có attention thật nên không dùng; giữ chữ ký đồng nhất

        def forward(self, x: Any) -> Any:
            x = x + self.pos_embed(x)
            x = x + self.drop_path(self.conv2(self.attn(self.conv1(self.norm1(x)))))
            return x + self.drop_path(self.mlp(self.norm2(x)))

    class SABlock(nn.Module):
        """Stage 3–4: MHRA toàn cục — self-attention trên toàn bộ ``D·H·W`` token."""

        def __init__(
            self, dim: int, num_heads: int, drop: float, attn_drop: float, drop_path: float
        ) -> None:
            super().__init__()
            self.pos_embed = nn.Conv3d(dim, dim, 3, padding=1, groups=dim)
            self.norm1 = nn.LayerNorm(dim, eps=1e-6)
            self.attn = Attention(dim, num_heads, qkv_bias, attn_drop, drop)
            self.drop_path = DropPath(drop_path) if drop_path > 0 else nn.Identity()
            self.norm2 = nn.LayerNorm(dim, eps=1e-6)
            self.mlp = Mlp(dim, int(dim * mlp_ratio), drop)

        def forward(self, x: Any) -> Any:
            x = x + self.pos_embed(x)
            b, c, d, h, w = x.shape
            x = x.flatten(2).transpose(1, 2)
            x = x + self.drop_path(self.attn(self.norm1(x)))
            x = x + self.drop_path(self.mlp(self.norm2(x)))
            return x.transpose(1, 2).reshape(b, c, d, h, w)

    class PatchEmbed(nn.Module):
        """Conv3d hạ mẫu + LayerNorm. Tên khoá ``proj`` / ``norm`` khớp checkpoint."""

        def __init__(
            self, in_ch: int, out_ch: int, kernel_: tuple[int, ...], stride_: tuple[int, ...]
        ) -> None:
            super().__init__()
            self.proj = nn.Conv3d(in_ch, out_ch, kernel_size=kernel_, stride=stride_)
            self.norm = nn.LayerNorm(out_ch)

        def forward(self, x: Any) -> Any:
            x = self.proj(x)
            b, c, d, h, w = x.shape
            x = self.norm(x.flatten(2).transpose(1, 2))
            return x.reshape(b, d, h, w, c).permute(0, 4, 1, 2, 3).contiguous()

    class UniFormer3D(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.patch_embed1 = PatchEmbed(in_channels, embed_dim[0], kernel, stride)
            self.patch_embed2 = PatchEmbed(embed_dim[0], embed_dim[1], (1, 2, 2), (1, 2, 2))
            self.patch_embed3 = PatchEmbed(embed_dim[1], embed_dim[2], (1, 2, 2), (1, 2, 2))
            self.patch_embed4 = PatchEmbed(embed_dim[2], embed_dim[3], (1, 2, 2), (1, 2, 2))

            self.pos_drop = nn.Dropout(drop_rate)
            dpr = [x.item() for x in torch.linspace(0, drop_path_rate, sum(depth))]
            heads = [dim // head_dim for dim in embed_dim]
            cut = [0, depth[0], depth[0] + depth[1], depth[0] + depth[1] + depth[2]]

            self.blocks1 = nn.ModuleList(
                [
                    CBlock(embed_dim[0], drop_rate, attn_drop_rate, dpr[cut[0] + i])
                    for i in range(depth[0])
                ]
            )
            self.blocks2 = nn.ModuleList(
                [
                    CBlock(embed_dim[1], drop_rate, attn_drop_rate, dpr[cut[1] + i])
                    for i in range(depth[1])
                ]
            )
            self.blocks3 = nn.ModuleList(
                [
                    SABlock(embed_dim[2], heads[2], drop_rate, attn_drop_rate, dpr[cut[2] + i])
                    for i in range(depth[2])
                ]
            )
            self.blocks4 = nn.ModuleList(
                [
                    SABlock(embed_dim[3], heads[3], drop_rate, attn_drop_rate, dpr[cut[3] + i])
                    for i in range(depth[3])
                ]
            )
            self.norm = nn.BatchNorm3d(embed_dim[-1])
            # `pre_logits` là Identity ở bản gốc (representation_size=None) nên không sinh
            # khoá nào. Giữ tên để ai đối chiếu checkpoint không tưởng là ta bỏ mất tầng.
            self.pre_logits = nn.Identity()
            self.head_drop = nn.Dropout(head_dropout) if head_dropout > 0 else nn.Identity()
            self.head = nn.Linear(embed_dim[-1], num_classes)
            self.apply(self._init_weights)

        @staticmethod
        def _init_weights(m: Any) -> None:
            # Repo hạng 2 chỉ khởi tạo Conv3d (kaiming fan_out) và bỏ nhánh Linear/LayerNorm.
            # Ta giữ nguyên điều đó cho Conv3d, và thêm trunc_normal cho Linear vì `head`
            # luôn train từ đầu — để mặc định của PyTorch thì bias đầu ra lệch ngay từ epoch 0.
            if isinstance(m, nn.Conv3d):
                nn.init.kaiming_normal_(m.weight, mode="fan_out", nonlinearity="relu")
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.trunc_normal_(m.weight, std=0.02)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.LayerNorm):
                nn.init.constant_(m.bias, 0)
                nn.init.constant_(m.weight, 1.0)

        def forward(self, x: Any) -> Any:
            # [N, 8, X, Y, Z] -> [N, 8, Z, X, Y]: trục lát của ta vào vai trục thời gian của
            # model video, để kernel 3×3×3 / 5×5×5 pretrained thấy đúng vai trò trục.
            # Xem docstring module.
            x = x.permute(0, 1, 4, 2, 3).contiguous()
            x = self.pos_drop(self.patch_embed1(x))
            for blk in self.blocks1:
                x = blk(x)
            x = self.patch_embed2(x)
            for blk in self.blocks2:
                x = blk(x)
            x = self.patch_embed3(x)
            for blk in self.blocks3:
                x = blk(x)
            x = self.patch_embed4(x)
            for blk in self.blocks4:
                x = blk(x)
            x = self.pre_logits(self.norm(x))
            return self.head(self.head_drop(x.flatten(2).mean(-1)))

    model = UniFormer3D()

    path = resolve_pretrained_path(pretrained_path)
    if path is None or not path.exists():
        if require_pretrained:
            raise FileNotFoundError(
                "Không tìm thấy trọng số Kinetics. Đặt env LLDMMRI_PRETRAINED_PATH hoặc "
                f"model.pretrained_path. Tải: {HF_BASE_URL}{PRETRAINED_FILENAMES[variant]}. "
                "Cả thí nghiệm này TỒN TẠI để đo tác dụng của pretrained — chạy nó without "
                "trọng số là một thí nghiệm khác mà không có gì báo."
            )
        return model

    load_kinetics_weights(model, path)
    return model


def load_kinetics_weights(model: Any, path: Any) -> dict[str, list[str]]:
    """Nạp trọng số Kinetics, bỏ `patch_embed1.*` và `head.*`, rồi **chặn nếu lệch kiến trúc**.

    Trả về ``{"missing", "unexpected", "loaded"}`` để cổng A của notebook in ra. Nổ nếu có khoá
    thiếu ngoài `DROPPED_PREFIXES` — xem docstring module về vụ E8 lọt qua ngưỡng phần trăm.
    """
    import torch

    raw = torch.load(path, map_location="cpu", weights_only=False)
    state = strip_state_dict(raw)
    state = {k: v for k, v in state.items() if not k.startswith(DROPPED_PREFIXES)}

    own = model.state_dict()
    # Lọc theo CẢ tên và shape: một khoá cùng tên khác shape sẽ làm `load_state_dict` nổ với
    # thông báo dài dòng, còn ở đây nó hiện ra như "thiếu" và cổng bên dưới chỉ đúng chỗ.
    keep = {k: v for k, v in state.items() if k in own and own[k].shape == v.shape}
    missing = sorted(set(own) - set(keep))
    unexpected = sorted(set(state) - set(keep))

    bad = unexpected_missing_keys(missing)
    if bad:
        raise RuntimeError(
            f"{len(bad)} khoá thiếu ngoài {DROPPED_PREFIXES}: {bad[:10]}"
            + (f" (và {len(bad) - 10} khoá nữa)" if len(bad) > 10 else "")
            + ". Kiến trúc lệch khỏi file trọng số — KHÔNG train tiếp, số sẽ vô nghĩa."
        )

    own.update(keep)
    model.load_state_dict(own)
    return {"missing": missing, "unexpected": unexpected, "loaded": sorted(keep)}


def count_flops_proxy(input_size: Sequence[int], patch_embed1_stride: Sequence[int]) -> int:
    """Tổng số token qua 4 stage — proxy ngân sách RẺ, không phải FLOPs.

    ⚠️ Đây **không** dùng để suy ra giờ chạy. AGENTS.md §6 đã ghi: con số 209.91 GFLOPs của
    CGHNet không suy được ra giờ, và ước lượng ~8h/fold từ FLOPs của tôi ở S-120 sai xa so với
    1.6h thật. Dùng nó chỉ để **so hai cấu hình với nhau**, ví dụ ``(1,2,2)`` so ``(2,2,2)``.
    """
    return sum(math.prod(shape) for shape in stage_token_counts(input_size, patch_embed1_stride))
