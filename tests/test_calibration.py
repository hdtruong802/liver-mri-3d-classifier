"""Test calibration: ECE, Brier, NLL, temperature scaling.

Dựng dữ liệu tổng hợp có **tính chất calibration đã biết trước** rồi kiểm hàm có
phát hiện đúng không. Không dùng dữ liệu thật: dự án chưa có kết quả nào, và một
test phụ thuộc checkpoint sẽ không chạy lại được.
"""

import numpy as np
import pytest
from src.eval.calibration import (
    adaptive_calibration_error,
    apply_temperature,
    brier_score,
    expected_calibration_error,
    fit_temperature,
    maximum_calibration_error,
    negative_log_likelihood,
    per_class_calibration_error,
    reliability_curve,
)


def _calibrated(n: int = 4000, n_classes: int = 7, seed: int = 0):
    """Model hiệu chỉnh hoàn hảo: nhãn được **rút ra từ chính** phân bố dự đoán.

    Đây là định nghĩa của calibrated, nên ECE của tập này phải gần 0 — sai lệch
    còn lại chỉ là nhiễu lấy mẫu hữu hạn.
    """
    rng = np.random.default_rng(seed)
    logits = rng.normal(0.0, 1.5, size=(n, n_classes))
    exp = np.exp(logits - logits.max(axis=1, keepdims=True))
    probs = exp / exp.sum(axis=1, keepdims=True)
    labels = np.array([rng.choice(n_classes, p=p) for p in probs])
    return probs, labels


def _overconfident(n: int = 4000, n_classes: int = 7, seed: int = 0, sharpen: float = 3.0):
    """Lấy dữ liệu calibrated rồi làm nhọn phân bố mà GIỮ NGUYÊN nhãn.

    Mô phỏng đúng dạng hỏng của mạng deep: thứ hạng lớp không đổi (accuracy giữ
    nguyên) nhưng độ tự tin bị thổi lên.
    """
    probs, labels = _calibrated(n, n_classes, seed)
    return apply_temperature(probs, 1.0 / sharpen), labels


# --- kiểm tra đầu vào --------------------------------------------------------


def test_rejects_unnormalised_probs():
    probs = np.array([[0.5, 0.2], [0.3, 0.3]])
    with pytest.raises(ValueError, match="chuẩn hoá"):
        expected_calibration_error(probs, np.array([0, 1]))


def test_rejects_length_mismatch():
    probs = np.array([[0.5, 0.5], [0.5, 0.5]])
    with pytest.raises(ValueError, match="labels"):
        expected_calibration_error(probs, np.array([0]))


def test_rejects_label_out_of_range():
    probs = np.array([[0.5, 0.5]])
    with pytest.raises(ValueError, match="ngoài khoảng"):
        expected_calibration_error(probs, np.array([5]))


# --- ECE / MCE ---------------------------------------------------------------


def test_calibrated_data_has_low_ece():
    probs, labels = _calibrated()
    assert expected_calibration_error(probs, labels) < 0.05


def test_overconfident_data_has_high_ece():
    probs, labels = _overconfident()
    assert expected_calibration_error(probs, labels) > 0.15


def test_overconfidence_shows_as_positive_gap():
    """Tự tin quá mức = độ tự tin lớn hơn accuracy ở các bin đông mẫu."""
    probs, labels = _overconfident()
    curve = reliability_curve(probs, labels, n_bins=10)
    busy = curve.count > 50
    assert (curve.gap[busy] > 0).mean() > 0.7


def test_reliability_curve_bins_cover_every_sample():
    """Không ca nào được rơi ra ngoài mọi bin — kể cả ca có độ tự tin đúng 1,0."""
    probs = np.array([[1.0, 0.0], [0.5, 0.5], [0.75, 0.25]])
    curve = reliability_curve(probs, np.array([0, 1, 0]), n_bins=4)
    assert curve.count.sum() == 3


def test_mce_is_at_least_ece():
    """MCE là chênh lệch tệ nhất nên không thể nhỏ hơn trung bình có trọng số."""
    probs, labels = _overconfident()
    assert maximum_calibration_error(probs, labels) >= expected_calibration_error(probs, labels)


def test_adaptive_ece_handles_clustered_confidence():
    """Độ tự tin dồn cục ở gần 1 làm bin đều bề rộng rỗng gần hết; adaptive thì không."""
    probs, labels = _overconfident(sharpen=6.0)
    curve = reliability_curve(probs, labels, n_bins=15, adaptive=True)
    assert (curve.count > 0).sum() >= 10
    assert adaptive_calibration_error(probs, labels) > 0.0


# --- Brier / NLL -------------------------------------------------------------


