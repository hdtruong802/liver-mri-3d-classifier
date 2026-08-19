"""Test TTA.

EMA đã được gỡ khỏi repo (WORKLOG S-197) nên phần test của nó cũng đi theo.

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
