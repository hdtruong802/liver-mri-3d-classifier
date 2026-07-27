"""Test metric đánh giá — thuần numpy, luôn chạy được (không cần torch).

Điểm quan trọng nhất được khoá ở đây: **macro-F1 phải phạt việc bỏ quên lớp hiếm**.
Đó là lý do chọn macro thay vì accuracy (Spec Sheet §3); nếu ai đó "tối ưu" hàm này
thành bỏ qua lớp vắng thì metric chính của dự án mất ý nghĩa.
"""

import numpy as np
import pytest
from src.eval.metrics import (
    accuracy,
    balanced_accuracy,
    classification_metrics,
    cohen_kappa,
    confusion_matrix,
    macro_f1,
    per_class_f1,
)


def test_confusion_matrix_counts_rows_as_truth():
    y_true = np.array([0, 0, 1, 6])
    y_pred = np.array([0, 1, 1, 6])
    matrix = confusion_matrix(y_true, y_pred)

    assert matrix.shape == (7, 7)
    assert matrix[0, 0] == 1
    assert matrix[0, 1] == 1  # thật lớp 0, đoán lớp 1
    assert matrix.sum() == 4


def test_mismatched_lengths_rejected():
    with pytest.raises(ValueError, match="khác độ dài"):
        confusion_matrix(np.array([0, 1]), np.array([0]))


def test_perfect_prediction_gives_one():
    y = np.array([0, 1, 2, 3, 4, 5, 6])
    assert macro_f1(y, y) == pytest.approx(1.0)
    assert cohen_kappa(y, y) == pytest.approx(1.0)
    assert balanced_accuracy(y, y) == pytest.approx(1.0)


def test_macro_f1_punishes_ignoring_a_rare_class():
    """Model đoán tất cả về lớp đa số: accuracy còn cao, macro-F1 phải sập."""
    y_true = np.array([6] * 18 + [2] * 2)  # 18 HCC, 2 áp-xe
    y_pred = np.array([6] * 20)

    assert accuracy(y_true, y_pred) == pytest.approx(0.9)
    # 2 lớp có mặt: F1(HCC)≈0.947, F1(áp-xe)=0 -> trung bình qua 7 lớp rất thấp.
    assert macro_f1(y_true, y_pred) < 0.15
    assert per_class_f1(y_true, y_pred)[2] == 0.0


def test_absent_class_scores_zero_not_nan():
    y_true = np.array([0, 0])
    y_pred = np.array([0, 0])
    scores = per_class_f1(y_true, y_pred)

    assert np.isfinite(scores).all()
    assert scores[0] == pytest.approx(1.0)
    assert scores[1:].sum() == 0.0


def test_balanced_accuracy_ignores_absent_classes():
    """Lớp không xuất hiện trong y_true không được kéo balanced accuracy xuống."""
    y_true = np.array([0, 0, 1, 1])
    y_pred = np.array([0, 0, 1, 0])
    assert balanced_accuracy(y_true, y_pred) == pytest.approx(0.75)  # (1.0 + 0.5) / 2


def test_kappa_is_zero_for_chance_level_agreement():
    """Đoán y hệt phân bố nhãn nhưng lệch pha -> đồng thuận bằng mức may rủi."""
    y_true = np.array([0, 0, 1, 1])
    y_pred = np.array([0, 1, 0, 1])
    assert cohen_kappa(y_true, y_pred) == pytest.approx(0.0, abs=1e-9)


def test_classification_metrics_returns_expected_keys():
    y = np.array([0, 1, 2])
    metrics = classification_metrics(y, y)
    assert set(metrics) == {"macro_f1", "balanced_accuracy", "accuracy", "cohen_kappa"}
    assert all(isinstance(v, float) for v in metrics.values())


def test_macro_f1_matches_sklearn_when_all_classes_present():
    """Metric chính phải trùng KHÍT với thứ leaderboard official dùng.

    `main/metrics.py` của LLD-MMRI2023 gọi thẳng
    ``sklearn.metrics.f1_score(y_true, y_pred, average='macro')``. Nếu bản của ta lệch
    dù chỉ chút ít thì mọi so sánh với con số 0.6083 đều vô nghĩa.
    """
    sklearn_metrics = pytest.importorskip("sklearn.metrics")
    rng = np.random.default_rng(0)

    for _ in range(20):
        y_true = np.concatenate([np.arange(7), rng.integers(0, 7, 100)])
        y_pred = rng.integers(0, 7, y_true.size)
        expected = sklearn_metrics.f1_score(y_true, y_pred, average="macro")
        assert macro_f1(y_true, y_pred) == pytest.approx(expected)


def test_macro_f1_differs_from_sklearn_only_when_a_class_is_wholly_absent():
    """Điều kiện tương đương, ghi lại rõ ràng thay vì để người sau tự vấp.

    sklearn lấy trung bình trên các lớp có mặt trong ``y_true ∪ y_pred``; bản của ta
    luôn lấy trung bình trên đủ 7 lớp, tính lớp vắng mặt là F1 = 0. Hai cách chỉ khác
    nhau khi một lớp **không xuất hiện ở cả nhãn thật lẫn dự đoán** — với val fold
    thật (78–82 ca, đủ 7 lớp) thì trường hợp này không xảy ra.
    """
    sklearn_metrics = pytest.importorskip("sklearn.metrics")
    y_true = np.array([0, 0, 1, 1])  # vắng lớp 2..6
    y_pred = np.array([0, 1, 1, 1])

    assert sklearn_metrics.f1_score(y_true, y_pred, average="macro") == pytest.approx(0.7, abs=0.05)
    assert macro_f1(y_true, y_pred) == pytest.approx(
        sklearn_metrics.f1_score(y_true, y_pred, average="macro") * 2 / 7
    )


def test_cohen_kappa_matches_sklearn():
    """official dùng ``sklearn.metrics.cohen_kappa_score`` không tham số."""
    sklearn_metrics = pytest.importorskip("sklearn.metrics")
    rng = np.random.default_rng(1)

    for _ in range(20):
        y_true = np.concatenate([np.arange(7), rng.integers(0, 7, 80)])
        y_pred = rng.integers(0, 7, y_true.size)
        expected = sklearn_metrics.cohen_kappa_score(y_true, y_pred)
        assert cohen_kappa(y_true, y_pred) == pytest.approx(expected)


def test_empty_input_does_not_crash():
    empty = np.zeros(0, dtype=int)
    assert accuracy(empty, empty) == 0.0
    assert cohen_kappa(empty, empty) == 0.0
    assert balanced_accuracy(empty, empty) == 0.0
