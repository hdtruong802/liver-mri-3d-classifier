"""Test bảng trustworthiness — chạy trên .npz giả, không cần torch/GPU.

Test quan trọng nhất của file này là `test_temperature_khong_nhin_thay_fold_cua_no`:
nó là thứ chặn dạng leakage mà `src/eval/trust.py` được viết ra để tránh.
"""

from pathlib import Path

import numpy as np
import pytest
from src.eval.calibration import (
    adaptive_calibration_error,
    apply_temperature,
    fit_temperature,
    fit_temperature_min_ece,
)
from src.eval.trust import (
    COVERAGES,
    calibration_row,
    fit_temperature_leave_one_fold_out,
    report,
    selective_row,
)

N_CLASSES = 7


def _overconfident(n: int, seed: int, sharpness: float = 4.0) -> tuple[np.ndarray, np.ndarray]:
    """Sinh dự đoán tự tin quá mức: đúng ~70% nhưng luôn nói gần như chắc chắn."""
    rng = np.random.default_rng(seed)
    labels = rng.integers(0, N_CLASSES, size=n)
    logits = rng.normal(0.0, 1.0, size=(n, N_CLASSES))
    # 70% số ca được đẩy lớp đúng lên đầu; phần còn lại để model đoán sai.
    correct = rng.random(n) < 0.7
    logits[correct, labels[correct]] += 3.0
    logits *= sharpness
    logits -= logits.max(axis=1, keepdims=True)
    probs = np.exp(logits)
    probs /= probs.sum(axis=1, keepdims=True)
    return probs, labels


def _write_fold(directory: Path, n: int, seed: int, offset: int) -> None:
    probs, labels = _overconfident(n, seed)
    directory.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        directory / "val_probs_best.npz",
        probs=probs,
        labels=labels,
        patient_ids=np.array([f"MR-{offset + i}" for i in range(n)]),
        epoch=42,
    )


@pytest.fixture
def run_dir(tmp_path: Path) -> Path:
    """Ba fold, bệnh nhân không trùng nhau — phân hoạch hợp lệ."""
    offset = 0
    for fold, n in enumerate((40, 35, 30), start=1):
        _write_fold(tmp_path / f"fold_{fold}", n, seed=fold, offset=offset)
        offset += n
    return tmp_path


# --- fit_temperature_min_ece -------------------------------------------------


def test_fit_ece_tra_ve_T_lon_hon_1_khi_tu_tin_qua_muc():
    probs, labels = _overconfident(600, seed=0)
    assert fit_temperature_min_ece(probs, labels) > 1.0


def test_fit_ece_ha_duoc_ece_so_voi_ban_goc():
    probs, labels = _overconfident(600, seed=1)
    t = fit_temperature_min_ece(probs, labels)
    truoc = adaptive_calibration_error(probs, labels)
    sau = adaptive_calibration_error(apply_temperature(probs, t), labels)
    assert sau < truoc


def test_fit_ece_va_fit_nll_khong_bat_buoc_trung_nhau():
    """Hai mục tiêu khác nhau — đây là lý do tồn tại của hàm thứ hai."""
    probs, labels = _overconfident(800, seed=2)
    assert fit_temperature_min_ece(probs, labels) != pytest.approx(
        fit_temperature(probs, labels), abs=0.05
    )


@pytest.mark.parametrize("bad", [(0.0, 5.0), (5.0, 1.0), (-1.0, 2.0)])
def test_fit_ece_tu_choi_bounds_hong(bad):
    probs, labels = _overconfident(50, seed=3)
    with pytest.raises(ValueError):
        fit_temperature_min_ece(probs, labels, bounds=bad)


def test_fit_ece_tu_choi_n_points_qua_nho():
    probs, labels = _overconfident(50, seed=4)
    with pytest.raises(ValueError):
        fit_temperature_min_ece(probs, labels, n_points=1)


# --- leave-one-fold-out ------------------------------------------------------


def test_lofo_giu_nguyen_so_ca_va_thu_tu(run_dir: Path):
    from src.eval.run import BEST, find_fold_predictions, load_predictions, pool_out_of_fold

    preds = {n: load_predictions(p) for n, p in find_fold_predictions(run_dir, BEST).items()}
    pooled = pool_out_of_fold(preds)
    probs, labels, temps = fit_temperature_leave_one_fold_out(preds)

    assert probs.shape == pooled["probs"].shape
    np.testing.assert_array_equal(labels, pooled["labels"])
    assert set(temps) == set(preds)
    np.testing.assert_allclose(probs.sum(axis=1), 1.0, atol=1e-9)


