"""Metric phân loại đa lớp — hàm **thuần**: nhãn vào, số ra.

Tách khỏi vòng train có chủ đích (AGENTS.md §8): mọi hàm ở đây chạy lại được trên
file dự đoán đã lưu của một checkpoint cũ, không cần dựng lại model hay GPU.

Chỉ dùng numpy để bộ metric không kéo theo deep-learning stack — W3 sẽ bọc thêm
bootstrap CI mức bệnh nhân quanh chính những hàm này (`src/eval/bootstrap.py`).
"""

from __future__ import annotations

import numpy as np

from src.data.taxonomy import NUM_CLASSES


def confusion_matrix(
    y_true: np.ndarray, y_pred: np.ndarray, num_classes: int = NUM_CLASSES
) -> np.ndarray:
    """Ma trận nhầm lẫn ``[num_classes, num_classes]``, hàng = thật, cột = đoán."""
    true = np.asarray(y_true, dtype=int).ravel()
    pred = np.asarray(y_pred, dtype=int).ravel()
    if true.shape != pred.shape:
        raise ValueError(f"y_true {true.shape} và y_pred {pred.shape} khác độ dài")
    matrix = np.zeros((num_classes, num_classes), dtype=np.int64)
    np.add.at(matrix, (true, pred), 1)
    return matrix


def per_class_f1(
    y_true: np.ndarray, y_pred: np.ndarray, num_classes: int = NUM_CLASSES
) -> np.ndarray:
    """F1 của từng lớp; lớp không có mẫu thật và không được đoán → F1 = 0.

    Quy ước 0 (thay vì NaN) để macro-F1 vẫn phạt việc bỏ quên lớp hiếm — áp-xe và
    FNH chỉ vài chục ca, một model "khôn lỏi" bỏ hẳn chúng phải bị trừ điểm.
    """
    matrix = confusion_matrix(y_true, y_pred, num_classes)
    tp = np.diag(matrix).astype(float)
    support = matrix.sum(axis=1).astype(float)  # số ca thật của lớp
    predicted = matrix.sum(axis=0).astype(float)  # số ca được đoán vào lớp
    denominator = support + predicted
    return np.divide(2.0 * tp, denominator, out=np.zeros_like(tp), where=denominator > 0)


def macro_f1(y_true: np.ndarray, y_pred: np.ndarray, num_classes: int = NUM_CLASSES) -> float:
    """Trung bình F1 **không trọng số** qua 7 lớp — metric chính của dự án.

    Chọn macro (Spec Sheet §3) vì phân bố lớp rất lệch: micro-F1/accuracy sẽ bị HCC
    và di căn chi phối, che mất việc model hỏng ở lớp hiếm.
    """
    return float(per_class_f1(y_true, y_pred, num_classes).mean())


def balanced_accuracy(
    y_true: np.ndarray, y_pred: np.ndarray, num_classes: int = NUM_CLASSES
) -> float:
    """Trung bình recall qua các lớp **có mặt** trong y_true (lớp vắng bị bỏ qua)."""
    matrix = confusion_matrix(y_true, y_pred, num_classes)
    support = matrix.sum(axis=1)
    present = support > 0
    if not present.any():
        return 0.0
    recall = np.diag(matrix)[present] / support[present]
    return float(recall.mean())


def accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Tỉ lệ đoán đúng tổng thể. Báo kèm macro-F1 chứ không thay được nó."""
    true = np.asarray(y_true).ravel()
    if true.size == 0:
        return 0.0
    return float((true == np.asarray(y_pred).ravel()).mean())


def cohen_kappa(y_true: np.ndarray, y_pred: np.ndarray, num_classes: int = NUM_CLASSES) -> float:
    """Cohen's κ — mức đồng thuận đã trừ phần "đúng do may".

    Báo song song macro-F1 vì κ so trực tiếp với mức đồng thuận giữa hai người đọc
    phim, là ngôn ngữ quen thuộc của giới chẩn đoán hình ảnh.
    """
    matrix = confusion_matrix(y_true, y_pred, num_classes).astype(float)
    total = matrix.sum()
    if total == 0:
        return 0.0
    observed = np.diag(matrix).sum() / total
    expected = float((matrix.sum(axis=0) @ matrix.sum(axis=1)) / (total * total))
    if np.isclose(expected, 1.0):
        return 0.0
    return float((observed - expected) / (1.0 - expected))


def classification_metrics(
    y_true: np.ndarray, y_pred: np.ndarray, num_classes: int = NUM_CLASSES
) -> dict[str, float]:
    """Bộ metric tối thiểu để báo số W2. Bộ đầy đủ + CI là việc của W3."""
    return {
        "macro_f1": macro_f1(y_true, y_pred, num_classes),
        "balanced_accuracy": balanced_accuracy(y_true, y_pred, num_classes),
        "accuracy": accuracy(y_true, y_pred),
        "cohen_kappa": cohen_kappa(y_true, y_pred, num_classes),
    }
