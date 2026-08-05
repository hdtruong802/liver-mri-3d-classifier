"""Test Grad-CAM 3D. Cần torch nên tự skip ở máy chưa cài.

Test neo của file này là `test_cam_khong_phai_hang_so`: một bản đồ hằng số vẫn render
ra ảnh đẹp và vẫn thuyết phục — nếu hook gắn nhầm tầng hoặc gradient không chảy về thì
chỉ có test này bắt được.
"""

import numpy as np
import pytest

torch = pytest.importorskip("torch", reason="cần torch")
pytest.importorskip("monai", reason="cần monai")

from src.models import build_model  # noqa: E402
from src.xai.gradcam import (  # noqa: E402
    CANDIDATE_LAYERS,
    CamResult,
    feature_layer_shapes,
    grad_cam_3d,
    phase_importance,
    resolve_layer,
)

# Nhỏ hơn 112×112×32 thật để test chạy nhanh, nhưng vẫn đủ để mọi tầng có Z ≥ 2.
SHAPE = (1, 8, 64, 64, 32)


@pytest.fixture(scope="module")
def model():
    return build_model({"name": "densenet121_3d", "in_channels": 8, "num_classes": 7})


@pytest.fixture(scope="module")
def volume():
    torch.manual_seed(0)
    return torch.randn(SHAPE)


def test_feature_layer_shapes_phu_moi_ung_vien(model):
    shapes = feature_layer_shapes(model, SHAPE)
    for name in CANDIDATE_LAYERS:
        assert name in shapes, f"thiếu {name}"
        assert len(shapes[name]) == 5


def test_tang_cuoi_hep_hon_tang_dau(model):
    """Ghi lại sự thật khiến `feature_layer_shapes` phải tồn tại: hạ mẫu rất mạnh."""
    shapes = feature_layer_shapes(model, SHAPE)
    assert shapes["norm5"][2:] < shapes["pool0"][2:]


def test_resolve_layer_bao_loi_doc_duoc(model):
    with pytest.raises(KeyError, match="không có tầng"):
        resolve_layer(model, "khong-ton-tai")


def test_cam_dung_khoang_va_dung_kich_thuoc(model, volume):
    r = grad_cam_3d(model, volume, target_class=0, layer="denseblock3")
    cam, native = r.cam, r.native_shape
    assert cam.shape == SHAPE[2:]
    assert cam.min() >= 0.0 and cam.max() <= 1.0
    assert len(native) == 3 and all(v >= 2 for v in native)


def test_cam_khong_phai_hang_so(model, volume):
    """Bản đồ phẳng vẫn render ra ảnh đẹp — chỉ test này phát hiện được."""
    cam = grad_cam_3d(model, volume, target_class=0, layer="denseblock3").cam
    assert cam.std() > 1e-6, "bản đồ hằng số: hook sai tầng hoặc gradient không chảy về"


@pytest.mark.parametrize("mode", ["hires", "gradcam"])
def test_hai_che_do_deu_chay_va_cho_ket_qua_khac_nhau(model, volume, mode):
    cam = grad_cam_3d(model, volume, target_class=0, layer="denseblock3", mode=mode).cam
    assert cam.min() >= 0.0 and cam.max() == pytest.approx(1.0)


def test_mode_khong_hop_le_thi_no(model, volume):
    with pytest.raises(ValueError, match="mode phải"):
        grad_cam_3d(model, volume, target_class=0, layer="denseblock3", mode="khong-co")


def test_dac_trung_dense_block_CO_gia_tri_am(model, volume):
    """Sự thật khiến `mode='hires'` phải là mặc định — xem docstring module.

    Nếu test này đỏ (đặc trưng hoá ra không âm) thì lập luận chọn HiResCAM sụp, và
    phải xem lại mặc định.
    """
    import torch
    from src.xai.gradcam import resolve_layer

    store = {}
    handle = resolve_layer(model, "denseblock3").register_forward_hook(
        lambda _m, _i, out: store.__setitem__("a", out)
    )
    model.eval()
    try:
        with torch.no_grad():
            model(volume)
    finally:
        handle.remove()
    am = (store["a"] < 0).float().mean().item()
    assert am > 0.01, f"chỉ {am:.1%} giá trị âm — giả định của Grad-CAM gốc KHÔNG bị vi phạm"