def test_lofo_khong_doi_du_doan_argmax(run_dir: Path):
    """Temperature scaling không được đổi lớp đoán — nếu đổi thì macro-F1 sẽ trôi."""
    from src.eval.run import BEST, find_fold_predictions, load_predictions, pool_out_of_fold

    preds = {n: load_predictions(p) for n, p in find_fold_predictions(run_dir, BEST).items()}
    pooled = pool_out_of_fold(preds)
    probs, _, _ = fit_temperature_leave_one_fold_out(preds)
    np.testing.assert_array_equal(probs.argmax(axis=1), pooled["probs"].argmax(axis=1))


def test_temperature_khong_nhin_thay_fold_cua_no(run_dir: Path):
    """Chặn leakage: `T` của một fold phải bằng `T` fit trên đúng các fold KHÁC.

    Đây là bất biến trung tâm của module. Nếu ai đó "đơn giản hoá" thành fit một
    `T` chung trên cả tập gộp thì test này đỏ.
    """
    from src.eval.run import BEST, find_fold_predictions, load_predictions

    preds = {n: load_predictions(p) for n, p in find_fold_predictions(run_dir, BEST).items()}
    _, _, temps = fit_temperature_leave_one_fold_out(preds)

    for held_out in preds:
        others = [n for n in sorted(preds) if n != held_out]
        expected = fit_temperature(
            np.concatenate([preds[n]["probs"] for n in others]),
            np.concatenate([preds[n]["labels"] for n in others]),
        )
        assert temps[held_out] == pytest.approx(expected, abs=1e-9)

    # Và các T phải thực sự khác nhau, nếu không test trên là vô nghĩa.
    assert len(set(np.round(list(temps.values()), 6))) > 1


def test_lofo_can_it_nhat_hai_fold(run_dir: Path):
    from src.eval.run import BEST, find_fold_predictions, load_predictions

    preds = {n: load_predictions(p) for n, p in find_fold_predictions(run_dir, BEST).items()}
    with pytest.raises(ValueError, match="ít nhất 2 fold"):
        fit_temperature_leave_one_fold_out({"fold_1": preds["fold_1"]})


# --- selective_row -----------------------------------------------------------


def test_selective_row_du_khoa(run_dir: Path):
    probs, labels = _overconfident(200, seed=7)
    row = selective_row(labels, probs, probs.max(axis=1))
    for c in COVERAGES:
        assert f"f1@{c:.0%}" in row["at_coverage"]
        assert f"acc@{c:.0%}" in row["at_coverage"]
    assert 0.0 <= row["aurc"] <= 1.0
    assert row["risk_full"] == pytest.approx(1.0 - (probs.argmax(axis=1) == labels).mean())


def test_diem_tin_cay_tot_hon_ngau_nhien(run_dir: Path):
    """AURC của max-prob phải thấp hơn AURC của điểm ngẫu nhiên."""
    probs, labels = _overconfident(600, seed=8)
    that = selective_row(labels, probs, probs.max(axis=1))["aurc"]
    rng = np.random.default_rng(0)
    ngau_nhien = np.mean(
        [selective_row(labels, probs, rng.random(len(labels)))["aurc"] for _ in range(20)]
    )
    assert that < ngau_nhien


# --- report ------------------------------------------------------------------


def test_report_du_khoa_va_macro_f1_khong_doi(run_dir: Path):
    # 2000 là sàn cứng do `src/eval/bootstrap.py` ép theo AGENTS.md §3.5 — không
    # hạ xuống được cho nhanh, và đó là chủ ý.
    r = report(run_dir, n_resamples=2000)

    assert r["n_folds"] == 3
    assert r["n_patients"] == 105
    assert set(r["temperature"]["leave_one_fold_out"]) == {"nll", "ece"}

    f1 = {k: v["macro_f1"] for k, v in r["calibration"].items()}
    assert f1["raw"] == pytest.approx(f1["temp_scaled_nll"])
    assert f1["raw"] == pytest.approx(f1["temp_scaled_ece"])

    assert r["aurc_reference"]["oracle"] < r["aurc_reference"]["chance"]
    assert set(r["ci"]) == {"macro_f1_full", "macro_f1_at_80"}


def test_report_bao_loi_khi_khong_co_fold(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        report(tmp_path)


def test_calibration_row_du_khoa():
    probs, labels = _overconfident(100, seed=9)
    row = calibration_row(probs, labels)
    assert set(row) == {"ece", "mce", "brier", "nll", "macro_f1"}
    assert all(np.isfinite(v) for v in row.values())
