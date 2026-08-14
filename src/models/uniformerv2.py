"""UniFormerV2 (ViT-B/16) nạp trọng số **CLIP-400M → K710**, thích nghi cho MRI 8 pha.

Nguồn kiến trúc: https://github.com/OpenGVLab/UniFormerV2
(`slowfast/models/uniformerv2_model.py`, hàm `uniformerv2_b16`). Trọng số:
``k400+k710_uniformerv2_b16_8x224.pyth``. ⚠️ MODEL_ZOO chỉ định bản **K710 thuần** cho việc
này, nhưng bucket Aliyun của họ đã chết (mọi URL trả 404, kiểm 2026-08-14) — xem ghi chú ở
`PRETRAINED_FILENAMES`.

## Nó KHÁC UniFormer-S ở đâu, và vì sao điều đó quan trọng

`src/models/uniformer3d.py` là kim tự tháp 4 stage: conv MHRA ở stage 1–2, self-attention ở
3–4, hạ mẫu dần qua `patch_embed1..4`. UniFormerV2 là **ViT phẳng**: một ViT ảnh (CLIP) chạy
**theo từng lát**, cộng hai thứ gắn thêm —

* `lmhra1`/`lmhra2` — MHRA cục bộ, conv 3D depthwise trộn theo trục lát **bên trong** mỗi block;
* `dec` — bộ trích xuất cross-attention, để một `temporal_cls_token` học được hút thông tin từ
  bốn block cuối (`return_list`).

Hệ quả thực tế: **không dùng lại được gì của `uniformer3d.py`** — không `stage_token_counts`,
không cổng B theo stage, không `DROPPED_PREFIXES` cũ.

## Ba chỗ CỐ Ý lệch khỏi bản gốc, cả ba đều bắt buộc và đều phải ghi vào báo cáo

| chỗ | bản gốc | ở đây | vì sao |
|---|---|---|---|
| `conv1` | `Conv3d(3, …)` RGB | `Conv3d(8, …)` | 8 pha MRI vào làm **kênh** |
| `positional_embedding` | lưới 14×14 (224/16) | lưới 7×7 (112/16) | crop của ta là 112 |
| `transformer.proj.2` | 710 lớp | 7 lớp | taxonomy của bài toán |

⚠️ **Chỗ lệch thứ nhất là chỗ đắt nhất, và nó nặng hơn ở V2 so với ở UniFormer-S.** Trong một
ViT phẳng, `conv1` là lớp **duy nhất** biến pixel thành token; vứt nó đi là vứt toàn bộ đặc
trưng mức thấp của CLIP. Ở UniFormer-S, `patch_embed1` chỉ là một trong bốn và ba stage sau
vẫn nhận trọng số.

Giảm thiểu bằng `inflate_input_channels`: lấy **trung bình** trọng số 3 kênh RGB rồi lặp ra 8
kênh, nhân `3/8` để **tổng theo kênh không đổi** ⇒ thang kích hoạt giữ nguyên. Không hoàn hảo,
nhưng hơn hẳn khởi tạo ngẫu nhiên. Đây là chỗ **phải ghi rõ**, đừng để nó thành một chi tiết
lặng lẽ.

## Trục lát của ta = trục thời gian của model video

`forward` hoán vị ``[N,8,X,Y,Z] → [N,8,Z,X,Y]``, cùng quy ước với `uniformer3d.py`. Không có
tham số nào phụ thuộc số lát: `lmhra` là conv depthwise kernel 3 theo trục lát, `dpe` là conv
3D depthwise, `dec` là cross-attention với query học được. Cả ba **bất biến với `T`** về mặt
shape. Đã neo bằng test.

## Chế độ hỏng nguy hiểm nhất ở file này

Kiến trúc đúng nhưng **nối dây sai** — ví dụ `dec[j]` hút từ nhầm block, hay `dpe` áp sai thứ
tự trục. Loại lỗi đó **nạp trọng số thành công 100%**, train trơn, ra số hợp lý, và không có
gì báo. Bộ kiểm khoá không bắt được nó.

Vì vậy `missing_pretrained_keys` kiểm **tập khoá**, không kiểm tỉ lệ, và cổng A của notebook
đối chiếu tập khoá của model với tập khoá của checkpoint theo **cả hai chiều**. Đó là mức bảo
đảm cao nhất có được mà không train thử — và nó vẫn không phủ được phần nối dây, nên phần đó
được transcribe **nguyên văn** từ mã gốc thay vì viết lại theo ý mình.
"""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Iterable
from typing import Any

