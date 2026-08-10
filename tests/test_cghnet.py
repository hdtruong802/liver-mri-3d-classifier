"""Test bản tái lập CGHNet.

Phần dựng mạng cần torch + monai nên skip ở máy này. Thứ test được mà không cần chúng —
và cũng là thứ đáng test hơn — là **các cổng và các con số trích từ bài**: một `λ_res` sai,
một `rotate_prob` để 1.0 thay vì 0.5, hay một deep supervision chỉ cộng hai số hạng đều cho
ra model chạy được và kết quả trông hợp lý. Khi đó con số 0.818 không còn là mốc đối chiếu
được nữa, mà ta lại không biết.
"""

from __future__ import annotations

import inspect

import pytest
import yaml
from src.models import DEEP_SUPERVISION_MODELS, build_model
from src.models.cghnet import (
    DEFAULT_LAMBDA_RES,
    PAPER_F1,
    PAPER_PARAMS_M,
    build_cghnet,
    resnet3d_feature_dim,
)
from src.train.losses import deep_supervision
from src.utils.io import repo_root


def _cfg(name: str) -> dict:
    return yaml.safe_load((repo_root() / "configs" / name).read_text("utf-8"))


# --- con số trích từ bài, neo lại để không trôi ---------------------------------


def test_lambda_res_la_0_50():
    """Bảng 6 quét 0.1-0.9 và chốt 0.50; 0.10 cho 77.9 và 0.90 cho 79.3."""
    assert DEFAULT_LAMBDA_RES == 0.50
    assert _cfg("cghnet.yaml")["model"]["lambda_res"] == 0.50


def test_moc_f1_cong_bo_dung_bang_2():
    """Thang bậc chẩn đoán của cả phép tái lập nằm ở ba con số này."""
    assert PAPER_F1 == {"3d": 0.724, "2d": 0.742, "main": 0.818}


def test_so_tham_so_cong_bo():
    assert PAPER_PARAMS_M == 59.37


def test_resnet50_cho_2048_kenh():
    """Nhánh 3D suy là ResNet-50-3D vì hàng ResNet3D của họ là 46.22M."""
    assert resnet3d_feature_dim(50) == 2048
    assert resnet3d_feature_dim(18) == 512
    with pytest.raises(ValueError, match="chưa biết số kênh"):
        resnet3d_feature_dim(200)


# --- cổng tham số, không cần torch ---------------------------------------------


def test_embed_dim_phai_chia_het_cho_so_pha():
    """Patch-embed dùng chung sinh embed_dim/num_phases chiều mỗi thì rồi concat theo
    trục thì (bài §3.2), nên phép concat phải ra đúng embed_dim."""
    with pytest.raises(ValueError, match="chia hết cho num_phases"):
        build_cghnet(embed_dim=100, num_phases=8)


def test_embed_dim_phai_chia_het_cho_so_head():
    with pytest.raises(ValueError, match="chia hết cho num_heads"):
        build_cghnet(embed_dim=384, num_heads=7)


def test_do_sau_resnet_khong_biet_thi_no():
    with pytest.raises(ValueError, match="chưa biết số kênh"):
        build_cghnet(resnet_depth=200)


# --- deep supervision ----------------------------------------------------------


def test_deep_supervision_cong_du_ba_so_hang():
    """Eq. 12: L = FL(y) + FL(y_2D) + FL(y_3D). Thiếu một số hạng thì đầu đó không nhận
    gradient, và ta mất luôn thang bậc chẩn đoán mà không có gì báo."""
    goi = []

    def base(logits, targets):  # noqa: ANN001, ANN202
        goi.append(logits)
        return float(logits)

    wrapped = deep_supervision(base)
    total = wrapped({"main": 1.0, "aux": {"2d": 10.0, "3d": 100.0}}, None)
    assert total == pytest.approx(111.0)
    assert goi == [1.0, 10.0, 100.0]


def test_deep_supervision_van_nhan_tensor_thuong():
    """Cùng một criterion phải dùng được cho model một đầu ra, để `run_epoch` không phải
    biết mình đang train kiến trúc nào."""
    wrapped = deep_supervision(lambda logits, targets: float(logits) * 2)
    assert wrapped(3.0, None) == pytest.approx(6.0)


def test_aux_weight_ap_dung_dung_cho():
    wrapped = deep_supervision(lambda logits, targets: float(logits), aux_weight=0.5)
    assert wrapped({"main": 1.0, "aux": {"a": 10.0}}, None) == pytest.approx(6.0)


