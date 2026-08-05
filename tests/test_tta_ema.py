"""Test TTA và EMA.

`flip_combinations` thuần tổ hợp nên chạy không cần torch. Phần còn lại cần torch và
tự skip — máy phát triển không cài deep-learning stack (AGENTS.md §4).
"""

import numpy as np
import pytest
from src.eval.tta import FLIP_SETS, flip_combinations

try:
    import torch
except ImportError:  # pragma: no cover - phụ thuộc môi trường
    torch = None

requires_torch = pytest.mark.skipif(torch is None, reason="cần torch")


# --- flip_combinations (không cần torch) -------------------------------------


def test_so_luot_la_2_mu_so_truc():
    for axes in ((), (1,), (1, 2), (1, 2, 3)):
        assert len(flip_combinations(axes)) == 2 ** len(axes)


def test_luot_dau_luon_la_anh_goc():
    """`probs_per_view[0]` phải so được trực tiếp với kết quả không TTA."""
    assert flip_combinations(FLIP_SETS["all"])[0] == ()


def test_khong_luot_nao_trung_nhau():
    combos = flip_combinations(FLIP_SETS["all"])
    assert len(set(combos)) == len(combos)


def test_flip_sets_dung_truc():
    """Trục tính trên tensor MỘT MẪU `[C, X, Y, Z]`; `tta_predict` tự cộng 1."""
    assert FLIP_SETS["inplane"] == (1, 2)
    assert FLIP_SETS["all"] == (1, 2, 3)
    assert 0 not in FLIP_SETS["all"], "trục 0 là kênh — lật nó là trộn 8 thì MRI"


# --- TTA với model thật ------------------------------------------------------


def _loader(n: int = 6, channels: int = 8, size: tuple[int, int, int] = (8, 8, 4)):
    rng = np.random.default_rng(0)
    images = torch.from_numpy(rng.random((n, channels, *size)).astype(np.float32))
    return [
        {
            "image": images[i : i + 2],
            "label": torch.arange(i, i + 2) % 7,
            "patient_id": [f"MR-{i}", f"MR-{i + 1}"],
        }
        for i in range(0, n, 2)
    ]


@requires_torch
def test_tta_tra_ve_dung_hinh_dang():
    from src.eval.tta import tta_predict

    model = torch.nn.Sequential(
        torch.nn.AdaptiveAvgPool3d(1), torch.nn.Flatten(), torch.nn.Linear(8, 7)
    )
    out = tta_predict(model, _loader(), torch.device("cpu"), axes=FLIP_SETS["inplane"], amp=False)

    assert out["probs"].shape == (6, 7)
    assert out["probs_per_view"].shape == (4, 6, 7)
    np.testing.assert_allclose(out["probs"].sum(axis=1), 1.0, atol=1e-5)


@requires_torch
def test_tta_la_trung_binh_cua_cac_luot():
    from src.eval.tta import tta_predict

    model = torch.nn.Sequential(
        torch.nn.AdaptiveAvgPool3d(1), torch.nn.Flatten(), torch.nn.Linear(8, 7)
    )
    out = tta_predict(model, _loader(), torch.device("cpu"), axes=FLIP_SETS["all"], amp=False)
    np.testing.assert_allclose(out["probs"], out["probs_per_view"].mean(axis=0), atol=1e-6)


@requires_torch
def test_model_bat_bien_voi_lat_thi_TTA_khong_doi_gi():
    """Neo ý nghĩa của TTA: nó chỉ thêm giá trị khi model CHƯA bất biến.

    `AdaptiveAvgPool3d` bất biến hoàn toàn với lật, nên mọi lượt phải trùng nhau. Nếu
    test này đỏ thì `tta_predict` đang lật nhầm trục (ví dụ lật chiều kênh).
    """
    from src.eval.tta import tta_predict

    model = torch.nn.Sequential(
        torch.nn.AdaptiveAvgPool3d(1), torch.nn.Flatten(), torch.nn.Linear(8, 7)
    )
    out = tta_predict(model, _loader(), torch.device("cpu"), axes=FLIP_SETS["all"], amp=False)
    for view in range(1, out["probs_per_view"].shape[0]):
        np.testing.assert_allclose(out["probs_per_view"][view], out["probs_per_view"][0], atol=1e-5)


