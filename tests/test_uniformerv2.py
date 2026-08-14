"""Test UniFormerV2 và hai config đi kèm.

⚠️ **Máy phát triển không có torch**, nên phần dựng mạng và nạp trọng số ở đây `skip`. Chỗ xác
nhận thật là **cổng A của notebook 24**: nó đối chiếu tập khoá của model với tập khoá của
checkpoint theo **cả hai chiều** trên file thật. Đừng đọc "test xanh" thành "kiến trúc đúng".

Những gì test được ở local đều là **cổng chặn thuần**: bố cục token, tập khoá được phép thiếu,
và hai config khác base ở đúng những khoá nào.
"""

from __future__ import annotations

import inspect

import pytest
import yaml
from src.models.uniformerv2 import (
    DROPPED_PREFIXES,
    PRETRAINED_BASE_URL,
    PRETRAINED_FILENAMES,
    UNIFORMERV2_VARIANTS,
    build_uniformerv2,
    missing_pretrained_keys,
    token_layout,
    variant_spec,
)
from src.utils.io import repo_root

try:
    import torch
except ImportError:  # pragma: no cover
    torch = None

requires_torch = pytest.mark.skipif(torch is None, reason="dựng mạng cần torch")


# --- bố cục token: cổng B của notebook dựa vào đây ------------------------------


def test_bo_cuc_token_o_hinh_hoc_that():
    """112 với patch 16 cho lưới 7×7 — đây là con số phải đọc bằng mắt trước khi train."""
    got = token_layout((14, 112, 112), 16, temporal_downsample=True)
    assert got["grid"] == 7
    assert got["tokens_per_frame"] == 50  # 7*7 + 1 token lớp
    assert got["frames_after_conv1"] == 7
    assert got["tokens_global_block"] == 350


def test_tat_ha_mau_thoi_gian_thi_giu_du_lat():
    got = token_layout((14, 112, 112), 16, temporal_downsample=False)
    assert got["frames_after_conv1"] == 14
    assert got["tokens_global_block"] == 700, "gấp đôi — đây là cái giá của việc giữ đủ lát"


def test_bo_cuc_luc_pretrain_de_doi_chieu():
    """224/16 = 14 ⇒ 196 token không gian. Con số này là mốc để thấy ta mất bao nhiêu."""
    got = token_layout((16, 224, 224), 16, temporal_downsample=True)
    assert got["grid"] == 14
    assert got["tokens_per_frame"] == 197


def test_canh_khong_chia_het_patch_thi_no():
    """100 không chia hết cho 16. ViT phẳng không xử lý phần dư, và nếu để lọt thì `conv1`
    lặng lẽ cắt bớt rìa ảnh — mất đúng phần viền tổn thương.

    ⚠️ Đừng dùng 96 làm ca thử: 96 = 6×16, tức nó CHIA HẾT và test sẽ không bao giờ đỏ.
    """
    with pytest.raises(ValueError, match="không chia hết"):
        token_layout((14, 100, 100), 16, temporal_downsample=True)
    # Và 96 phải đi qua được, để test trên không đỏ vì lý do sai.
    assert token_layout((14, 96, 96), 16, temporal_downsample=True)["grid"] == 6


# --- cổng khoá thiếu -----------------------------------------------------------


def test_ba_tien_to_duoc_phep_thieu_va_khong_hon():
    assert DROPPED_PREFIXES == ("conv1.", "positional_embedding", "transformer.proj.2.")
    duoc_phep = [
        "conv1.weight",
        "positional_embedding",
        "transformer.proj.2.weight",
        "transformer.proj.2.bias",
    ]
    assert missing_pretrained_keys(duoc_phep) == []


def test_khoa_thieu_ngoai_ba_tien_to_bi_bao():
    """Đây là cổng chống chế độ hỏng tệ nhất: `strict=False` im lặng khi kiến trúc lệch."""
    la = missing_pretrained_keys(
        ["conv1.weight", "transformer.dec.0.attn.in_proj_weight", "transformer.balance"]
    )
    assert la == ["transformer.balance", "transformer.dec.0.attn.in_proj_weight"]


def test_proj_0_KHONG_duoc_phep_thieu():
    """`transformer.proj.0` là LayerNorm, shape không phụ thuộc số lớp nên PHẢI nạp được.
    Chỉ `proj.2` (Linear 710→7) mới được bỏ."""
    assert missing_pretrained_keys(["transformer.proj.0.weight"]) == ["transformer.proj.0.weight"]


# --- dò tiền tố bọc của checkpoint ---------------------------------------------