from src.models.resnet3d import resolve_pretrained_path
from src.models.uniformer3d import _drop_path, strip_state_dict

IN_CHANNELS = 8
NUM_CLASSES = 7

# Ba tiền tố KHÔNG khớp được về hình học — xem bảng ở docstring. Mọi khoá khác mà thiếu đều là
# dấu hiệu lệch kiến trúc, và phải nổ chứ không phải cảnh báo.
DROPPED_PREFIXES = ("conv1.", "positional_embedding", "transformer.proj.2.")

UNIFORMERV2_VARIANTS: dict[str, dict[str, Any]] = {
    # Khớp `uniformerv2_b16()` của họ.
    "b16": {
        "patch_size": 16,
        "width": 768,
        "layers": 12,
        "heads": 12,
        "return_list": (8, 9, 10, 11),
        "n_dim": 768,
        "n_head": 12,
    },
}

# ⚠️⚠️ CHỖ LỆCH BẮT BUỘC: đây là bản **K400+K710**, không phải K710 thuần.
#
# MODEL_ZOO của họ liệt kê `k710_uniformerv2_b16_8x224.pyth` — bản trung gian được chỉ định
# làm điểm khởi tạo cho finetune xuôi dòng, và đó là bản đáng dùng nhất cho chuyển giao xuyên
# miền. **Nhưng toàn bộ bucket Aliyun của họ đã chết**: mọi URL trong MODEL_ZOO trả 404
# (kiểm 2026-08-14, cả nhóm k710 lẫn k400).
#
# Bản còn sống là mirror trên HuggingFace của chính tác giả, và nó chỉ có bản **đã finetune
# thêm trên K400**. Chuỗi pretrain vì thế là CLIP-400M -> K710 -> K400 chứ không dừng ở K710.
#
# Hệ quả, phải ghi vào báo cáo: đặc trưng đã chuyên biệt hoá thêm một bước về 400 lớp hành
# động. Mức ảnh hưởng có lẽ nhỏ — ta bỏ hẳn đầu ra và finetune toàn mạng — nhưng đây là một
# chỗ lệch THẬT so với thứ đã đề xuất, không phải một chi tiết vụn.
PRETRAINED_FILENAMES: dict[str, str] = {
    "b16": "k400+k710_uniformerv2_b16_8x224.pyth",
}

# Mirror của tác giả UniFormerV2. Dấu `+` trong tên file hợp lệ trong đường dẫn URL (chỉ ở
# query string nó mới nghĩa là dấu cách), đã kiểm cả hai dạng đều trả 206.
PRETRAINED_BASE_URL = "https://huggingface.co/Andy1621/uniformerv2/resolve/main/"

# Dung lượng thật, để cell tải phân biệt được file thật với một trang lỗi.
PRETRAINED_SIZE_BYTES = 458_289_355

# Độ phân giải và lưới token lúc pretrain, dùng để nội suy `positional_embedding`.
PRETRAINED_RESOLUTION = 224

__all__ = [
    "DROPPED_PREFIXES",
    "IN_CHANNELS",
    "NUM_CLASSES",
    "PRETRAINED_BASE_URL",
    "PRETRAINED_FILENAMES",
    "PRETRAINED_RESOLUTION",
    "PRETRAINED_SIZE_BYTES",
    "UNIFORMERV2_VARIANTS",
    "build_uniformerv2",
    "load_clip_k710_weights",
    "missing_pretrained_keys",
    "token_layout",
    "variant_spec",
]


def variant_spec(variant: str) -> dict[str, Any]:
    """Tham số kiến trúc; nổ nếu tên sai thay vì im lặng chọn mặc định."""
    if variant not in UNIFORMERV2_VARIANTS:
        raise ValueError(
            f"model.variant phải thuộc {sorted(UNIFORMERV2_VARIANTS)}, nhận {variant!r}"
        )
    return dict(UNIFORMERV2_VARIANTS[variant])