def test_brier_and_nll_are_zero_for_perfect_predictions():
    probs = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
    labels = np.array([0, 1, 2])
    assert brier_score(probs, labels) == pytest.approx(0.0, abs=1e-9)
    assert negative_log_likelihood(probs, labels) == pytest.approx(0.0, abs=1e-9)


def test_brier_penalises_confident_mistakes_more():
    confident_wrong = np.array([[0.99, 0.01]])
    hesitant_wrong = np.array([[0.55, 0.45]])
    labels = np.array([1])
    assert brier_score(confident_wrong, labels) > brier_score(hesitant_wrong, labels)


def test_nll_is_finite_for_zero_probability_truth():
    """Xác suất 0 cho lớp đúng phải cho số hữu hạn, không phải inf."""
    assert np.isfinite(negative_log_likelihood(np.array([[1.0, 0.0]]), np.array([1])))


# --- temperature scaling -----------------------------------------------------


def test_temperature_preserves_predicted_class():
    """Điểm mấu chốt: hiệu chỉnh KHÔNG đánh đổi độ chính xác."""
    probs, _ = _overconfident()
    for t in (0.5, 1.5, 3.0):
        assert np.array_equal(apply_temperature(probs, t).argmax(axis=1), probs.argmax(axis=1))


def test_temperature_output_is_a_distribution():
    probs, _ = _overconfident()
    out = apply_temperature(probs, 2.0)
    assert np.allclose(out.sum(axis=1), 1.0)
    assert (out >= 0).all()


def test_temperature_above_one_softens():
    probs = np.array([[0.9, 0.07, 0.03]])
    assert apply_temperature(probs, 3.0).max() < probs.max()
    assert apply_temperature(probs, 0.5).max() > probs.max()


def test_temperature_rejects_non_positive():
    with pytest.raises(ValueError, match="dương"):
        apply_temperature(np.array([[0.5, 0.5]]), 0.0)


def test_fit_temperature_corrects_overconfidence():
    """Dữ liệu bị làm nhọn gấp 3 thì T học được phải ~3 và ECE phải giảm mạnh."""
    probs, labels = _overconfident(sharpen=3.0)
    t = fit_temperature(probs, labels)
    assert t > 1.5, f"T={t:.3f} — không nhận ra model đang tự tin quá mức"

    before = expected_calibration_error(probs, labels)
    after = expected_calibration_error(apply_temperature(probs, t), labels)
    assert after < before / 2, f"ECE {before:.4f} -> {after:.4f}: chưa cải thiện đủ"


def test_fit_temperature_leaves_calibrated_data_alone():
    """Dữ liệu vốn đã hiệu chỉnh thì T phải gần 1 — không được 'sửa' cái không hỏng."""
    probs, labels = _calibrated()
    assert 0.8 < fit_temperature(probs, labels) < 1.25


def test_fit_temperature_minimises_nll():
    probs, labels = _overconfident()
    t = fit_temperature(probs, labels)
    best = negative_log_likelihood(apply_temperature(probs, t), labels)
    for other in (t * 0.6, t * 1.6, 1.0):
        assert best <= negative_log_likelihood(apply_temperature(probs, other), labels) + 1e-6


# --- theo từng lớp -----------------------------------------------------------


def test_per_class_skips_absent_classes():
    """Lớp không có mẫu phải BỊ BỎ, không trả 0 — 0 sẽ bị đọc nhầm là hoàn hảo."""
    probs, labels = _calibrated(n=400, n_classes=7)
    labels = np.where(labels == 6, 5, labels)  # xoá sạch lớp 6
    result = per_class_calibration_error(probs, labels)
    assert 6 not in result
    assert set(result).issubset(set(range(7)))


def test_per_class_detects_one_bad_class():
    """ECE tổng có thể đẹp trong khi một lớp hỏng nặng — đó là lý do hàm này tồn tại."""
    rng = np.random.default_rng(3)
    n, k, bad = 3000, 7, 4
    probs, labels = _calibrated(n, k, seed=3)
    # Với riêng lớp `bad`: thổi xác suất lên cao ở những ca KHÔNG thuộc lớp đó.
    victims = rng.random(n) < 0.30
    probs = probs.copy()
    probs[victims & (labels != bad), bad] += 0.55
    probs = probs / probs.sum(axis=1, keepdims=True)

    per_class = per_class_calibration_error(probs, labels)
    others = [v for c, v in per_class.items() if c != bad]
    assert per_class[bad] > max(others), (
        f"ECE lớp {bad} = {per_class[bad]:.4f} không nổi hơn các lớp còn lại {max(others):.4f}"
    )
