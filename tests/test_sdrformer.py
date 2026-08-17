"""Test bản tái lập SDR-Former.

Phần dựng mạng cần torch nên skip ở máy này. Thứ test được mà không cần torch — và cũng là
thứ đáng test hơn — là **các con số trích từ bài** và **số học hình dạng**: một `stage_pool`
sai, một lưới GSA không chia được, hay một `epochs: 300` chép nhầm từ config khác đều cho ra
model chạy trơn và kết quả trông hợp lý, mà lúc đó mốc 0.7910 không còn đối chiếu được nữa.

⚠️ Bất biến quan trọng nhất của kiến trúc này — nhánh CNN luôn có **đúng 2x** số voxel trong
mặt phẳng và **cùng số lát** với nhánh Transformer — được kiểm ở đây bằng số học thuần, vì
nếu nó sai thì BCIM vẫn chạy (interpolate không kén kích thước) và chỉ lặng lẽ ghép sai.
"""

from __future__ import annotations

import pytest
import yaml
from src.models import build_model
from src.models.sdrformer import (
    ATTENTION_SCHEMES,
    DEFAULT_GRID,
    DEFAULT_STAGE_CHANNELS,
    NUM_PHASES,
    PAPER_FLOPS_G,
    PAPER_MR,
    PAPER_PARAMS_M,
    SNN_GAIN_MR,
    STAGE_POOL,
    build_sdrformer,
    stage_shapes,
)
from src.utils.io import repo_root

CONFIG = "sdrformer.yaml"


def _cfg(name: str = CONFIG) -> dict:
    return yaml.safe_load((repo_root() / "configs" / name).read_text("utf-8"))


# --- con số trích từ bài, neo lại để không trôi ---------------------------------


def test_moc_mr_dung_bang_1():
    """Hàng SDR-Former, phần "MR (8-phase)" của Bảng 1 — mốc đối chiếu của cả phép tái lập."""
    assert PAPER_MR == {"acc": 0.7885, "auc": 0.9536, "f1": 0.7910, "kappa": 0.7467}


def test_so_tham_so_va_flops_cong_bo():
    """Bảng 4, cột 8 pha."""
    assert PAPER_PARAMS_M == 19.34
    assert PAPER_FLOPS_G == 40.26


def test_bang_snn_du_sau_backbone_va_toan_bo_deu_duong():
    """Đây là bằng chứng MỘT BIẾN cho trục fusion — thứ biện minh cho cả cấu hình này.

    Nếu một hàng bị chép sai thành âm thì lý do chạy thí nghiệm biến mất mà không ai thấy.
    """
    assert len(SNN_GAIN_MR) == 6
    for ten, (image_level, siamese) in SNN_GAIN_MR.items():
        assert siamese > image_level, f"{ten}: Siamese phải cao hơn image-level"

    hieu = [siamese - plain for plain, siamese in SNN_GAIN_MR.values()]
    assert min(hieu) == pytest.approx(0.0223, abs=1e-4)  # DenseNet-121, nhỏ nhất
    assert max(hieu) == pytest.approx(0.0516, abs=1e-4)  # UniFormer-S, lớn nhất
    assert sum(hieu) / len(hieu) == pytest.approx(0.036, abs=5e-4)


def test_transformer_huong_loi_tu_snn_nhieu_hon_cnn():
    """Khẳng định §5.1 của bài: "Transformer-based models demonstrate more substantial
    performance enhancements in the multi-phase context". Nó là cơ sở để kỳ vọng hướng này
    hợp với một backbone lai, chứ không phải với một CNN thuần."""
    cnn = ["resnet50", "densenet121", "mcscnn"]
    tfm = ["botnet50", "uniformer_s", "h2former"]
    d_cnn = [SNN_GAIN_MR[k][1] - SNN_GAIN_MR[k][0] for k in cnn]
    d_tfm = [SNN_GAIN_MR[k][1] - SNN_GAIN_MR[k][0] for k in tfm]
    assert min(d_tfm) > max(d_cnn), "mọi transformer phải hưởng lợi hơn mọi CNN"


