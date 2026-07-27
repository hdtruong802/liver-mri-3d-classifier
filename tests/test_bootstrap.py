"""Test CI bootstrap mức bệnh nhân."""

import numpy as np
import pytest
from src.eval.bootstrap import (
    N_RESAMPLES,
    bootstrap_all,
    bootstrap_metric,
    default_metrics,
    format_ci,
    stratified_indices,
)
from src.eval.metrics import accuracy, macro_f1

RNG = np.random.default_rng(0)


def test_point_estimate_is_the_metric_on_original_data():
    """`point` phải là metric trên dữ liệu gốc, KHÔNG phải trung bình bootstrap.

    Trung bình của các lần lấy mẫu lại là ước lượng lệch của chính nó; báo nó ra thay
    cho giá trị thật là một lỗi tinh vi và khó phát hiện về sau.
    """
    y_true = RNG.integers(0, 7, 200)
    y_pred = RNG.integers(0, 7, 200)
    result = bootstrap_metric(y_true, y_pred, macro_f1, n_resamples=N_RESAMPLES)

    assert result["point"] == pytest.approx(macro_f1(y_true, y_pred))


def test_ci_brackets_the_point_estimate():
    y_true = RNG.integers(0, 7, 200)
    y_pred = np.where(RNG.random(200) < 0.6, y_true, RNG.integers(0, 7, 200))
    result = bootstrap_metric(y_true, y_pred, macro_f1)

    assert result["ci_low"] <= result["point"] <= result["ci_high"]


def test_smaller_sample_gives_wider_ci():
    """Đúng tính chất khiến CI đáng giá: 82 bệnh nhân phải cho CI rộng hơn 394."""
    rng = np.random.default_rng(1)
    big_true = rng.integers(0, 7, 394)
    big_pred = np.where(rng.random(394) < 0.6, big_true, rng.integers(0, 7, 394))
    small_true, small_pred = big_true[:82], big_pred[:82]

    wide = bootstrap_metric(small_true, small_pred, macro_f1)
    narrow = bootstrap_metric(big_true, big_pred, macro_f1)

    assert (wide["ci_high"] - wide["ci_low"]) > (narrow["ci_high"] - narrow["ci_low"])


def test_perfect_prediction_has_degenerate_ci():
    y = np.tile(np.arange(7), 20)
    result = bootstrap_metric(y, y, macro_f1)

    assert result["point"] == pytest.approx(1.0)
    assert result["ci_low"] == pytest.approx(1.0)


def test_stratified_resample_preserves_class_counts():
    """Không giữ số ca mỗi lớp thì mẫu lặp có thể mất hẳn lớp hiếm -> macro-F1 méo."""
    labels = np.array([0] * 50 + [2] * 3 + [6] * 20)
    idx = stratified_indices(labels, np.random.default_rng(0))
    resampled = labels[idx]

    for value in np.unique(labels):
        assert (resampled == value).sum() == (labels == value).sum()


def test_rejects_too_few_resamples():
    """AGENTS.md §3.5 đặt sàn 2000 lần — chặn ngay tại API, không để tuỳ tiện."""
    y = np.arange(7)
    with pytest.raises(ValueError, match="2000"):
        bootstrap_metric(y, y, macro_f1, n_resamples=100)


def test_rejects_mismatched_lengths():
    with pytest.raises(ValueError, match="khác độ dài"):
        bootstrap_metric(np.arange(5), np.arange(3), accuracy)


def test_same_seed_reproduces_ci():
    y_true = RNG.integers(0, 7, 120)
    y_pred = RNG.integers(0, 7, 120)
    first = bootstrap_metric(y_true, y_pred, macro_f1, seed=7)
    second = bootstrap_metric(y_true, y_pred, macro_f1, seed=7)

    assert first == second


def test_bootstrap_all_covers_default_metrics():
    y_true = RNG.integers(0, 7, 150)
    y_pred = RNG.integers(0, 7, 150)
    results = bootstrap_all(y_true, y_pred, default_metrics())

    assert set(results) == {"macro_f1", "cohen_kappa", "balanced_accuracy", "accuracy"}
    for value in results.values():
        assert value["ci_low"] <= value["point"] <= value["ci_high"]
        assert value["n_patients"] == 150


def test_format_ci_is_readable():
    text = format_ci({"point": 0.2647, "ci_low": 0.1804, "ci_high": 0.3512})
    assert text == "0.2647 [0.1804, 0.3512]"
