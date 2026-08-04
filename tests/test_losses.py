"""Test hàm mất mát.

Phần trọng số lớp là numpy thuần nên không cần torch. Phần focal cần torch và tự skip.

Test neo của file này là `test_focal_gamma_0_bang_cross_entropy`: nếu focal viết sai
thì nó vẫn "chạy được" và cho ra một model tệ hơn mà không ai biết vì sao. Ràng nó
vào một hàm đã được kiểm chứng là cách duy nhất bắt được chuyện đó.
"""

import numpy as np
import pytest
from src.train.losses import build_criterion, effective_number_weights

try:
    import torch
except ImportError:  # pragma: no cover - phụ thuộc môi trường
    torch = None

requires_torch = pytest.mark.skipif(torch is None, reason="cần torch")

# Thành phần lớp thật của trainval (AGENTS.md §5): HCC 125, u máu 63, ICC 46, ...
LABELS_THAT = [0] * 63 + [1] * 46 + [2] * 42 + [3] * 40 + [4] * 42 + [5] * 36 + [6] * 125


# --- effective_number_weights ------------------------------------------------


def test_trung_binh_bang_1():
    """Chuẩn hoá về trung bình 1 để đổi weighting không kéo theo đổi lr hiệu dụng."""
    w = effective_number_weights(LABELS_THAT)
    assert w.mean() == pytest.approx(1.0)


def test_lop_hiem_duoc_trong_so_cao_hon():
    w = effective_number_weights(LABELS_THAT)
    assert w[5] > w[6], "FNH (36 ca) phải nặng hơn HCC (125 ca)"


def test_tang_cham_hon_nghich_tan_suat():
    """Điểm khác biệt của class-balanced so với nghịch tần suất trần."""
    from src.train.loop import class_weights_from_labels

    eff = effective_number_weights(LABELS_THAT)
    inv = class_weights_from_labels(LABELS_THAT)
    assert eff.max() / eff.min() < inv.max() / inv.min()


def test_lop_vang_mat_nhan_trong_so_1():
    w = effective_number_weights([0] * 10 + [1] * 5)
    assert w[6] == pytest.approx(1.0)


def test_beta_nho_cho_trong_so_gan_deu():
    w = effective_number_weights(LABELS_THAT, beta=0.01)
    np.testing.assert_allclose(w, np.ones(7), atol=0.02)


@pytest.mark.parametrize("bad", [-0.1, 1.0, 1.5])
def test_beta_ngoai_khoang_thi_no(bad):
    with pytest.raises(ValueError):
        effective_number_weights(LABELS_THAT, beta=bad)


# --- focal loss --------------------------------------------------------------


@requires_torch
def test_focal_gamma_0_bang_cross_entropy():
    """γ=0 phải cho lại ĐÚNG cross-entropy — neo tính đúng đắn của cả module."""
    from src.train.losses import focal_loss

    torch.manual_seed(0)
    logits = torch.randn(32, 7)
    targets = torch.randint(0, 7, (32,))
    torch.testing.assert_close(
        focal_loss(logits, targets, gamma=0.0),
        torch.nn.functional.cross_entropy(logits, targets),
    )


@requires_torch
def test_focal_gamma_0_co_trong_so_bang_cross_entropy_co_trong_so():
    from src.train.losses import focal_loss

    torch.manual_seed(1)
    logits = torch.randn(64, 7)
    targets = torch.randint(0, 7, (64,))
    w = torch.rand(7) + 0.5
    torch.testing.assert_close(
        focal_loss(logits, targets, gamma=0.0, weight=w),
        torch.nn.functional.cross_entropy(logits, targets, weight=w),
    )


@requires_torch
def test_focal_ha_dong_gop_cua_ca_da_dung_chac():
    """Đây là cơ chế mà toàn bộ lý do dùng focal dựa vào."""
    from src.train.losses import focal_loss

    de = torch.tensor([[8.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]])  # đoán đúng, rất chắc
    kho = torch.tensor([[0.4, 0.3, 0.1, 0.05, 0.05, 0.05, 0.05]])
    y = torch.tensor([0])

    ce_de = focal_loss(de, y, gamma=0.0).item()
    ce_kho = focal_loss(kho, y, gamma=0.0).item()
    fl_de = focal_loss(de, y, gamma=2.0).item()
    fl_kho = focal_loss(kho, y, gamma=2.0).item()

    # Ca dễ bị hạ mạnh hơn ca khó rất nhiều.
    assert fl_de / ce_de < fl_kho / ce_kho / 100


@requires_torch
def test_focal_khong_am_va_huu_han():
    from src.train.losses import focal_loss

    torch.manual_seed(2)
    for scale in (1.0, 50.0):  # 50 để ép xác suất bão hoà, kiểm ổn định số học
        logits = torch.randn(16, 7) * scale
        loss = focal_loss(logits, torch.randint(0, 7, (16,)), gamma=2.0)
        assert torch.isfinite(loss) and loss.item() >= 0.0


@requires_torch
def test_focal_gamma_am_thi_no():
    from src.train.losses import focal_loss

    with pytest.raises(ValueError):
        focal_loss(torch.randn(4, 7), torch.zeros(4, dtype=torch.long), gamma=-1.0)


# --- build_criterion ---------------------------------------------------------


@requires_torch
def test_build_criterion_mac_dinh_la_cross_entropy_tran():
    c = build_criterion({}, LABELS_THAT, torch.device("cpu"))
    assert isinstance(c, torch.nn.CrossEntropyLoss)
    assert c.weight is None


@requires_torch
@pytest.mark.parametrize("mode", ["balanced", "effective_number"])
def test_build_criterion_gan_trong_so(mode):
    c = build_criterion({"loss": {"class_weights": mode}}, LABELS_THAT, torch.device("cpu"))
    assert c.weight is not None and c.weight.shape == (7,)


@requires_torch
def test_build_criterion_focal_chay_duoc():
    c = build_criterion({"loss": {"name": "focal", "gamma": 2.0}}, LABELS_THAT, torch.device("cpu"))
    loss = c(torch.randn(8, 7), torch.randint(0, 7, (8,)))
    assert torch.isfinite(loss)


@requires_torch
@pytest.mark.parametrize("cfg", [{"name": "khong-ton-tai"}, {"class_weights": "khong-ton-tai"}])
def test_build_criterion_tu_choi_gia_tri_la(cfg):
    with pytest.raises(ValueError):
        build_criterion({"loss": cfg}, LABELS_THAT, torch.device("cpu"))