def test_build_criterion_bat_deep_supervision_tu_config():
    torch = pytest.importorskip("torch", reason="build_criterion cần torch")
    from src.train.losses import build_criterion

    cfg = _cfg("cghnet.yaml")
    assert cfg["loss"]["deep_supervision"] is True
    criterion = build_criterion(cfg, [0, 1, 2, 3, 4, 5, 6], device=torch.device("cpu"))
    logits = torch.zeros(2, 7)
    labels = torch.zeros(2, dtype=torch.long)
    mot_dau = criterion(logits, labels)
    ba_dau = criterion({"main": logits, "aux": {"2d": logits, "3d": logits}}, labels)
    assert float(ba_dau) == pytest.approx(3 * float(mot_dau), rel=1e-5)


# --- config -------------------------------------------------------------------


def test_config_khop_dac_ta_cua_bai():
    """Mọi khoá có nhãn [BÀI] trong config phải khớp §4.3 và Bảng 4/6."""
    cfg = _cfg("cghnet.yaml")
    assert cfg["train"]["epochs"] == 300
    assert cfg["train"]["lr"] == 0.0001
    assert cfg["train"]["weight_decay"] == 0.00001, "bài ghi 1e-5, không phải 0.05"
    assert cfg["train"]["warmup_epochs"] == 5
    assert cfg["data"]["batch_size"] * cfg["train"]["accum_steps"] == 4, "bài: batch size 4"
    assert cfg["loss"]["name"] == "focal", "Bảng 4: focal 81.8 so với CE 79.9"
    assert cfg["loss"]["aux_weight"] == 1.0, "Eq. 12 cộng không trọng số"


def test_config_augment_khop_bai():
    """Bài: "each with a probability of 0.5" — áp cho CẢ xoay, không chỉ lật."""
    aug = _cfg("cghnet.yaml")["data"]["augment"]
    assert aug["flip_prob"] == 0.5
    assert aug["rotate_prob"] == 0.5, "bài nói 0.5; mặc định của transform là 1.0"
    assert sorted(aug["flip_axes"]) == ["x", "y", "z"]
    assert not any(aug["translate_voxels"]), "cắt ngẫu nhiên rồi, tịnh tiến nữa là đệm 0 trở lại"


def test_config_bat_buoc_rotate_mode_nearest():
    """Lề cache chỉ 8 voxel trong mặt phẳng mà xoay 10 độ hỏng góc tới ~12 voxel (đo ở
    E12). `constant` sẽ để lọt voxel bị lấp 0 vào khối cắt ngẫu nhiên."""
    assert _cfg("cghnet.yaml")["data"]["augment"]["rotate_mode"] == "nearest"


def test_hinh_hoc_cache_khop_bai():
    """Bài: resize về 16x128x128 rồi random crop 14x112x112 (thứ tự D x H x W)."""
    pre = _cfg("preprocess_cghnet.yaml")
    inner = pre["target_size"]
    margin = pre["crop_margin_voxels"]
    assert inner == [112, 112, 14]
    assert margin == [8, 8, 1]
    grid = [s + 2 * m for s, m in zip(inner, margin, strict=True)]
    assert grid == [128, 128, 16], f"lưới cache {grid}, bài dùng 128x128x16"
    assert _cfg("cghnet.yaml")["data"]["crop_size"] == inner, "hai config phải khớp"


def test_cache_cghnet_phan_biet_duoc_voi_e4_va_e12():
    """Ba cache đều per_phase + lesion_tight; chỉ target_size và lề phân biệt được chúng.
    Cho nhầm cache thì model nhận hình học khác mà KHÔNG có gì báo lỗi."""
    cghnet = _cfg("preprocess_cghnet.yaml")
    e12 = _cfg("preprocess_e12.yaml")
    e4 = _cfg("preprocess_e4.yaml")
    dau_van_tay = lambda c: (  # noqa: E731
        tuple(c["target_size"]),
        tuple(c.get("crop_margin_voxels") or (0, 0, 0)),
    )
    assert len({dau_van_tay(cghnet), dau_van_tay(e12), dau_van_tay(e4)}) == 3
    assert cghnet["cache_dir"] != e12["cache_dir"] != e4["cache_dir"]


