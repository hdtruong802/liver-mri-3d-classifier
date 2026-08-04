"""Test MC-dropout.

Phần tổng hợp (`report_members`) chạy trên `.npz` giả nên không cần torch. Phần
bật/tắt dropout thì cần torch thật và sẽ tự skip nếu chưa cài.
"""

from pathlib import Path

import numpy as np
import pytest
from src.eval.mc_dropout import save_member_probs
from src.eval.trust import report_members

try:
    import torch
except ImportError:  # pragma: no cover - phụ thuộc môi trường
    torch = None

# Chỉ các test chạm model thật mới cần torch; phần tổng hợp `.npz` thì không, và
# gate cả file bằng `importorskip` sẽ giấu mất chúng trên máy chưa cài torch.
requires_torch = pytest.mark.skipif(torch is None, reason="cần torch")


def _members(k: int, n: int, seed: int, spread: float = 0.3) -> np.ndarray:
    """`k` thành viên bất đồng nhau vừa phải trên `n` ca."""
    rng = np.random.default_rng(seed)
    base = rng.normal(0.0, 1.0, size=(n, 7))
    out = []
    for _ in range(k):
        logits = base + rng.normal(0.0, spread, size=(n, 7))
        logits -= logits.max(axis=1, keepdims=True)
        p = np.exp(logits)
        out.append(p / p.sum(axis=1, keepdims=True))
    return np.stack(out)


def _write(directory: Path, k: int, n: int, seed: int, offset: int, spread: float = 0.3) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    members = _members(k, n, seed, spread)
    save_member_probs(
        directory / "mc_dropout.npz",
        {
            "member_probs": members,
            "labels": np.random.default_rng(seed).integers(0, 7, size=n),
            "patient_ids": [f"MR-{offset + i}" for i in range(n)],
            "n_passes": k,
        },
    )


@pytest.fixture
def members_dir(tmp_path: Path) -> Path:
    offset = 0
    for fold, n in enumerate((30, 25, 20), start=1):
        _write(tmp_path / f"fold_{fold}", k=8, n=n, seed=fold, offset=offset)
        offset += n
    return tmp_path


# --- enable_dropout ----------------------------------------------------------


def _net():
    """Dựng trong hàm, không ở module level — module này phải import được khi thiếu torch."""

    class Net(torch.nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.bn = torch.nn.BatchNorm1d(4)
            self.drop = torch.nn.Dropout(0.5)
            self.fc = torch.nn.Linear(4, 7)

        def forward(self, x):
            return self.fc(self.drop(self.bn(x)))

    return Net()


@requires_torch
def test_enable_dropout_bat_dropout_nhung_GIU_batchnorm_o_eval():
    """Bất biến trung tâm: BatchNorm phải ở eval, nếu không ca này ảnh hưởng ca kia."""
    from src.eval.mc_dropout import enable_dropout

    net = _net()
    n = enable_dropout(net)

    assert n == 1
    assert net.drop.training is True, "dropout phải bật"
    assert net.bn.training is False, "BatchNorm phải Ở EVAL — xem docstring module"


@requires_torch
def test_enable_dropout_cho_ket_qua_khac_nhau_giua_cac_pass():
    from src.eval.mc_dropout import enable_dropout

    net = _net()
    enable_dropout(net)
    x = torch.randn(16, 4)
    with torch.no_grad():
        a, b = net(x), net(x)
    assert not torch.allclose(a, b), "dropout bật thì hai lượt phải khác nhau"


@requires_torch
def test_batchnorm_o_eval_thi_du_doan_khong_phu_thuoc_ca_khac_trong_batch():
    """Nếu ai đó đổi sang `model.train()`, test này đỏ."""
    from src.eval.mc_dropout import enable_dropout

    net = _net()
    net.bn.running_mean.fill_(0.0)
    net.bn.running_var.fill_(1.0)
    enable_dropout(net)
    net.drop.eval()  # tắt dropout để cô lập đúng ảnh hưởng của BatchNorm

    x = torch.randn(8, 4)
    with torch.no_grad():
        rieng = net(x[:1])
        chung = net(x)[:1]
    torch.testing.assert_close(rieng, chung)


@requires_torch
def test_count_dropout_modules():
    from src.eval.mc_dropout import count_dropout_modules

    assert count_dropout_modules(_net()) == 1
    assert count_dropout_modules(torch.nn.Linear(4, 7)) == 0


@requires_torch
def test_mc_dropout_predict_no_neu_model_khong_co_dropout():
    from src.eval.mc_dropout import mc_dropout_predict

    net = torch.nn.Linear(4, 7)
    with pytest.raises(RuntimeError, match="không có lớp Dropout"):
        mc_dropout_predict(net, [], torch.device("cpu"), n_passes=2)


# --- report_members ----------------------------------------------------------


def test_report_members_gop_dung_so_ca(members_dir: Path):
    r = report_members(members_dir)
    assert r["n_folds"] == 3
    assert r["n_patients"] == 75
    assert r["n_passes"] == [8]
    assert set(r["selective"]) == {"max-prob", "-entropy toàn phần", "-epistemic"}


def test_report_members_epistemic_duong_khi_cac_thanh_vien_bat_dong(members_dir: Path):
    r = report_members(members_dir)
    assert r["epistemic_summary"]["mean"] > 0.0


def test_report_members_epistemic_bang_0_khi_cac_thanh_vien_giong_het(tmp_path: Path):
    """Chế độ hỏng thầm lặng: dropout không bật thì mọi thành viên như nhau."""
    _write(tmp_path / "fold_1", k=5, n=20, seed=0, offset=0, spread=0.0)
    r = report_members(tmp_path)
    assert r["epistemic_summary"]["max"] == pytest.approx(0.0, abs=1e-9)


def test_report_members_chan_benh_nhan_trung_giua_hai_fold(tmp_path: Path):
    _write(tmp_path / "fold_1", k=4, n=10, seed=1, offset=0)
    _write(tmp_path / "fold_2", k=4, n=10, seed=2, offset=0)  # cùng offset -> trùng id
    with pytest.raises(ValueError, match="có ở cả"):
        report_members(tmp_path)


def test_report_members_bao_loi_khi_khong_co_file(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        report_members(tmp_path)


def test_report_members_tu_choi_member_probs_sai_chieu(tmp_path: Path):
    d = tmp_path / "fold_1"
    d.mkdir(parents=True)
    np.savez_compressed(
        d / "mc_dropout.npz",
        member_probs=np.ones((10, 7)),  # thiếu chiều K
        labels=np.zeros(10, dtype=np.int64),
        patient_ids=np.array([f"MR-{i}" for i in range(10)]),
        n_passes=1,
    )
    with pytest.raises(ValueError, match="phải là"):
        report_members(tmp_path)
