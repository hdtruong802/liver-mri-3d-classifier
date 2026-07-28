"""Test selective prediction: entropy, tách bất định, risk–coverage, AURC.

Dùng dữ liệu tổng hợp có tính chất đã biết. Trọng tâm là hai bất biến quan trọng:
điểm tin cậy **xếp hạng tốt** phải làm sai số giảm khi hạ coverage, và bất định
**toàn phần bằng nhau** vẫn có thể tách ra thành hai cấu tạo ngược nhau.
"""

import numpy as np
import pytest
from sklearn.metrics import f1_score
from src.eval.selective import (
    aurc,
    coverage_at_risk,
    metric_at_coverage,
    predictive_entropy,
    risk_coverage_curve,
    selective_accuracy,
    uncertainty_decomposition,
)


def _macro_f1(y_true, y_pred):
    return float(f1_score(y_true, y_pred, average="macro", zero_division=0))


# --- entropy -----------------------------------------------------------------


def test_entropy_bounds():
    one_hot = np.array([[1.0, 0.0, 0.0, 0.0]])
    uniform = np.full((1, 4), 0.25)
    assert predictive_entropy(one_hot)[0] == pytest.approx(0.0, abs=1e-9)
    assert predictive_entropy(uniform)[0] == pytest.approx(1.0, abs=1e-9)


def test_entropy_unnormalised_matches_nats():
    """Không chuẩn hoá thì entropy của phân bố đều 7 lớp phải bằng ln(7)."""
    uniform = np.full((1, 7), 1 / 7)
    assert predictive_entropy(uniform, normalise=False)[0] == pytest.approx(np.log(7))


def test_entropy_increases_with_spread():
    sharp = np.array([[0.92, 0.03, 0.02, 0.01, 0.01, 0.005, 0.005]])
    spread = np.array([[0.35, 0.30, 0.15, 0.10, 0.05, 0.03, 0.02]])
    assert predictive_entropy(sharp)[0] < predictive_entropy(spread)[0]


# --- tách aleatoric / epistemic ---------------------------------------------


def test_agreeing_but_unsure_is_aleatoric():
    """5 model đồng thuận mà đều lưỡng lự: bất định nằm ở dữ liệu, không ở model."""
    members = np.array(
        [
            [[0.40, 0.35, 0.10, 0.06, 0.04, 0.03, 0.02]],
            [[0.38, 0.37, 0.11, 0.05, 0.04, 0.03, 0.02]],
            [[0.42, 0.33, 0.09, 0.07, 0.04, 0.03, 0.02]],
            [[0.39, 0.36, 0.10, 0.06, 0.05, 0.02, 0.02]],
            [[0.41, 0.34, 0.10, 0.06, 0.04, 0.03, 0.02]],
        ]
    )
    out = uncertainty_decomposition(members)
    assert out["total"][0] > 0.6
    assert out["epistemic"][0] < 0.02, "model đồng thuận thì epistemic phải ~0"
    assert out["aleatoric"][0] == pytest.approx(out["total"][0], abs=0.02)


def test_disagreeing_but_confident_is_epistemic():
    """5 model đều chắc chắn nhưng chỉ vào 3 lớp khác nhau: dấu hiệu ca ngoài miền."""
    eps = 0.01

    def one_hot(i):
        p = np.full(7, eps)
        p[i] = 1 - 6 * eps
        return p

    members = np.array([[one_hot(i)] for i in (0, 1, 0, 2, 1)])
    out = uncertainty_decomposition(members)
    assert out["aleatoric"][0] < 0.2, "từng model rất chắc thì aleatoric phải thấp"
    assert out["epistemic"][0] > 0.4, "bất đồng mạnh thì epistemic phải cao"


def test_decomposition_sums_to_total():
    rng = np.random.default_rng(0)
    logits = rng.normal(size=(5, 50, 7))
    exp = np.exp(logits - logits.max(axis=2, keepdims=True))
    members = exp / exp.sum(axis=2, keepdims=True)
    out = uncertainty_decomposition(members)
    assert np.allclose(out["aleatoric"] + out["epistemic"], out["total"], atol=1e-9)
    assert (out["epistemic"] >= 0).all(), "mutual information không được âm"


def test_single_member_is_rejected():
    """Một model đơn lẻ không có epistemic uncertainty — phải báo lỗi, không trả 0."""
    with pytest.raises(ValueError, match="ít nhất 2 thành viên"):
        uncertainty_decomposition(np.full((1, 3, 7), 1 / 7))


# --- risk–coverage -----------------------------------------------------------