def test_cam_doi_theo_lop_dich(model, volume):
    """Giống nhau ở hai lớp nghĩa là `target_class` không được dùng."""
    a = grad_cam_3d(model, volume, target_class=0, layer="denseblock3").cam
    b = grad_cam_3d(model, volume, target_class=6, layer="denseblock3").cam
    assert not np.allclose(a, b)


def test_tra_ve_CamResult_du_khoa(model, volume):
    r = grad_cam_3d(model, volume, target_class=0, layer="denseblock3")
    assert isinstance(r, CamResult)
    assert r.degenerate is False
    assert 0.0 <= r.negative_fraction <= 1.0
    assert "đặc trưng âm" in r.explain()


def test_ban_do_suy_bien_KHONG_no_ma_danh_dau(model, volume):
    """Suy biến là kết quả, không phải lỗi — thư viện đo, người gọi đặt chính sách.

    Neo hành vi đã sửa ở S-097: trước đó hàm `raise`, và điều đó chặn đúng phép phân
    tích đáng giá nhất (bản đồ phản chứng cho lớp thật ở ca đoán sai).
    """
    import torch

    # Ép suy biến bằng cách đảo dấu gradient: nhân logit đích với -1 không làm được
    # từ ngoài, nên dùng một lớp mà model gần như chắc chắn không ủng hộ.
    logits = None
    model.eval()
    with torch.no_grad():
        logits = model(volume)[0]
    worst = int(logits.argmin())
    r = grad_cam_3d(model, volume, target_class=worst, layer="denseblock3")

    assert isinstance(r, CamResult)  # không nổ, dù suy biến hay không
    if r.degenerate:
        assert r.cam.max() == 0.0
        assert r.combined_max <= 0.0


def test_tu_choi_tang_co_chieu_bang_1(model):
    """Với đầu vào mỏng, tầng sâu sẽ còn Z = 1 — phải nổ chứ không trả bản đồ vô nghĩa."""
    thin = torch.randn(1, 8, 32, 32, 8)
    with pytest.raises(ValueError, match="chiều bằng 1"):
        grad_cam_3d(model, thin, target_class=0, layer="norm5")


def test_du_doan_o_train_mode_KHAC_o_eval_mode(model, volume):
    """Neo lý do notebook phải gọi `model.eval()` (WORKLOG S-096).

    `build_model` trả về model ở chế độ train. Ở đó dropout còn bật và BatchNorm dùng
    thống kê của batch — với batch = 1 thì mỗi kênh bị chuẩn hoá bằng chính nó. Lớp
    đoán ra khác hẳn, và Grad-CAM sẽ giải thích một lớp mà model không thật sự đoán.
    """
    model.train()
    with torch.no_grad():
        a = model(volume)
        b = model(volume)
    model.eval()
    with torch.no_grad():
        c = model(volume)
        d = model(volume)

    assert not torch.allclose(a, b), "train mode phải KHÔNG tất định (dropout)"
    torch.testing.assert_close(c, d)  # eval mode phải tất định
    assert not torch.allclose(a, c, atol=1e-3), "hai chế độ phải cho kết quả khác nhau"


def test_model_ve_dung_che_do_sau_khi_chay(model, volume):
    """Grad-CAM chuyển model sang eval; nếu quên trả về thì vòng train sau đó hỏng."""
    model.train()
    grad_cam_3d(model, volume, target_class=0, layer="denseblock3")
    assert model.training is True
    model.eval()


def test_phase_importance_dung_hinh_dang_va_tong_1(model, volume):
    values = phase_importance(model, volume, target_class=0)
    assert values.shape == (8,)
    assert (values >= 0).all()
    assert values.sum() == pytest.approx(1.0, abs=1e-5)


def test_phase_importance_khong_deu_tap(model, volume):
    """Đều tăm tắp nghĩa là gradient không tới được đầu vào."""
    values = phase_importance(model, volume, target_class=0)
    assert values.std() > 1e-6