def test_registry_biet_cghnet_co_deep_supervision():
    assert "cghnet" in DEEP_SUPERVISION_MODELS
    nhan = set(inspect.signature(build_cghnet).parameters)
    assert set(_cfg("cghnet.yaml")["model"]) - {"name"} <= nhan


# --- dựng thật, chỉ chạy nơi có torch + monai (Kaggle) -------------------------


def test_dung_that_ba_dau_ra_va_hinh_hoc():
    """Phép kiểm cuối: cho một batch đúng hình học của bài đi qua toàn mạng."""
    torch = pytest.importorskip("torch", reason="dựng mạng cần torch")
    pytest.importorskip("monai", reason="ResNet-3D lấy từ MONAI")

    model = build_model(_cfg("cghnet.yaml")["model"])
    x = torch.zeros(2, 8, 112, 112, 14)

    model.train()
    out = model(x)
    assert isinstance(out, dict), "chế độ train phải trả dict cho deep supervision"
    assert set(out) == {"main", "aux"}
    assert set(out["aux"]) == {"2d", "3d"}
    for logits in (out["main"], out["aux"]["2d"], out["aux"]["3d"]):
        assert tuple(logits.shape) == (2, 7)

    model.eval()
    with torch.no_grad():
        tensor_out = model(x)
    assert torch.is_tensor(tensor_out), (
        "chế độ eval phải trả TENSOR — cả src/eval/* dựa vào điều này để không phải sửa"
    )
    assert tuple(tensor_out.shape) == (2, 7)


def test_forward_heads_luon_tra_dict():
    """Cần cho cell thang bậc: đọc ba đầu ra từ checkpoint mà không phải bật train mode
    (bật train mode sẽ kéo BatchNorm sang thống kê của batch hiện tại)."""
    torch = pytest.importorskip("torch", reason="dựng mạng cần torch")
    pytest.importorskip("monai", reason="ResNet-3D lấy từ MONAI")

    model = build_model(_cfg("cghnet.yaml")["model"]).eval()
    with torch.no_grad():
        out = model.forward_heads(torch.zeros(1, 8, 112, 112, 14))
    assert set(out) == {"main", "aux"}


def test_attention_pool_dung_chuan_L2_khong_phai_scalar():
    """Bài Eq. 2: điểm của mỗi token là ||P||_2 của vector logit K chiều, không phải một
    scalar học trực tiếp. Thay bằng Linear(dim, 1) là một module khác."""
    torch = pytest.importorskip("torch", reason="dựng mạng cần torch")
    pytest.importorskip("monai", reason="ResNet-3D lấy từ MONAI")

    model = build_model(_cfg("cghnet.yaml")["model"]).eval()
    assert model.pool_2d.score.out_features == 7, "K phải là num_classes"
    with torch.no_grad():
        model.forward_heads(torch.zeros(2, 8, 112, 112, 14))
    w = model.last_slice_weights
    assert tuple(w.shape) == (2, 14), "trọng số phải có một số cho mỗi LÁT"
    torch.testing.assert_close(w.sum(dim=1), torch.ones(2))


def test_beta_trong_khoang_0_1():
    """Eq. 10: beta = sigma(MLP(...)), là cổng tin cậy giữa hai nhánh."""
    torch = pytest.importorskip("torch", reason="dựng mạng cần torch")
    pytest.importorskip("monai", reason="ResNet-3D lấy từ MONAI")

    model = build_model(_cfg("cghnet.yaml")["model"]).eval()
    with torch.no_grad():
        model.forward_heads(torch.zeros(3, 8, 112, 112, 14))
    beta = model.last_beta
    assert tuple(beta.shape) == (3, 1)
    assert bool((beta >= 0).all() and (beta <= 1).all())


def test_z_co_ve_1_o_layer4_la_tat_yeu():
    """Với z=14 và 16 lần hạ mẫu thì layer4 còn z=1. Ghi lại thành test để lần sau không
    ai tưởng đó là lỗi và đi 'sửa'."""
    torch = pytest.importorskip("torch", reason="dựng mạng cần torch")
    pytest.importorskip("monai", reason="ResNet-3D lấy từ MONAI")

    model = build_model(_cfg("cghnet.yaml")["model"]).eval()
    with torch.no_grad():
        _tokens, spatial = model.encode_volume(torch.zeros(1, 8, 112, 112, 14))
    assert spatial == (7, 7, 1), f"vết không gian {spatial}, mong đợi (7, 7, 1)"