def test_do_duoc_tien_to_backbone():
    """Lớp model của PySlowFast gán mạng vào `self.backbone`, nên checkpoint mang tiền tố đó.

    Không gỡ thì **không khoá nào khớp** và thông báo lỗi lại nói "lệch kiến trúc" — sai hoàn
    toàn. Đã tốn một vòng chạy Kaggle vì đúng chuyện này.
    """
    from src.models.uniformerv2 import detect_key_prefix

    model = {"conv1.weight", "ln_pre.weight", "transformer.balance"}
    ck = {"backbone." + k for k in model} | {"head.weight"}
    assert detect_key_prefix(ck, model) == ("backbone.", 3)


def test_khong_go_tien_to_khi_no_khong_giup():
    """Hoà thì ưu tiên KHÔNG tiền tố — gỡ bừa một đoạn đầu là tự thêm rủi ro."""
    from src.models.uniformerv2 import detect_key_prefix

    model = {"conv1.weight", "ln_pre.weight"}
    assert detect_key_prefix(model, model) == ("", 2)


def test_sai_file_han_thi_so_khop_bang_0():
    """Khác hẳn nhau thì không tiền tố nào cứu được, và chỗ gọi phải nổ với thông báo ĐÚNG."""
    from src.models.uniformerv2 import detect_key_prefix

    _, n = detect_key_prefix({"foo.a", "foo.b"}, {"conv1.weight", "ln_pre.weight"})
    assert n == 0


def test_loader_go_tien_to_truoc_khi_ket_luan_lech_kien_truc():
    """Kiểm ở mức mã nguồn: thứ tự hai bước này là chỗ đã sai một lần."""
    src = (repo_root() / "src" / "models" / "uniformerv2.py").read_text(encoding="utf-8")
    than = src[src.index("def load_clip_k710_weights") :]
    i_go = than.index("detect_key_prefix")
    i_no = than.index("missing_pretrained_keys(missing)")
    assert i_go < i_no, "phải gỡ tiền tố TRƯỚC khi kết luận lệch kiến trúc"


# --- hợp đồng ------------------------------------------------------------------


def test_variant_sai_thi_no_thay_vi_lay_mac_dinh():
    with pytest.raises(ValueError, match="model.variant"):
        variant_spec("b32")


def test_b16_khop_thong_so_ban_goc():
    """Khớp `uniformerv2_b16()`: ViT-B/16, 12 block, và global block hút 4 block CUỐI."""
    spec = variant_spec("b16")
    assert (spec["patch_size"], spec["width"], spec["layers"], spec["heads"]) == (16, 768, 12, 12)
    assert spec["return_list"] == (8, 9, 10, 11)
    assert len(spec["return_list"]) == 4, "n_layers của decoder phải bằng len(return_list)"


def test_moi_variant_deu_co_ten_file_trong_so():
    assert set(PRETRAINED_FILENAMES) == set(UNIFORMERV2_VARIANTS)


def test_trong_so_la_ban_k400_k710_va_do_la_CHO_LECH_bat_buoc():
    """⚠️ Neo lại một chỗ lệch, không phải một lựa chọn.

    MODEL_ZOO chỉ định bản **K710 thuần** làm điểm khởi tạo cho finetune xuôi dòng, và đó là
    bản đáng dùng nhất cho chuyển giao xuyên miền. Nhưng **bucket Aliyun của họ đã chết** —
    mọi URL trả 404 (kiểm 2026-08-14). Bản còn sống là mirror của tác giả trên HuggingFace,
    và nó đã finetune thêm một bước trên K400.

    Test này tồn tại để chỗ lệch đó không lặng lẽ biến mất khỏi tài liệu: nếu ai đó sau này
    tìm được bản K710 thuần thì phải sửa cả test này, tức phải đọc lý do.
    """
    ten = PRETRAINED_FILENAMES["b16"]
    assert ten == "k400+k710_uniformerv2_b16_8x224.pyth"
    assert "k710" in ten, "chuỗi pretrain vẫn đi qua K710"
    assert "k400" in ten, "và nó KHÔNG dừng ở K710 — đây là chỗ lệch"
    assert "huggingface.co" in PRETRAINED_BASE_URL, "Aliyun đã chết, phải là mirror HF"


def test_dung_luong_ghim_khop_file_that():
    """Cell tải dùng con số này để phân biệt checkpoint với một trang lỗi."""
    from src.models.uniformerv2 import PRETRAINED_SIZE_BYTES

    assert PRETRAINED_SIZE_BYTES == 458_289_355
    assert 4e8 < PRETRAINED_SIZE_BYTES < 5e8


def test_mac_dinh_doi_trong_so_pretrained():
    """Cả thí nghiệm tồn tại để đo tác dụng của pretrained — chạy không trọng số phải NỔ."""
    assert inspect.signature(build_uniformerv2).parameters["require_pretrained"].default is True