def test_perfect_ranking_gives_zero_risk_at_low_coverage():
    """Điểm tin cậy hoàn hảo đẩy mọi ca sai xuống cuối."""
    correct = np.array([True] * 80 + [False] * 20)
    scores = np.concatenate([np.linspace(1.0, 0.5, 80), np.linspace(0.4, 0.0, 20)])
    curve = risk_coverage_curve(correct, scores)
    assert curve.risk[:70].max() == pytest.approx(0.0)
    assert curve.coverage[-1] == pytest.approx(1.0)
    assert curve.risk[-1] == pytest.approx(0.20)


def test_full_coverage_risk_equals_overall_error_rate():
    """Bất kể xếp hạng thế nào, ở coverage 100% sai số phải bằng tỉ lệ lỗi chung."""
    rng = np.random.default_rng(1)
    correct = rng.random(200) < 0.7
    curve = risk_coverage_curve(correct, rng.random(200))
    assert curve.risk[-1] == pytest.approx(1.0 - correct.mean())


def test_good_scores_beat_random_scores_on_aurc():
    rng = np.random.default_rng(2)
    correct = rng.random(500) < 0.75
    informative = correct + rng.normal(0, 0.25, size=500)  # tương quan với đúng/sai
    assert aurc(correct, informative) < aurc(correct, rng.random(500))


def test_aurc_rejects_nan_scores():
    with pytest.raises(ValueError, match="NaN"):
        aurc(np.array([True, False]), np.array([1.0, np.nan]))


# --- accuracy / coverage -----------------------------------------------------


def test_selective_accuracy_improves_as_coverage_drops():
    rng = np.random.default_rng(3)
    correct = rng.random(400) < 0.7
    scores = correct + rng.normal(0, 0.3, size=400)
    at_100 = selective_accuracy(correct, scores, 1.0)
    at_60 = selective_accuracy(correct, scores, 0.6)
    assert at_60 > at_100
    assert at_100 == pytest.approx(correct.mean())


def test_coverage_at_risk_finds_largest_feasible_coverage():
    correct = np.array([True] * 90 + [False] * 10)
    scores = np.linspace(1.0, 0.0, 100)
    # 10 ca sai nằm cuối => giữ 90 ca đầu thì sai số 0.
    assert coverage_at_risk(correct, scores, 0.0) == pytest.approx(0.90)
    assert coverage_at_risk(correct, scores, 0.05) > 0.90


def test_coverage_at_risk_returns_zero_when_impossible():
    """Ca chắc nhất cũng sai thì không có coverage nào đạt sai số 0."""
    correct = np.array([False, True, True])
    scores = np.array([1.0, 0.5, 0.2])
    assert coverage_at_risk(correct, scores, 0.0) == 0.0


def test_selective_accuracy_rejects_bad_coverage():
    correct = np.array([True, False])
    for bad in (0.0, -0.1, 1.5):
        with pytest.raises(ValueError, match="coverage"):
            selective_accuracy(correct, np.array([1.0, 0.0]), bad)


# --- metric bất kỳ ở một mức coverage ---------------------------------------


def test_macro_f1_at_coverage_is_the_headline_number():
    """Con số trung tâm của dự án: macro-F1 ở coverage 80% phải cao hơn ở 100%."""
    rng = np.random.default_rng(4)
    n, k = 400, 7
    y_true = rng.integers(0, k, size=n)
    y_pred = y_true.copy()
    wrong = rng.random(n) < 0.3
    y_pred[wrong] = (y_true[wrong] + rng.integers(1, k, size=wrong.sum())) % k
    scores = (~wrong) + rng.normal(0, 0.25, size=n)

    full = metric_at_coverage(y_true, y_pred, scores, 1.0, _macro_f1)
    partial = metric_at_coverage(y_true, y_pred, scores, 0.8, _macro_f1)
    assert full == pytest.approx(_macro_f1(y_true, y_pred))
    assert partial > full


def test_metric_at_coverage_rejects_length_mismatch():
    with pytest.raises(ValueError, match="khác độ dài"):
        metric_at_coverage(np.array([0, 1]), np.array([0]), np.array([1.0, 0.0]), 1.0, _macro_f1)


def test_metric_at_coverage_keeps_most_confident_cases():
    """Ca giữ lại phải đúng là ca có score cao nhất, không phải ca đầu mảng."""
    y_true = np.array([0, 1, 0, 1])
    y_pred = np.array([1, 1, 0, 1])  # ca 0 sai
    scores = np.array([0.1, 0.9, 0.8, 0.7])  # ca sai có score thấp nhất
    assert metric_at_coverage(y_true, y_pred, scores, 0.75, _macro_f1) == pytest.approx(1.0)