def test_uniformer_s_cua_ho_thap_hon_ban_pretrained_cua_ta():
    """Mốc quan trọng nhất để không đọc sai kết quả: bản SNN-UniFormer-S from-scratch của họ
    (0.7639) vẫn THẤP HƠN 0.7682 mà ta đã đo trên test-104 với UniFormer-S + Kinetics.

    Tức trục fusion một mình không đủ bù cho pretrained; chỉ SDR-Former đủ bộ (0.7910) mới
    vượt lên. Ai đọc bảng mà bỏ qua điều này sẽ kỳ vọng sai."""
    assert SNN_GAIN_MR["uniformer_s"][1] < 0.7682
    assert PAPER_MR["f1"] > 0.7682


# --- cổng tham số, không cần torch ---------------------------------------------


def test_attention_chi_co_gsa():
    """Bảng 5 so bốn cơ chế và chốt GSA. Ba cái kia phải NỔ, không được lặng lẽ rơi về mặc
    định — nếu không, một config viết `swin` sẽ chạy ra số của GSA và bị đọc thành số Swin."""
    assert ATTENTION_SCHEMES == ("gsa",)
    for ten in ("swin", "sra", "psa"):
        with pytest.raises(ValueError, match="attention phải thuộc"):
            build_sdrformer(attention=ten)


def test_kenh_phai_chia_het_cho_so_head():
    with pytest.raises(ValueError, match="chia hết cho num_heads"):
        build_sdrformer(stage_channels=(30, 64, 128), num_heads=4)


def test_so_stage_phai_dung_ba():
    with pytest.raises(ValueError, match="đúng 3 phần tử"):
        build_sdrformer(stage_channels=(32, 64))


def test_tham_so_am_bi_tu_choi():
    with pytest.raises(ValueError, match="blocks_per_stage"):
        build_sdrformer(blocks_per_stage=0)
    with pytest.raises(ValueError, match="bcim_hidden_mult"):
        build_sdrformer(bcim_hidden_mult=0)
    with pytest.raises(ValueError, match="grid_size"):
        build_sdrformer(grid_size=(2, 7))


# --- số học hình dạng: bất biến mà BCIM phụ thuộc vào --------------------------


def test_hinh_dang_khop_hinh_2_cua_bai():
    """Hình 2 vẽ ở 16 lát (trước khi cắt); ta cắt còn 14 nên 16->14 và 8->7. Trong mặt phẳng
    thì khớp từng con số."""
    rows = stage_shapes((14, 112, 112))
    ten = [r[0] for r in rows]
    assert ten == ["stem", "stage1", "stage2", "stage3"]

    kenh = [r[1] for r in rows]
    assert kenh == [16, 32, 64, 128]

    cnn = [r[2] for r in rows]
    trans = [r[3] for r in rows]
    assert cnn == [(14, 56, 56), (14, 28, 28), (7, 14, 14), (7, 14, 14)]
    assert trans == [(14, 28, 28), (14, 14, 14), (7, 7, 7), (7, 7, 7)]


def test_bat_bien_bcim_nhanh_cao_gap_doi_trong_mat_phang_cung_so_lat():
    """⚠️ Bất biến QUAN TRỌNG NHẤT của file này.

    Bài định nghĩa `F_v` là `C x D x H/2 x W/2` — cùng D, nửa mặt phẳng. Nếu sai, BCIM vẫn
    chạy (F.interpolate nhận mọi kích thước) và chỉ lặng lẽ ghép hai feature map lệch nhau.
    Không có gì nổ, không có gì cảnh báo, chỉ có điểm số thấp hơn đáng lẽ.
    """
    for size in [(14, 112, 112), (16, 128, 128), (8, 64, 64)]:
        for ten, _ch, cnn, trans in stage_shapes(size):
            assert cnn[0] == trans[0], f"{size} {ten}: số lát lệch {cnn[0]} vs {trans[0]}"
            assert cnn[1] == 2 * trans[1], f"{size} {ten}: trục H không gấp đôi"
            assert cnn[2] == 2 * trans[2], f"{size} {ten}: trục W không gấp đôi"


def test_canh_le_bi_tu_choi():
    """Nhánh thấp lấy nửa mặt phẳng nên cạnh lẻ làm hai nhánh lệch ngay từ đầu."""
    with pytest.raises(ValueError, match="phải chẵn"):
        stage_shapes((14, 111, 112))


def test_pool_dung_hinh_2():
    """MaxPool 1x2x2 sau stage 1, 2x2x2 sau stage 2, không pool sau stage 3."""
    assert STAGE_POOL == ((1, 2, 2), (2, 2, 2), None)