# --- cần torch -----------------------------------------------------------------


@requires_torch
def test_thoi_kenh_giu_nguyen_tong_theo_kenh():
    """3 kênh RGB → 8 kênh MRI mà **tổng theo kênh không đổi**, nên thang kích hoạt giữ nguyên.

    Nếu chỉ lặp mà không chia thì kích hoạt bị nhân 8/3 và `ln_pre` phải hấp thụ một cú lệch
    thang nó chưa từng thấy lúc pretrain — sai lặng lẽ, không nổ.
    """
    from src.models.uniformerv2 import inflate_input_channels

    w = torch.randn(768, 3, 1, 16, 16)
    ra = inflate_input_channels(w, 8)
    assert ra.shape == (768, 8, 1, 16, 16)
    assert torch.allclose(ra.sum(dim=1), w.sum(dim=1), atol=1e-5)


@requires_torch
def test_thoi_kenh_chap_ca_trong_so_2d():
    from src.models.uniformerv2 import inflate_input_channels

    ra = inflate_input_channels(torch.randn(768, 3, 16, 16), 8)
    assert ra.ndim == 5 and ra.shape[2] == 1


@requires_torch
def test_noi_suy_pos_embed_giu_token_lop():
    """Token lớp phải đi qua NGUYÊN VẸN; chỉ phần không gian được nội suy."""
    from src.models.uniformerv2 import interpolate_position_embedding

    w = torch.randn(197, 768)
    ra = interpolate_position_embedding(w, 7)
    assert ra.shape == (50, 768)
    assert torch.allclose(ra[0], w[0]), "token lớp bị đụng"


@requires_torch
def test_noi_suy_pos_embed_khong_lam_gi_khi_luoi_trung():
    from src.models.uniformerv2 import interpolate_position_embedding

    w = torch.randn(50, 768)
    assert interpolate_position_embedding(w, 7) is w


@requires_torch
def test_forward_ra_dung_so_lop_va_bat_bien_voi_so_lat():
    """Không tham số nào được phụ thuộc số lát — nếu có thì đổi Z sẽ nổ, và ta phải biết."""
    model = build_uniformerv2(input_resolution=112, t_size=14, require_pretrained=False).eval()
    with torch.no_grad():
        assert model(torch.randn(2, 8, 112, 112, 14)).shape == (2, 7)

    # Cùng bộ tham số, đổi số lát: shape tham số không được đổi.
    truoc = {k: tuple(v.shape) for k, v in model.state_dict().items()}
    khac = build_uniformerv2(input_resolution=112, t_size=16, require_pretrained=False)
    assert {k: tuple(v.shape) for k, v in khac.state_dict().items()} == truoc


# --- config --------------------------------------------------------------------


def _phang(d, tien=""):
    out = {}
    for k, v in d.items():
        key = f"{tien}{k}"
        out.update(_phang(v, key + ".")) if isinstance(v, dict) else out.update({key: v})
    return out


def test_config_base_khac_uniformer_s_dung_hai_khoa():
    """Đúng hai khoá: biến thể và thư mục ra. Thừa một khoá là thí nghiệm hai biến."""
    cfg = repo_root() / "configs"
    a = _phang(yaml.safe_load((cfg / "uniformer_s.yaml").read_text("utf-8")))
    b = _phang(yaml.safe_load((cfg / "uniformer_base.yaml").read_text("utf-8")))
    lech = {k for k in set(a) | set(b) if a.get(k, "<vắng>") != b.get(k, "<vắng>")}
    assert lech == {"model.variant", "output_dir"}, f"lệch ngoài dự kiến: {lech}"
    assert b["model.variant"] == "base"


def test_config_v2_dung_dung_ten_model_va_hinh_hoc():
    cfg = yaml.safe_load((repo_root() / "configs" / "uniformerv2_b16.yaml").read_text("utf-8"))
    assert cfg["model"]["name"] == "uniformerv2"
    assert cfg["model"]["variant"] == "b16"
    # `t_size` phải bằng chiều Z của crop; lệch thì reshape trong transformer nổ với thông
    # báo về số phần tử, không gợi ra nguyên nhân.
    assert cfg["model"]["t_size"] == cfg["data"]["crop_size"][2]
    assert cfg["model"]["input_resolution"] == cfg["data"]["crop_size"][0]
    assert cfg["data"]["crop_size"][0] == cfg["data"]["crop_size"][1], "in-plane phải vuông"
    assert cfg["data"]["crop_size"][0] % 16 == 0, "cạnh in-plane phải chia hết cho patch 16"