def missing_pretrained_keys(missing: Iterable[str]) -> list[str]:
    """Khoá thiếu mà KHÔNG thuộc `DROPPED_PREFIXES` — dấu hiệu lệch kiến trúc.

    Hàm **thuần**, không cần torch: một cổng chặn không test được thì sẽ hỏng đúng lúc không
    ai nhìn.
    """
    return sorted(k for k in missing if not k.startswith(DROPPED_PREFIXES))


def token_layout(
    input_size: tuple[int, int, int], patch_size: int, temporal_downsample: bool
) -> dict[str, int]:
    """Số lát và số token sau `conv1`, để cổng B của notebook đối chiếu bằng tay.

    `input_size` là ``(D, H, W)`` **theo thứ tự của model** (D = trục lát).

    Tồn tại vì một cấu hình từng chạy suốt ở nửa độ phân giải mà **không có gì báo**: số token
    phải in ra và đọc bằng mắt trước khi cam kết GPU.
    """
    d, h, w = (int(v) for v in input_size)
    if h % patch_size or w % patch_size:
        raise ValueError(
            f"cạnh trong mặt phẳng {h}×{w} không chia hết cho patch_size {patch_size}; "
            "ViT phẳng không xử lý được phần dư"
        )
    t_out = d // 2 if temporal_downsample else d
    grid = h // patch_size
    return {
        "frames_in": d,
        "frames_after_conv1": t_out,
        "grid": grid,
        "tokens_per_frame": grid * grid + 1,
        "tokens_global_block": t_out * (grid * grid + 1),
    }


def inflate_input_channels(weight: Any, in_channels: int) -> Any:
    """Trọng số `conv1` từ 3 kênh RGB sang `in_channels` kênh MRI.

    Lấy trung bình theo trục kênh vào rồi lặp lại, nhân ``3 / in_channels`` để **tổng theo kênh
    không đổi**. Nhờ đó thang kích hoạt đi vào block đầu giữ nguyên; nếu chỉ lặp mà không chia
    thì kích hoạt bị nhân lên ``in_channels / 3`` và `ln_pre` phải hấp thụ một cú lệch thang mà
    nó chưa từng thấy lúc pretrain.

    Chấp cả trọng số 4 chiều (conv 2D của CLIP gốc) lẫn 5 chiều (checkpoint đã là 3D).
    """
    if weight.ndim == 4:  # (out, 3, kh, kw) — chưa thổi theo trục thời gian
        weight = weight.unsqueeze(2)
    if weight.ndim != 5:
        raise ValueError(f"conv1 phải 4 hoặc 5 chiều, nhận shape {tuple(weight.shape)}")
    c_in = weight.shape[1]
    if c_in == in_channels:
        return weight
    mean = weight.mean(dim=1, keepdim=True)
    return mean.repeat(1, in_channels, 1, 1, 1) * (c_in / in_channels)


def interpolate_position_embedding(weight: Any, grid: int) -> Any:
    """Nội suy `positional_embedding` từ lưới lúc pretrain sang lưới của ta.

    Trọng số có dạng ``(1 + g0*g0, width)``: một token lớp rồi ``g0×g0`` token không gian.
    Token lớp giữ nguyên; phần không gian nội suy song khối (bicubic) — cùng cách ViT vẫn dùng
    khi đổi độ phân giải.

    ⚠️ Với crop 112 và patch 16 thì ``g0 = 14 → grid = 7``, tức **giữ lại 49 trên 196 token**.
    Đây là mất mát thật, không phải một phép đổi shape vô hại: tiên nghiệm không gian của CLIP
    bị lấy mẫu thưa đi bốn lần. Cách tránh duy nhất là dựng cache ở 224 in-plane — nhưng đó là
    một biến nữa, xem config.
    """
    import torch
    import torch.nn.functional as functional

    n_tok, width = weight.shape
    g0 = int(round((n_tok - 1) ** 0.5))
    if g0 * g0 + 1 != n_tok:
        raise ValueError(f"positional_embedding {n_tok} token không phải 1 + lưới vuông")
    if g0 == grid:
        return weight
    cls_tok, spatial = weight[:1], weight[1:]
    spatial = spatial.reshape(1, g0, g0, width).permute(0, 3, 1, 2)
    spatial = functional.interpolate(
        spatial.float(), size=(grid, grid), mode="bicubic", align_corners=False
    )
    spatial = spatial.permute(0, 2, 3, 1).reshape(grid * grid, width).to(weight.dtype)
    return torch.cat([cls_tok, spatial], dim=0)