@requires_torch
def test_tta_tra_model_ve_dung_che_do():
    from src.eval.tta import tta_predict

    model = torch.nn.Sequential(
        torch.nn.AdaptiveAvgPool3d(1), torch.nn.Flatten(), torch.nn.Linear(8, 7)
    )
    model.train()
    tta_predict(model, _loader(), torch.device("cpu"), axes=(), amp=False)
    assert model.training is True


# --- EMA ---------------------------------------------------------------------


def _net():
    return torch.nn.Sequential(torch.nn.Linear(4, 4), torch.nn.BatchNorm1d(4))


@requires_torch
def test_ema_tu_choi_decay_ngoai_khoang():
    from src.train.ema import ModelEma

    for bad in (0.0, 1.0, -0.5, 1.5):
        with pytest.raises(ValueError, match="decay"):
            ModelEma(_net(), decay=bad)


@requires_torch
def test_ema_bam_theo_trong_so_nhung_cham_hon():
    from src.train.ema import ModelEma

    net = _net()
    ema = ModelEma(net, decay=0.9, use_num_updates=False)
    goc = net[0].weight.detach().clone()

    with torch.no_grad():
        net[0].weight.add_(1.0)
    ema.update(net)

    # Sau MỘT bước: ema = 0.9*cũ + 0.1*mới, tức mới dịch 10% quãng đường.
    torch.testing.assert_close(ema.module[0].weight, goc + 0.1, rtol=1e-5, atol=1e-6)


@requires_torch
def test_ema_KHONG_trung_binh_buffer_cua_batchnorm():
    """Bất biến trung tâm — xem docstring `src/train/ema.py`.

    `running_mean` đã là thống kê trượt do BatchNorm tự duy trì; EMA chồng lên là làm
    trơn hai lần, và `num_batches_tracked` là số nguyên đếm bước.
    """
    from src.train.ema import ModelEma

    net = _net()
    ema = ModelEma(net, decay=0.9, use_num_updates=False)
    with torch.no_grad():
        net[1].running_mean.fill_(5.0)
        net[1].num_batches_tracked.fill_(42)
    ema.update(net)

    torch.testing.assert_close(ema.module[1].running_mean, net[1].running_mean)
    assert int(ema.module[1].num_batches_tracked) == 42, "buffer phải SAO CHÉP, không trung bình"


@requires_torch
def test_ema_warmup_dung_decay_nho_luc_dau():
    """Không có warmup thì vài epoch đầu EMA còn phần lớn là trọng số ngẫu nhiên."""
    from src.train.ema import ModelEma

    net = _net()
    ema = ModelEma(net, decay=0.999, use_num_updates=True)
    assert ema._current_decay() < 0.999
    ema.num_updates = 100_000
    assert ema._current_decay() == pytest.approx(0.999)


@requires_torch
def test_ema_khong_giu_gradient():
    """Bản EMA không bao giờ được train — nếu còn gradient thì nó sẽ bị optimizer đụng."""
    from src.train.ema import ModelEma

    ema = ModelEma(_net(), decay=0.9)
    assert not any(p.requires_grad for p in ema.module.parameters())


@requires_torch
def test_ema_state_dict_khu_hoi_duoc():
    from src.train.ema import ModelEma

    net = _net()
    a = ModelEma(net, decay=0.9)
    a.num_updates = 7
    b = ModelEma(net, decay=0.9)
    b.load_state_dict(a.state_dict())
    assert b.num_updates == 7
    torch.testing.assert_close(b.module[0].weight, a.module[0].weight)
