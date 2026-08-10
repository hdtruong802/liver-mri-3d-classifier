"""Test phép so có ghép cặp giữa hai run.

Thứ đáng test nhất ở đây không phải con số mà là **các cổng**: một phép so lệch bệnh
nhân, lệch thứ tự, hay lấy fold không có ở cả hai bên vẫn in ra một bảng trông rất hợp
lý. Không cổng nào thì sai đó không bao giờ tự lộ.
"""

from __future__ import annotations

import numpy as np
import pytest
from src.eval.compare import align, compare, fold_number, paired_test, two_sided_p


def _write(dir_path, pids, labels, probs, name="val_probs_best.npz"):
    dir_path.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        dir_path / name,
        probs=np.asarray(probs, dtype=float),
        labels=np.asarray(labels, dtype=int),
        patient_ids=np.array(list(pids)),
        epoch=7,
    )


def _probs(labels, strength, seed):
    rng = np.random.default_rng(seed)
    logits = rng.normal(size=(len(labels), 7))
    logits[np.arange(len(labels)), labels] += strength
    p = np.exp(logits)
    return p / p.sum(axis=1, keepdims=True)


# --- suy số fold từ tên thư mục ------------------------------------------------


def test_fold_number_nhan_ca_ba_kieu_ten():
    """Hai run khác kiến trúc có hash khác nhau trong tên thư mục, nên khớp theo TÊN
    là không bao giờ khớp. Phải khớp theo SỐ."""
    assert fold_number("fold_1") == 1
    assert fold_number("fold2") == 2
    assert fold_number("fold3_4c2cf705") == 3


def test_fold_number_no_khi_khong_suy_duoc():
    with pytest.raises(ValueError, match="không suy được số fold"):
        fold_number("linh_tinh")


# --- cổng ghép cặp -------------------------------------------------------------


def test_align_sap_lai_thu_tu_benh_nhan():
    """Thứ tự lưu trong hai file không nhất thiết giống nhau. Lệch thứ tự mà không sắp
    lại thì phép ghép cặp ghép sai người với người, và ra nhiễu thuần."""
    labels = np.array([0, 1, 2])
    a = {"patient_ids": ["MR1", "MR2", "MR3"], "labels": labels, "probs": np.eye(7)[[0, 1, 2]]}
    b = {
        "patient_ids": ["MR3", "MR1", "MR2"],
        "labels": np.array([2, 0, 1]),
        "probs": np.eye(7)[[2, 0, 1]],
    }
    got_labels, pa, pb = align(a, b, fold=1)
    np.testing.assert_array_equal(got_labels, labels)
    np.testing.assert_allclose(pa, pb), "sau khi sắp, hai bên phải trỏ cùng bệnh nhân"


def test_align_no_khi_tap_benh_nhan_lech():
    a = {"patient_ids": ["MR1", "MR2"], "labels": np.array([0, 1]), "probs": np.eye(7)[[0, 1]]}
    b = {"patient_ids": ["MR1", "MR9"], "labels": np.array([0, 1]), "probs": np.eye(7)[[0, 1]]}
    with pytest.raises(ValueError, match="tập bệnh nhân lệch"):
        align(a, b, fold=1)


def test_align_no_khi_nhan_that_lech():
    """Cùng bệnh nhân mà nhãn thật khác nhau nghĩa là một bên đọc sai split."""
    a = {"patient_ids": ["MR1", "MR2"], "labels": np.array([0, 1]), "probs": np.eye(7)[[0, 1]]}
    b = {"patient_ids": ["MR1", "MR2"], "labels": np.array([0, 5]), "probs": np.eye(7)[[0, 1]]}
    with pytest.raises(ValueError, match="nhãn thật khác nhau"):
        align(a, b, fold=1)


# --- phép kiểm -----------------------------------------------------------------


def test_hai_run_giong_het_cho_hieu_0_va_P_1():
    """Bẫy đã dính một lần: `2 * min(m, 1 - m)` cho P = 0 khi mọi hiệu bằng 0, tức
    tuyên bố ý nghĩa tối đa cho một hiệu ứng bằng không."""
    rng = np.random.default_rng(0)
    labels = rng.integers(0, 7, 120)
    probs = _probs(labels, 2.0, seed=1)
    r = paired_test(labels, probs, probs, n_resamples=200)
    assert r["diff"] == pytest.approx(0.0)
    assert r["p"] == pytest.approx(1.0)


def test_bat_duoc_hieu_ung_that_va_dung_dau():
    rng = np.random.default_rng(2)
    labels = rng.integers(0, 7, 300)
    yeu = _probs(labels, 0.3, seed=3)
    manh = _probs(labels, 3.0, seed=4)
    r = paired_test(labels, yeu, manh, n_resamples=300)
    assert r["diff"] > 0.1, "candidate mạnh hơn rõ rệt mà hiệu không dương"
    assert r["lo"] > 0, "CI phải hoàn toàn dương khi hiệu ứng rõ"
    assert r["p"] < 0.05


def test_two_sided_p_trong_khoang_0_1():
    assert two_sided_p(np.zeros(500)) == pytest.approx(1.0)
    assert two_sided_p(np.full(500, 0.05)) == pytest.approx(0.0)
    assert 0.0 <= two_sided_p(np.random.default_rng(0).normal(size=500)) <= 1.0


# --- cổng "chỉ dùng fold có ở cả hai bên" --------------------------------------


def test_chi_dung_fold_co_o_ca_hai_ben(tmp_path, monkeypatch):
    """Gộp 5 fold của một bên với 2 fold của bên kia là so trên hai tập bệnh nhân khác
    nhau, mà con số ra vẫn trông hợp lý."""
    monkeypatch.setattr("src.eval.compare.resolve_repo_path", lambda p: p)
    rng = np.random.default_rng(5)

    a_root, b_root = tmp_path / "A", tmp_path / "B"
    for fold in (1, 2, 3):
        pids = [f"MR{fold}{i:03d}" for i in range(30)]
        labels = rng.integers(0, 7, 30)
        _write(a_root / f"fold_{fold}", pids, labels, _probs(labels, 1.0, seed=10 + fold))
        if fold <= 2:  # candidate chỉ có fold 1, 2
            _write(
                b_root / f"fold{fold}_abc12345", pids, labels, _probs(labels, 1.5, seed=20 + fold)
            )

    r = compare(a_root, b_root, n_resamples=100)
    assert r["folds"] == [1, 2]
    assert r["bo_qua"]["baseline"] == [3]
    assert r["n"] == 60, "chỉ được gộp 2 fold × 30 ca"


def test_no_khi_khong_fold_nao_trung(tmp_path, monkeypatch):
    monkeypatch.setattr("src.eval.compare.resolve_repo_path", lambda p: p)
    rng = np.random.default_rng(6)
    labels = rng.integers(0, 7, 20)
    pids = [f"MR{i:03d}" for i in range(20)]
    _write(tmp_path / "A" / "fold_1", pids, labels, _probs(labels, 1.0, seed=1))
    _write(tmp_path / "B" / "fold_4", pids, labels, _probs(labels, 1.0, seed=2))
    with pytest.raises(ValueError, match="không fold nào có ở cả hai bên"):
        compare(tmp_path / "A", tmp_path / "B", n_resamples=50)


def test_khong_thay_file_thi_no_ro_rang(tmp_path, monkeypatch):
    monkeypatch.setattr("src.eval.compare.resolve_repo_path", lambda p: p)
    (tmp_path / "rong").mkdir()
    with pytest.raises(FileNotFoundError, match="không thấy"):
        compare(tmp_path / "rong", tmp_path / "rong")
