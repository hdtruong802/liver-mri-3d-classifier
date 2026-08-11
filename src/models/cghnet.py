"""CGHNet — Cross-Guided 2D–3D Hybrid Network, tái lập từ bài báo.

Nguồn: Li, Sailike, Li, Zhang, Shang, Chen, *CGHNet: Cross-Guided 2D–3D Hybrid Network
with attention mechanism for focal liver lesion classification*, Computerized Medical
Imaging and Graphics **132** (2026) 102780, doi:10.1016/j.compmedimag.2026.102780.
Bài đo trên **đúng test-104 official** của LLD-MMRI2023 và báo macro-F1 **0.818**.

## ⚠️ Đây là TÁI LẬP TỪ VĂN BẢN, không phải chạy lại code của tác giả

Bài **không công khai code** (mục Data availability chỉ ghi *"Data will be made available
on request"*). Và bài **không nói** những siêu tham số sau:

- **ViT: độ sâu, số chiều, patch, head.** Ta dùng depth 6 · dim 384 · patch 16 · 6 head,
  chọn để khớp tổng tham số 59.37M mà Bảng 5 của họ công bố.
- **Độ sâu ResNet-3D.** Ta dùng **ResNet-50-3D**: hàng `ResNet3D` của họ là 46.22M, khớp
  đúng biến thể đó (Hara). ResNet-18-3D là 33M (ta đã đo 33.14M), ResNet-34-3D ~63M.
- **`K` của attention pooling.** Ta dùng 7 = `num_classes`, theo câu *"projects each fused
  patch to a class logit vector"*.
- **`γ`, `α` của Focal Loss.** Ta dùng γ=2, α đều — mặc định của Lin và cs.
- **Chiều token nhánh 3D vào CGFM.** Ta chiếu 2048 → 384; không chiếu thì riêng
  `W_fuse,3D` đã 8.4M và tổng vượt 59.37M.

**Bằng chứng gián tiếp cho bộ suy luận trên: tổng tham số khớp gần khít.** Đếm tay từng
khối với mặc định của module này cho **59.02M** so với **59.37M** của Bảng 5, lệch −0.6%::

    ViT (patch-embed + 6 block + pos/cls + norm)      10.83M
    ResNet-50-3D (conv1 8 kênh, không có fc)          46.36M
    token_proj 2048->384 + CGFM + pool + heads + β     1.84M
    ------------------------------------------------ -------
    tổng                                              59.02M   (bài: 59.37M)

Đó không chứng minh ta dựng đúng kiến trúc của họ, nhưng nếu chọn ResNet-18-3D (33M) hay
ResNet-34-3D (63M), hoặc không chiếu 2048→384, thì tổng lệch hàng chục triệu.

**Cổng A của notebook in số tham số thật cạnh 59.37M.** Lệch nhiều nghĩa là bản tái lập
khác kiến trúc gốc, và mọi so sánh với 0.818 phải nói rõ điều đó.

## Thang bậc tự chẩn đoán — lý do bản tái lập này well-posed

Bài train bằng **multi-head deep supervision**: `L = FL(ŷ) + FL(ŷ_2D) + FL(ŷ_3D)` (Eq. 12).
Nên **một lần chạy cho ba con số**, và cả ba có mốc công bố (Bảng 2, trên test-104):

    nhánh 3D một mình   0.724      lệch xuống ~0.62  =>  sai PROTOCOL/DỮ LIỆU, không phải fusion
    nhánh 2D một mình   0.742      lệch nhiều        =>  sai nhánh ViT
    hợp nhất (CGHNet)   0.818      hai nhánh đúng mà cái này thấp  =>  sai CGFM/ADF

Đây là thang bậc chẩn đoán **không tốn thêm giờ GPU nào**, và nó bao trọn phép thử "hình
học 14×112×112 có phải nút thắt không" — biến lớn nhất dự án chưa thử (mọi thí nghiệm đều
z=32 hoặc 48, còn cả baseline official lẫn CGHNet đều z=16).

## Hợp đồng đầu ra — cố ý phụ thuộc chế độ train/eval

- ``model.train()`` → **dict** ``{"main": [B,7], "aux": {"2d": [B,7], "3d": [B,7]}}``
- ``model.eval()``  → **tensor** ``[B,7]`` (chỉ logits chính)

Nhờ vậy **toàn bộ `src/eval/*` không phải sửa**: `mc_dropout.enable_dropout` gọi
`model.eval()` rồi chỉ bật lại riêng các lớp `Dropout` (nên `self.training` của module gốc
vẫn `False`), còn `tta.py` và `xai/gradcam.py` đều gọi `model.eval()`.

⚠️ Kiểu trả về đổi theo chế độ là thứ dễ gây bất ngờ, nên nó có test riêng
(`tests/test_cghnet.py`). Nếu ai đó cần dict ở eval thì gọi `forward_heads()` tường minh.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

NUM_PHASES = 8
SPATIAL_DIMS = 3

# Số tham số bài báo công bố (Bảng 5). Cổng của notebook đối chiếu với con số này.
PAPER_PARAMS_M = 59.37
PAPER_FLOPS_G = 209.91

# Mốc macro-F1 trên test-104, Bảng 1 và Bảng 2. Dùng để đọc thang bậc chẩn đoán.
PAPER_F1 = {"3d": 0.724, "2d": 0.742, "main": 0.818}

# λ_res của ADF. Bài quét 0.1–0.9 (Bảng 6) và chốt 0.50; hai đầu đều tệ hơn.
DEFAULT_LAMBDA_RES = 0.50

__all__ = [
    "DEFAULT_LAMBDA_RES",
    "PAPER_F1",
    "PAPER_FLOPS_G",
    "PAPER_PARAMS_M",
    "build_cghnet",
    "resnet3d_feature_dim",
]

# Số kênh của feature map `layer4` = ``block_inplanes[3] * block.expansion``.
# Bottleneck (resnet50+) expansion 4; BasicBlock (resnet10/18/34) expansion 1.
_RESNET_FEATURE_DIM: dict[int, int] = {10: 512, 18: 512, 34: 512, 50: 2048, 101: 2048}


def resnet3d_feature_dim(depth: int) -> int:
    """Số kênh feature map `layer4` của ResNet-3D độ sâu này."""
    if depth not in _RESNET_FEATURE_DIM:
        raise ValueError(f"chưa biết số kênh của resnet{depth}. Có: {sorted(_RESNET_FEATURE_DIM)}")
    return _RESNET_FEATURE_DIM[depth]


def build_cghnet(
    num_phases: int = NUM_PHASES,
    num_classes: int = 7,
    embed_dim: int = 384,
    depth: int = 6,
    num_heads: int = 6,
    patch_size: int = 16,
    mlp_ratio: float = 4.0,
    resnet_depth: int = 50,
    token_dim: int = 384,
    conv1_stride: int | Sequence[int] = 1,
    dropout_prob: float = 0.2,
    attn_pool_dim: int | None = None,
    lambda_res: float = DEFAULT_LAMBDA_RES,
    in_plane_size: int = 112,
) -> Any:
    """Dựng CGHNet nhận ``[B, num_phases, X, Y, Z]`` → logits ``[B, num_classes]``.

    Tham số:
        embed_dim, depth, num_heads, patch_size, mlp_ratio: nhánh ViT. **Bài không nói**
            các giá trị này; mặc định ở đây được chọn để tổng tham số khớp 59.37M.
        resnet_depth: nhánh 3D. 50 suy từ hàng `ResNet3D` 46.22M của bài.
        token_dim: số chiều token của nhánh 3D **sau khi chiếu** từ
            ``resnet3d_feature_dim(resnet_depth)``. Bài không nói có chiếu hay không;
            không chiếu thì riêng `W_fuse,3D` (4096→2048) đã 8.4M và tổng vượt 59.37M.
        conv1_stride: stride conv1 của nhánh 3D. ⚠️ Thứ tự trục là ``[X, Y, Z]``, nên
            ``[2, 2, 1]`` là "hạ mẫu trong mặt phẳng, giữ z". Với đầu vào 112×112×14 và
            stride 1, vết không gian là::

                conv1 112×112×14 -> maxpool 56×56×7 -> 28×28×4 -> 14×14×2 -> layer4 7×7×1

            ⇒ ``N_v = 49`` token. Trục z co về 1 ở `layer4` là **tất yếu** của z=14 với 16
            lần hạ mẫu, không phải lỗi.
        attn_pool_dim: ``K`` của attention pooling. ``None`` = `num_classes`, theo câu
            *"projects each fused patch to a class logit vector"* của bài.
        lambda_res: hệ số hiệu chỉnh dư của ADF (Eq. 11). Bài chốt 0.50.
        in_plane_size: cạnh trong mặt phẳng của khối **model nhận** (``data.crop_size[0]``).
            Chỉ dùng để cấp phát `pos_embed` **trong `__init__`** — xem 🐛 dưới đây.

    🐛 **LỖI ĐÃ SỬA 2026-08-11 (WORKLOG S-126) — `pos_embed` chưa bao giờ được học.**

    Bản trước cấp phát ``self.pos_embed`` **lười, trong `forward`**, vì số patch phụ thuộc
    kích thước ảnh. Nhưng `src/train/run.py` dựng optimizer ở dòng ``AdamW(build_param_groups(
    model, ...))`` **trước** lần forward đầu, nên `pos_embed` sinh ra *sau khi* optimizer đã
    chụp xong danh sách tham số:

    * `nn.Module.__setattr__` **có** đăng ký nó ⇒ nó xuất hiện trong `state_dict()` và trong
      `best.pt`, nên nhìn checkpoint thì thấy đủ và không có gì đáng ngờ;
    * nhưng nó **không nằm trong param group nào** ⇒ **không bao giờ nhận một bước cập nhật**.

    Suốt 300 epoch của fold 1, positional embedding là **nhiễu ngẫu nhiên đóng băng**
    (``trunc_normal_(std=0.02)``), trong khi bài nói rõ *"supplemented by **learnable**
    positional embeddings E_pos"*. Không lỗi nào nổ, không cảnh báo nào in ra.

    ⚠️ **Hệ quả: con số CGHNet fold 1 = 0.6935 là của bản CÓ LỖI.** Nó không so trực tiếp
    được với bất kỳ run nào sau khi sửa. Muốn có mốc CGHNet đúng thì phải train lại.

    `tests/test_models.py::test_khong_model_nao_sinh_tham_so_moi_khi_forward` chặn cả **lớp**
    lỗi này cho mọi model trong `_BUILDERS`, không chỉ cho CGHNet.
    """
    # Kiểm tham số TRƯỚC khi import torch, để cấu hình sai nổ ngay ở local.
    if embed_dim % num_phases != 0:
        raise ValueError(
            f"embed_dim={embed_dim} phải chia hết cho num_phases={num_phases}: patch-embed "
            "dùng chung sinh embed_dim/num_phases chiều cho mỗi thì rồi concat theo trục thì "
            "(bài §3.2), nên phép concat phải ra đúng embed_dim."
        )
    if embed_dim % num_heads != 0:
        raise ValueError(f"embed_dim={embed_dim} phải chia hết cho num_heads={num_heads}")
    if lambda_res < 0.0:
        raise ValueError(f"lambda_res phải >= 0, nhận {lambda_res}")
    feature_dim = resnet3d_feature_dim(resnet_depth)
    pool_dim = num_classes if attn_pool_dim is None else int(attn_pool_dim)

    import torch
    from monai.networks.nets import resnet as monai_resnet
    from torch import nn

    class TransformerBlock(nn.Module):
        """Pre-LN block: MSA rồi MLP, mỗi cái có kết nối dư (bài Eq. 1)."""

        def __init__(self) -> None:
            super().__init__()
            self.norm1 = nn.LayerNorm(embed_dim)
            self.attn = nn.MultiheadAttention(
                embed_dim, num_heads, dropout=dropout_prob, batch_first=True
            )
            self.norm2 = nn.LayerNorm(embed_dim)
            hidden = int(embed_dim * mlp_ratio)
            self.mlp = nn.Sequential(
                nn.Linear(embed_dim, hidden),
                nn.GELU(),
                nn.Dropout(dropout_prob),
                nn.Linear(hidden, embed_dim),
                nn.Dropout(dropout_prob),
            )

        def forward(self, x: Any) -> Any:
            h = self.norm1(x)
            x = x + self.attn(h, h, h, need_weights=False)[0]
            return x + self.mlp(self.norm2(x))

    class AttentionPool(nn.Module):
        """Attention pooling *uncertainty-aware* của bài (Eq. 2–5).

        Điểm quan trọng và dễ làm sai: điểm số của mỗi token **không** phải một scalar
        học trực tiếp, mà là **chuẩn L2 của một vector logit `K` chiều**. Bài lý giải
        rằng độ lớn ``‖P‖₂`` là proxy cho độ tự tin dự đoán — token nào kích hoạt mạnh
        thì đóng góp nhiều. Thay bằng `Linear(dim, 1)` là một module khác, không phải
        module này.
        """

        def __init__(self, dim: int) -> None:
            super().__init__()
            self.score = nn.Linear(dim, pool_dim)

        def forward(self, tokens: Any) -> tuple[Any, Any]:
            logits = self.score(tokens)  # [B, L, K]
            scores = torch.linalg.vector_norm(logits, ord=2, dim=-1)  # [B, L]
            weights = scores.softmax(dim=1)
            pooled = (tokens * weights.unsqueeze(-1)).sum(dim=1)  # [B, dim]
            return pooled, weights

    class CrossGuidedFusion(nn.Module):
        """CGFM (bài Eq. 6–8): cổng **chéo**, không phải tự hiệu chỉnh kiểu SE.

        Mỗi nhánh sinh một descriptor toàn cục bằng GAP trên trục chuỗi, descriptor đó
        đi qua MLP + sigmoid thành một cổng theo kênh, rồi cổng đó nhân vào **nhánh đối
        diện**. Đây là chỗ khác Squeeze-and-Excitation: SE tự nhân vào chính mình, còn
        ở đây thông tin đi ngang qua khe ngữ nghĩa giữa ViT và CNN.
        """

        def __init__(self) -> None:
            super().__init__()
            self.gate_2to3 = nn.Sequential(nn.Linear(embed_dim, token_dim), nn.Sigmoid())
            self.gate_3to2 = nn.Sequential(nn.Linear(token_dim, embed_dim), nn.Sigmoid())
            self.fuse_2d = nn.Linear(embed_dim * 2, embed_dim)
            self.fuse_3d = nn.Linear(token_dim * 2, token_dim)

        def forward(self, z2d: Any, z3d: Any) -> tuple[Any, Any]:
            g2d = z2d.mean(dim=1)  # [B, embed_dim]
            g3d = z3d.mean(dim=1)  # [B, token_dim]
            gamma_2to3 = self.gate_2to3(g2d).unsqueeze(1)  # [B, 1, token_dim]
            gamma_3to2 = self.gate_3to2(g3d).unsqueeze(1)  # [B, 1, embed_dim]
            # Nhân cổng CHÉO rồi nối dư với bản gốc để không mất danh tính đặc trưng.
            fused_2d = self.fuse_2d(torch.cat([z2d, z2d * gamma_3to2], dim=-1))
            fused_3d = self.fuse_3d(torch.cat([z3d, z3d * gamma_2to3], dim=-1))
            return fused_2d, fused_3d

    class CGHNet(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.num_phases = num_phases
            self.num_classes = num_classes
            self.lambda_res = float(lambda_res)
            # Giữ lại để soi, không tham gia đồ thị đạo hàm.
            self.last_slice_weights: Any = None
            self.last_voxel_weights: Any = None
            self.last_beta: Any = None

            # --- nhánh 2D: patch-embed DÙNG CHUNG cho từng thì (bài §3.2) ---
            per_phase_dim = embed_dim // num_phases
            self.patch_embed = nn.Conv2d(
                1, per_phase_dim, kernel_size=patch_size, stride=patch_size
            )
            self.patch_size = patch_size
            # Chiếu sau khi concat theo trục thì, "to align with the latent dimension".
            self.modality_proj = nn.Linear(embed_dim, embed_dim)
            self.cls_token = nn.Parameter(torch.zeros(1, 1, embed_dim))
            # `pos_embed` cấp phát NGAY Ở ĐÂY, không lười trong forward. Cấp phát lười làm
            # nó sinh ra sau khi optimizer đã chụp `model.parameters()` ⇒ không bao giờ được
            # học. Xem 🐛 ở docstring của `build_cghnet`.
            n_patch = (in_plane_size // patch_size) ** 2
            self.n_token = n_patch + 1  # + cls token
            self.pos_embed = nn.Parameter(torch.zeros(1, self.n_token, embed_dim))
            nn.init.trunc_normal_(self.pos_embed, std=0.02)
            self.blocks = nn.ModuleList(TransformerBlock() for _ in range(depth))
            self.norm_2d = nn.LayerNorm(embed_dim)

            # --- nhánh 3D: ResNet-3D, lấy feature map layer4 ---
            stride = (
                int(conv1_stride)
                if isinstance(conv1_stride, int)
                else tuple(int(s) for s in conv1_stride)
            )
            factory = getattr(monai_resnet, f"resnet{resnet_depth}", None)
            if factory is None:
                raise ValueError(f"MONAI không có resnet{resnet_depth}")
            # `feed_forward=False` để không dựng `fc`; ta gọi tay các submodule vì
            # `ResNet.forward` kết thúc bằng avgpool + flatten, mà ta cần feature MAP.
            self.resnet = factory(
                spatial_dims=SPATIAL_DIMS,
                n_input_channels=num_phases,
                shortcut_type="B",
                bias_downsample=False,
                conv1_t_stride=stride,
                feed_forward=False,
            )
            self.token_proj = (
                nn.Identity() if feature_dim == token_dim else nn.Linear(feature_dim, token_dim)
            )

            # --- hợp nhất ---
            self.cgfm = CrossGuidedFusion()
            self.pool_2d = AttentionPool(embed_dim)
            self.pool_3d = AttentionPool(token_dim)

            # --- ADF (bài Eq. 9–11) ---
            joint = embed_dim + token_dim
            drop = nn.Dropout
            self.head_2d = nn.Sequential(drop(dropout_prob), nn.Linear(embed_dim, num_classes))
            self.head_3d = nn.Sequential(drop(dropout_prob), nn.Linear(token_dim, num_classes))
            self.head_fus = nn.Sequential(drop(dropout_prob), nn.Linear(joint, num_classes))
            self.gate_beta = nn.Sequential(
                nn.Linear(joint, joint // 4), nn.GELU(), nn.Linear(joint // 4, 1), nn.Sigmoid()
            )

            nn.init.trunc_normal_(self.cls_token, std=0.02)

        # -- nhánh 2D -----------------------------------------------------------
        def encode_slices(self, x: Any) -> Any:
            """``[B, P, X, Y, Z]`` → chuỗi lát ``[B, Z, embed_dim]``."""
            batch, phases, size_x, size_y, depth_z = x.shape
            # Gộp batch, lát và thì lại để patch-embed chạy MỘT lượt trên ảnh 1 kênh.
            slices = x.permute(0, 4, 1, 2, 3).reshape(batch * depth_z * phases, 1, size_x, size_y)
            patches = self.patch_embed(slices)  # [B*Z*P, per_phase_dim, h, w]
            n_patch = patches.shape[2] * patches.shape[3]
            # Concat theo TRỤC THÌ: [B*Z, N, P*per_phase_dim] = [B*Z, N, embed_dim]
            patches = patches.reshape(batch * depth_z, phases, -1, n_patch)
            patches = patches.permute(0, 3, 1, 2).reshape(batch * depth_z, n_patch, -1)
            tokens = self.modality_proj(patches)

            cls = self.cls_token.expand(tokens.shape[0], -1, -1)
            tokens = torch.cat([cls, tokens], dim=1)
            if tokens.shape[1] != self.n_token:
                # NỔ thay vì cấp phát lại. Cấp phát lại trong forward chính là lỗi đã sửa;
                # và một model dựng cho 112 in-plane mà nhận 96 thì hình học đã sai rồi.
                raise ValueError(
                    f"nhận {tokens.shape[1]} token/lát nhưng `pos_embed` dựng cho "
                    f"{self.n_token}. Đặt `model.in_plane_size` khớp `data.crop_size[0]` "
                    f"(hiện in_plane_size={in_plane_size}, patch_size={patch_size})."
                )
            tokens = tokens + self.pos_embed

            for block in self.blocks:
                tokens = block(tokens)
            summary = self.norm_2d(tokens[:, 0])  # cls token của từng lát
            return summary.reshape(batch, depth_z, embed_dim)

        # -- nhánh 3D -----------------------------------------------------------
        def encode_volume(self, x: Any) -> tuple[Any, tuple[int, ...]]:
            """``[B, P, X, Y, Z]`` → chuỗi token ``[B, N_v, token_dim]`` + hình dạng map."""
            net = self.resnet
            h = net.act(net.bn1(net.conv1(x)))
            if not net.no_max_pool:
                h = net.maxpool(h)
            h = net.layer4(net.layer3(net.layer2(net.layer1(h))))
            spatial = tuple(h.shape[2:])
            tokens = h.flatten(start_dim=2).transpose(1, 2)  # [B, N_v, C']
            return self.token_proj(tokens), spatial

        # -- toàn mạng ----------------------------------------------------------
        def forward_heads(self, x: Any) -> dict[str, Any]:
            """Trả về đủ ba đầu ra, bất kể chế độ. Dùng cho thang bậc chẩn đoán."""
            if x.ndim != 5:
                raise ValueError(f"cần đầu vào [B, P, X, Y, Z], nhận {tuple(x.shape)}")
            if x.shape[1] != self.num_phases:
                raise ValueError(f"cần {self.num_phases} thì, nhận {x.shape[1]}")

            z2d = self.encode_slices(x)
            z3d, _ = self.encode_volume(x)
            z2d, z3d = self.cgfm(z2d, z3d)

            e2d, w_slice = self.pool_2d(z2d)
            e3d, w_voxel = self.pool_3d(z3d)
            self.last_slice_weights = w_slice.detach()
            self.last_voxel_weights = w_voxel.detach()

            joint = torch.cat([e2d, e3d], dim=1)
            y_2d = self.head_2d(e2d)
            y_3d = self.head_3d(e3d)
            y_fus = self.head_fus(joint)
            beta = self.gate_beta(joint)  # [B, 1]
            self.last_beta = beta.detach()

            # Eq. 11: hiệu chỉnh DƯ, không phải trung bình. Bình quân đơn thuần triệt
            # tiêu một dự đoán đúng và tự tin khi hai nhánh phân kỳ.
            main = y_fus + self.lambda_res * (beta * y_2d + (1.0 - beta) * y_3d)
            return {"main": main, "aux": {"2d": y_2d, "3d": y_3d}}

        def forward(self, x: Any) -> Any:
            out = self.forward_heads(x)
            # Chỉ chế độ train trả dict: nhờ vậy src/eval/* (đều gọi model.eval()) dùng
            # được y nguyên, không phải sửa một dòng nào.
            return out if self.training else out["main"]

    return CGHNet()