def build_uniformerv2(
    variant: str = "b16",
    in_channels: int = IN_CHANNELS,
    num_classes: int = NUM_CLASSES,
    input_resolution: int = 112,
    t_size: int = 14,
    temporal_downsample: bool = True,
    dw_reduction: float = 1.5,
    no_lmhra: bool = False,
    double_lmhra: bool = True,
    mlp_factor: float = 4.0,
    mlp_dropout: float = 0.5,
    cls_dropout: float = 0.5,
    backbone_drop_path_rate: float = 0.0,
    drop_path_rate: float = 0.0,
    pretrained_path: str | None = None,
    require_pretrained: bool = True,
) -> Any:
    """Dựng UniFormerV2 cho đầu vào ``[N, in_channels, X, Y, Z]``.

    `t_size` là **số lát trước** `conv1`. Nếu `temporal_downsample` thì `conv1` stride 2 theo
    trục lát và số lát vào transformer còn một nửa — hàm tự tính, chỗ gọi không phải nhẩm.
    """
    import torch
    from torch import nn

    spec = variant_spec(variant)
    patch_size = int(spec["patch_size"])
    width = int(spec["width"])
    layers = int(spec["layers"])
    heads = int(spec["heads"])
    return_list = tuple(int(i) for i in spec["return_list"])
    n_dim = int(spec["n_dim"])
    n_head = int(spec["n_head"])
    n_layers = len(return_list)

    layout = token_layout(
        (t_size, input_resolution, input_resolution), patch_size, temporal_downsample
    )
    t_down = layout["frames_after_conv1"]
    grid = layout["grid"]

    class LayerNorm(nn.LayerNorm):
        """Chuẩn hoá ở fp32 rồi trả về dtype cũ — bản của CLIP.

        Bắt buộc giữ: dưới AMP fp16, LayerNorm tính thẳng ở fp16 mất ổn định số học, và đó là
        lý do CLIP tự định nghĩa lớp này thay vì dùng `nn.LayerNorm` trần.
        """

        def forward(self, x: Any) -> Any:
            return super().forward(x.float()).type(x.dtype)

    class QuickGELU(nn.Module):
        def forward(self, x: Any) -> Any:
            return x * torch.sigmoid(1.702 * x)

    class DropPath(nn.Module):
        def __init__(self, p: float) -> None:
            super().__init__()
            self.p = float(p)

        def forward(self, x: Any) -> Any:
            return _drop_path(x, self.p, self.training)

    class LocalMHRA(nn.Module):
        """Conv 3D depthwise trộn theo trục lát, đặt **bên trong** mỗi block ViT.

        `pos_embed[3]` khởi tạo bằng 0 để lúc bắt đầu nhánh này là ánh xạ đồng nhất — nhờ vậy
        model khởi động đúng bằng ViT ảnh pretrained, rồi mới học dần phần theo lát.
        """

        def __init__(self, d_model: int, dw_reduction: float = 1.5, pos_kernel_size: int = 3):
            super().__init__()
            padding = pos_kernel_size // 2
            re_d = int(d_model // dw_reduction)
            self.pos_embed = nn.Sequential(
                nn.BatchNorm3d(d_model),
                nn.Conv3d(d_model, re_d, kernel_size=1),
                nn.Conv3d(
                    re_d,
                    re_d,
                    kernel_size=(pos_kernel_size, 1, 1),
                    padding=(padding, 0, 0),
                    groups=re_d,
                ),
                nn.Conv3d(re_d, d_model, kernel_size=1),
            )
            nn.init.constant_(self.pos_embed[3].weight, 0)
            nn.init.constant_(self.pos_embed[3].bias, 0)

        def forward(self, x: Any) -> Any:
            return self.pos_embed(x)

    class ResidualAttentionBlock(nn.Module):
        def __init__(self, d_model: int, n_head_: int, drop_path: float = 0.0):
            super().__init__()
            self.drop_path = DropPath(drop_path) if drop_path > 0 else nn.Identity()
            self.no_lmhra = no_lmhra
            self.double_lmhra = double_lmhra
            if not no_lmhra:
                self.lmhra1 = LocalMHRA(d_model, dw_reduction=dw_reduction)
                if double_lmhra:
                    self.lmhra2 = LocalMHRA(d_model, dw_reduction=dw_reduction)
            self.attn = nn.MultiheadAttention(d_model, n_head_)
            self.ln_1 = LayerNorm(d_model)
            self.mlp = nn.Sequential(
                OrderedDict(
                    [
                        ("c_fc", nn.Linear(d_model, d_model * 4)),
                        ("gelu", QuickGELU()),
                        ("c_proj", nn.Linear(d_model * 4, d_model)),
                    ]
                )
            )
            self.ln_2 = LayerNorm(d_model)

        def _mix_slices(self, x: Any, lmhra: Any, t: int) -> Any:
            """Gấp token về khối 3D, trộn theo lát, rồi trải lại. Token lớp không tham gia."""
            tmp = x[1:, :, :]
            length, nt, c = tmp.shape
            n = nt // t
            h = w = int(length**0.5)
            tmp = tmp.view(h, w, n, t, c).permute(2, 4, 3, 0, 1).contiguous()
            tmp = tmp + self.drop_path(lmhra(tmp))
            tmp = tmp.view(n, c, t, length).permute(3, 0, 2, 1).contiguous().view(length, nt, c)
            return torch.cat([x[:1, :, :], tmp], dim=0)

        def forward(self, x: Any, t: int) -> Any:
            if not self.no_lmhra:
                x = self._mix_slices(x, self.lmhra1, t)
            y = self.ln_1(x)
            x = x + self.drop_path(self.attn(y, y, y, need_weights=False)[0])
            if not self.no_lmhra and self.double_lmhra:
                x = self._mix_slices(x, self.lmhra2, t)
            return x + self.drop_path(self.mlp(self.ln_2(x)))

    class Extractor(nn.Module):
        """Cross-attention: query là `temporal_cls_token`, key/value là token của một block.

        ⚠️ `attention` được viết tay thay vì gọi `nn.MultiheadAttention.forward` vì query và
        key/value có **độ dài khác nhau** và bản gốc cắt `in_proj_weight` bằng tay. Giữ nguyên
        cách cắt đó — đổi sang API chuẩn sẽ ra kết quả khác trong khi trọng số vẫn nạp được.
        """

        def __init__(self, d_model: int, n_head_: int, dropout: float, drop_path: float):
            super().__init__()
            self.drop_path = DropPath(drop_path) if drop_path > 0 else nn.Identity()
            self.attn = nn.MultiheadAttention(d_model, n_head_)
            self.ln_1 = nn.LayerNorm(d_model)
            d_mlp = round(mlp_factor * d_model)
            self.mlp = nn.Sequential(
                OrderedDict(
                    [
                        ("c_fc", nn.Linear(d_model, d_mlp)),
                        ("gelu", QuickGELU()),
                        ("dropout", nn.Dropout(dropout)),
                        ("c_proj", nn.Linear(d_mlp, d_model)),
                    ]
                )
            )
            self.ln_2 = nn.LayerNorm(d_model)
            self.ln_3 = nn.LayerNorm(d_model)
            nn.init.xavier_uniform_(self.attn.in_proj_weight)
            nn.init.constant_(self.attn.out_proj.weight, 0.0)
            nn.init.constant_(self.attn.out_proj.bias, 0.0)
            nn.init.xavier_uniform_(self.mlp[0].weight)
            nn.init.constant_(self.mlp[-1].weight, 0.0)
            nn.init.constant_(self.mlp[-1].bias, 0.0)

        def attention(self, x: Any, y: Any) -> Any:
            d = self.ln_1.weight.size(0)
            q = (x @ self.attn.in_proj_weight[:d].T) + self.attn.in_proj_bias[:d]
            k = (y @ self.attn.in_proj_weight[d:-d].T) + self.attn.in_proj_bias[d:-d]
            v = (y @ self.attn.in_proj_weight[-d:].T) + self.attn.in_proj_bias[-d:]
            tx, ty, n = q.size(0), k.size(0), q.size(1)
            nh, hd = self.attn.num_heads, self.attn.head_dim
            q = q.view(tx, n, nh, hd).permute(1, 2, 0, 3)
            k = k.view(ty, n, nh, hd).permute(1, 2, 0, 3)
            v = v.view(ty, n, nh, hd).permute(1, 2, 0, 3)
            aff = (q @ k.transpose(-2, -1) / (hd**0.5)).softmax(dim=-1)
            out = (aff @ v).permute(2, 0, 1, 3).flatten(2)
            return self.attn.out_proj(out)

        def forward(self, x: Any, y: Any) -> Any:
            x = x + self.drop_path(self.attention(self.ln_1(x), self.ln_3(y)))
            return x + self.drop_path(self.mlp(self.ln_2(x)))

    class Transformer(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.t = t_down
            self.return_list = return_list
            b_dpr = [x.item() for x in torch.linspace(0, backbone_drop_path_rate, max(layers, 1))]
            self.resblocks = nn.ModuleList(
                [ResidualAttentionBlock(width, heads, b_dpr[i]) for i in range(layers)]
            )
            self.temporal_cls_token = nn.Parameter(torch.zeros(1, 1, n_dim))
            self.dpe = nn.ModuleList(
                [
                    nn.Conv3d(n_dim, n_dim, kernel_size=3, padding=1, groups=n_dim)
                    for _ in range(n_layers)
                ]
            )
            for m in self.dpe:
                nn.init.constant_(m.bias, 0.0)
            dpr = [x.item() for x in torch.linspace(0, drop_path_rate, max(n_layers, 1))]
            self.dec = nn.ModuleList(
                [Extractor(n_dim, n_head, mlp_dropout, dpr[i]) for i in range(n_layers)]
            )
            self.proj = nn.Sequential(
                nn.LayerNorm(n_dim), nn.Dropout(cls_dropout), nn.Linear(n_dim, num_classes)
            )
            self.balance = nn.Parameter(torch.zeros(n_dim))

        def forward(self, x: Any) -> Any:
            t = self.t
            length, nt, c = x.shape
            n = nt // t
            h = w = int((length - 1) ** 0.5)
            cls_token = self.temporal_cls_token.repeat(1, n, 1)

            j = -1
            for i, block in enumerate(self.resblocks):
                x = block(x, t)
                if i in self.return_list:
                    j += 1
                    tmp = x.clone().view(length, n, t, c)
                    feats = tmp[1:].permute(1, 3, 2, 0).reshape(n, c, t, h, w)
                    feats = (
                        self.dpe[j](feats.clone())
                        .view(n, c, t, length - 1)
                        .permute(3, 0, 2, 1)
                        .contiguous()
                    )
                    tmp[1:] = tmp[1:] + feats
                    cls_token = self.dec[j](cls_token, tmp.permute(2, 0, 1, 3).flatten(0, 1))

            weight_ = torch.sigmoid(self.balance)
            residual = x.view(length, n, t, c)[0].mean(1)
            return self.proj((1 - weight_) * cls_token[0, :, :] + weight_ * residual)

    class UniFormerV2(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            if temporal_downsample:
                self.conv1 = nn.Conv3d(
                    in_channels,
                    width,
                    (3, patch_size, patch_size),
                    (2, patch_size, patch_size),
                    (1, 0, 0),
                    bias=False,
                )
            else:
                self.conv1 = nn.Conv3d(
                    in_channels,
                    width,
                    (1, patch_size, patch_size),
                    (1, patch_size, patch_size),
                    bias=False,
                )
            scale = width**-0.5
            self.class_embedding = nn.Parameter(scale * torch.randn(width))
            self.positional_embedding = nn.Parameter(scale * torch.randn(grid * grid + 1, width))
            self.ln_pre = LayerNorm(width)
            self.transformer = Transformer()

        def forward(self, x: Any) -> Any:
            # [N, C, X, Y, Z] -> [N, C, Z, X, Y]: trục lát vào vai trục thời gian, đúng như
            # `uniformer3d.py`. Kernel theo thời gian của `lmhra`/`dpe` nhờ đó thấy trục lát.
            x = x.permute(0, 1, 4, 2, 3)
            x = self.conv1(x)
            n, c, t, h, w = x.shape
            x = x.permute(0, 2, 3, 4, 1).reshape(n * t, h * w, c)
            cls = self.class_embedding.to(x.dtype) + torch.zeros(
                x.shape[0], 1, x.shape[-1], dtype=x.dtype, device=x.device
            )
            x = torch.cat([cls, x], dim=1) + self.positional_embedding.to(x.dtype)
            x = self.ln_pre(x).permute(1, 0, 2)
            return self.transformer(x)

    model = UniFormerV2()

    path = resolve_pretrained_path(pretrained_path)
    if path is None or not path.exists():
        if require_pretrained:
            raise FileNotFoundError(
                "Không tìm thấy trọng số CLIP→K710. Đặt env LLDMMRI_PRETRAINED_PATH hoặc "
                f"model.pretrained_path. Tải: {PRETRAINED_BASE_URL}"
                f"{PRETRAINED_FILENAMES[variant]}. Cả thí nghiệm này TỒN TẠI để đo tác dụng "
                "của pretrained — chạy nó không trọng số là một thí nghiệm KHÁC mà không có "
                "gì báo."
            )
        return model

    load_clip_k710_weights(model, path, in_channels=in_channels, grid=grid)
    return model


def load_clip_k710_weights(
    model: Any, path: Any, in_channels: int = IN_CHANNELS, grid: int = 7
) -> dict[str, list[str]]:
    """Nạp checkpoint K710, thích nghi ba khoá lệch, rồi **chặn nếu lệch kiến trúc**.

    Trả về ``{"missing", "unexpected", "loaded", "adapted"}`` để cổng A in ra.

    Ba việc thích nghi, tất cả đều được ghi vào ``adapted`` để cổng A đọc được:

    1. ``conv1.weight`` — thổi 3 kênh RGB thành `in_channels` kênh MRI;
    2. ``positional_embedding`` — nội suy lưới 14×14 xuống ``grid×grid``;
    3. ``transformer.proj.2.*`` — bỏ hẳn, vì số lớp khác.

    ⚠️ File ``.pyth`` là checkpoint của **PySlowFast**, không phải `state_dict` phẳng — phải
    bóc khoá ``model_state``. `strip_state_dict` dùng lại từ `uniformer3d.py` làm đúng việc đó
    và cũng gỡ tiền tố ``module.`` của DataParallel.
    """
    import torch

    raw = torch.load(path, map_location="cpu", weights_only=False)
    state = strip_state_dict(raw)
    dich = model.state_dict()
    adapted: list[str] = []

    if "conv1.weight" in state:
        w = state["conv1.weight"]
        if w.shape != dich["conv1.weight"].shape:
            w = inflate_input_channels(w, in_channels)
            adapted.append(f"conv1.weight {tuple(state['conv1.weight'].shape)} -> {tuple(w.shape)}")
        state["conv1.weight"] = w

    if "positional_embedding" in state:
        p = state["positional_embedding"]
        if p.shape != dich["positional_embedding"].shape:
            p = interpolate_position_embedding(p, grid)
            adapted.append(
                f"positional_embedding {tuple(state['positional_embedding'].shape)} "
                f"-> {tuple(p.shape)}"
            )
        state["positional_embedding"] = p

    # Bỏ mọi khoá còn lệch shape. Ở đây chỉ nên còn đầu ra phân lớp; nếu có khoá khác lọt vào
    # danh sách này thì đó là dấu hiệu lệch kiến trúc và cổng A phải thấy nó.
    lech_shape = [k for k, v in state.items() if k in dich and v.shape != dich[k].shape]
    for k in lech_shape:
        adapted.append(f"BỎ {k} {tuple(state[k].shape)} != {tuple(dich[k].shape)}")
        state.pop(k)

    report = model.load_state_dict(state, strict=False)
    missing = list(report.missing_keys)
    unexpected = list(report.unexpected_keys)

    la = missing_pretrained_keys(missing)
    if la:
        raise RuntimeError(
            f"{len(la)} khoá thiếu ngoài {DROPPED_PREFIXES}: {la[:12]}\n"
            "Đây là lệch KIẾN TRÚC, không phải lệch cấu hình. `strict=False` sẽ không báo gì "
            "và model vẫn train ra số hợp lý — nên dừng ở đây."
        )

    loaded = sorted(set(state) - set(unexpected))
    return {
        "missing": sorted(missing),
        "unexpected": sorted(unexpected),
        "loaded": loaded,
        "adapted": adapted,
    }