def test_luoi_gsa_chia_het_moi_stage_cua_nhanh_transformer():
    """Lưới không chia hết vẫn chạy (có đệm), nhưng đệm nghĩa là một phần token là rác.

    ⚠️ Block attention của stage N chạy **trước** pool của stage N, nên đầu vào của nó là
    hình dạng ở hàng **trước đó** (`stem` cho stage 1). Đọc nhầm sang hàng cùng tên là kiểm
    một tensor không tồn tại — chính lỗi bản đầu của test này mắc phải.
    """
    gd, gh, gw = DEFAULT_GRID
    rows = stage_shapes((14, 112, 112))
    vao_attention = [(rows[i + 1][0], rows[i][3]) for i in range(len(rows) - 1)]
    assert [t for t, _ in vao_attention] == ["stage1", "stage2", "stage3"]
    assert [s for _, s in vao_attention] == [(14, 28, 28), (14, 14, 14), (7, 7, 7)]

    can_dem = []
    for ten, (d, h, w) in vao_attention:
        assert h % gh == 0, f"{ten}: H={h} không chia hết cho {gh}"
        assert w % gw == 0, f"{ten}: W={w} không chia hết cho {gw}"
        if d % gd:
            can_dem.append(ten)
    assert can_dem == ["stage3"], f"chỉ stage3 được phép cần đệm, nhận {can_dem}"


def test_moi_nhom_attention_co_98_token():
    """2*7*7 = 98 token mỗi nhóm ở MỌI stage — đây là lý do cấu hình này rẻ, và là con số
    cổng B in ra để đối chiếu."""
    gd, gh, gw = DEFAULT_GRID
    assert gd * gh * gw == 98


# --- config khớp bài -----------------------------------------------------------


def test_config_dung_cache_cghnet_khong_build_cache_moi():
    """§4.2 của bài: resize 16x128x128 rồi cắt 14x112x112 — khớp CHÍNH XÁC cache CGHNet."""
    cfg = _cfg()
    pre = _cfg("preprocess_cghnet.yaml")
    assert cfg["data"]["crop_size"] == pre["target_size"] == [112, 112, 14]
    assert [
        s + 2 * m for s, m in zip(pre["target_size"], pre["crop_margin_voxels"], strict=True)
    ] == [128, 128, 16]


def test_config_200_epoch_khong_phai_300():
    """§4.2: "spans over 200 epochs, with the first 5 epochs designated as a warm-up phase".
    Mọi config khác của dự án là 300 — chỗ này rất dễ bị "thống nhất" nhầm."""
    cfg = _cfg()
    assert cfg["train"]["epochs"] == 200
    assert cfg["train"]["warmup_epochs"] == 5


def test_config_dung_cross_entropy_tran_khong_focal():
    """§4.2: "The standard cross-entropy loss function is employed". Không focal, không trọng
    số lớp, không label smoothing — dù đây vẫn là bài toán 7 lớp mất cân bằng."""
    cfg = _cfg()
    assert cfg["loss"]["name"] == "cross_entropy"
    assert cfg["loss"]["class_weights"] == "none"
    assert cfg["loss"]["label_smoothing"] == 0.0
    assert cfg["data"]["sampling"] == "instance"


def test_config_batch_8_va_wd_005():
    """§4.2: batch size 8, AdamW lr 1e-4, weight decay 0.05."""
    cfg = _cfg()
    assert cfg["data"]["batch_size"] == 8
    assert cfg["train"]["accum_steps"] == 1
    assert float(cfg["train"]["lr"]) == 1e-4
    assert float(cfg["train"]["weight_decay"]) == 0.05


def test_config_giu_ban_literal_cua_hinh_2():
    """Bản literal (~12.7M) chứ không phải bản chỉnh để khớp 19.34M. Đổi hai khoá này là đổi
    kiến trúc, và phải ghi vào báo cáo — nên chúng bị neo ở đây."""
    cfg = _cfg()["model"]
    assert cfg["blocks_per_stage"] == 1
    assert cfg["bcim_hidden_mult"] == 1
    assert cfg["stem_channels"] == 16
    assert tuple(cfg["stage_channels"]) == DEFAULT_STAGE_CHANNELS


def test_config_bat_ca_hai_module_loi():
    """Bảng 3 là ablation; cấu hình chạy thật phải là hàng "SDR-Former" đủ bộ."""
    cfg = _cfg()["model"]
    assert cfg["use_bcim"] is True
    assert cfg["use_apsm"] is True


def test_config_khong_bat_augment_cua_recipe_khac():
    """Ba augment lọc không gian thuộc recipe đội hạng 2, KHÔNG có trong bài này. Bật chúng
    là trộn hai recipe và mốc 0.7910 mất nghĩa."""
    aug = _cfg()["data"]["augment"]
    assert aug["edge_prob"] == 0
    assert aug["emboss_prob"] == 0
    assert aug["filter_prob"] == 0
    assert aug["intensity_prob"] == 0
    assert _cfg()["data"]["mixup_alpha"] == 0.0


def test_config_giu_dropout_cho_mc_dropout():
    """`uniformer_s` để head_dropout 0.0 nên MC-dropout vô nghĩa ở đó. Cấu hình này lấy lại
    được đại lượng bất định epistemic — đóng góp headline của dự án."""
    assert _cfg()["model"]["dropout_prob"] > 0


def test_config_so_pha_khop_taxonomy():
    cfg = _cfg()["model"]
    assert cfg["num_phases"] == NUM_PHASES == 8
    assert cfg["num_classes"] == 7


# --- dựng mạng thật (cần torch) ------------------------------------------------


def test_dung_duoc_qua_registry_va_ra_dung_shape():
    torch = pytest.importorskip("torch", reason="dựng mạng cần torch")

    cfg = _cfg()["model"]
    model = build_model(cfg).eval()
    x = torch.zeros(2, 8, 112, 112, 14)
    with torch.no_grad():
        out = model(x)
    assert tuple(out.shape) == (2, 7)


def test_encoder_dung_chung_trong_so_cho_ca_8_pha():
    """Đây là điều làm hướng này khả thi: 8 pha nhưng chỉ MỘT bộ tham số encoder. Nếu ai đó
    đổi sang 8 encoder riêng thì số tham số nhảy vọt và 312 ca train chắc chắn overfit."""
    pytest.importorskip("torch", reason="dựng mạng cần torch")

    m2 = build_sdrformer(num_phases=2)
    m8 = build_sdrformer(num_phases=8)
    enc2 = sum(p.numel() for p in m2.encoder.parameters())
    enc8 = sum(p.numel() for p in m8.encoder.parameters())
    assert enc2 == enc8, "encoder phải dùng chung, số tham số không được phụ thuộc số pha"


def test_apsm_sinh_trong_so_tren_truc_pha_va_tong_bang_1():
    """Eq. (2): softmax chạy trên trục PHA, riêng từng kênh. Nếu ai đó softmax nhầm trục kênh
    thì mạng vẫn chạy và vẫn hội tụ, chỉ là APSM không còn chọn pha nữa."""
    torch = pytest.importorskip("torch", reason="dựng mạng cần torch")

    model = build_sdrformer(num_phases=8).eval()
    with torch.no_grad():
        model(torch.randn(2, 8, 112, 112, 14))

    w = model.apsm_c.last_weights  # [B, P, C]
    assert tuple(w.shape[:2]) == (2, 8)
    tong = w.sum(dim=1)
    assert torch.allclose(tong, torch.ones_like(tong), atol=1e-4), (
        "tổng trọng số trên trục pha phải bằng 1 cho từng kênh — softmax đang chạy sai trục"
    )
    assert tuple(model.last_phase_weights.shape) == (2, 8)


def test_dau_vao_sai_so_pha_thi_no():
    torch = pytest.importorskip("torch", reason="dựng mạng cần torch")

    model = build_sdrformer(num_phases=8).eval()
    with pytest.raises(ValueError, match="cần 8 pha"):
        model(torch.zeros(1, 4, 112, 112, 14))
    with pytest.raises(ValueError, match=r"\[B, P, X, Y, Z\]"):
        model(torch.zeros(1, 8, 112, 112))


def test_tat_module_van_dung_duoc_cho_ablation_bang_3():
    torch = pytest.importorskip("torch", reason="dựng mạng cần torch")

    for bcim, apsm in [(False, True), (True, False), (False, False)]:
        model = build_sdrformer(use_bcim=bcim, use_apsm=apsm).eval()
        with torch.no_grad():
            out = model(torch.zeros(1, 8, 112, 112, 14))
        assert tuple(out.shape) == (1, 7)
