"""Khoảng tin cậy bootstrap ở **mức bệnh nhân** (AGENTS.md §3.5).

Vì sao mọi con số của dự án phải kèm CI, nói bằng dữ liệu của chính dự án: ở fold 1,
macro-F1 val dao động 0.115–0.265 qua các epoch mà không có xu hướng (WORKLOG S-042).
Hai cấu hình khác nhau cho ra 0.2725 và 0.2647 — nhìn thì khác nhau, nhưng trên 82
bệnh nhân thì **không phân biệt được với nhiễu**. Một điểm ước lượng trần trụi ở quy
mô này gần như không mang thông tin.

Đơn vị lấy mẫu lại là **bệnh nhân**, không phải ROI hay lát cắt: đó là đơn vị độc lập
duy nhất trong dữ liệu này (AGENTS.md §3.2). Lấy mẫu ở mức nhỏ hơn sẽ cho CI hẹp giả
tạo vì các mẫu trong cùng một bệnh nhân tương quan với nhau.

Mặc định dùng **stratified** bootstrap: lấy mẫu lại trong từng lớp, giữ nguyên số ca
mỗi lớp. Với 7 lớp rất lệch nhau, bootstrap thường có thể sinh ra mẫu lặp không chứa
lớp hiếm nào — khi đó macro-F1 tính trên số lớp khác đi và phân phối bị méo.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np

from src.data.taxonomy import NUM_CLASSES

N_RESAMPLES = 2000  # sàn theo AGENTS.md §3.5
DEFAULT_SEED = 20260727


def stratified_indices(labels: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Một lần lấy mẫu lại có hoàn lại, **giữ nguyên số ca của từng lớp**."""
    picked: list[np.ndarray] = []
    for value in np.unique(labels):
        pool = np.flatnonzero(labels == value)
        picked.append(rng.choice(pool, size=pool.size, replace=True))
    return np.concatenate(picked)


def bootstrap_metric(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    metric: Callable[[np.ndarray, np.ndarray], float],
    n_resamples: int = N_RESAMPLES,
    confidence: float = 0.95,
    stratified: bool = True,
    seed: int = DEFAULT_SEED,
) -> dict[str, float]:
    """Ước lượng điểm + CI bootstrap percentile cho một metric bất kỳ.

    `metric` là hàm thuần ``(y_true, y_pred) -> float`` — dùng thẳng được các hàm
    trong `src.eval.metrics`.

    Trả về ``{"point", "ci_low", "ci_high", "n_resamples", "n_patients"}``. `point` là
    metric trên dữ liệu gốc, **không phải trung bình của bootstrap** (trung bình
    bootstrap là ước lượng lệch của chính nó).
    """
    y_true = np.asarray(y_true).ravel()
    y_pred = np.asarray(y_pred).ravel()
    if y_true.shape != y_pred.shape:
        raise ValueError(f"y_true {y_true.shape} và y_pred {y_pred.shape} khác độ dài")
    if n_resamples < N_RESAMPLES:
        raise ValueError(f"n_resamples phải ≥ {N_RESAMPLES} (AGENTS.md §3.5), nhận {n_resamples}")

    rng = np.random.default_rng(seed)
    scores = np.empty(n_resamples, dtype=float)
    for i in range(n_resamples):
        idx = (
            stratified_indices(y_true, rng)
            if stratified
            else rng.integers(0, y_true.size, y_true.size)
        )
        scores[i] = metric(y_true[idx], y_pred[idx])

    alpha = (1.0 - confidence) / 2.0
    return {
        "point": float(metric(y_true, y_pred)),
        "ci_low": float(np.quantile(scores, alpha)),
        "ci_high": float(np.quantile(scores, 1.0 - alpha)),
        "n_resamples": float(n_resamples),
        "n_patients": float(y_true.size),
    }


def bootstrap_all(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    metrics: dict[str, Callable[[np.ndarray, np.ndarray], float]],
    **kwargs: object,
) -> dict[str, dict[str, float]]:
    """Chạy `bootstrap_metric` cho nhiều metric, dùng chung một seed."""
    return {name: bootstrap_metric(y_true, y_pred, fn, **kwargs) for name, fn in metrics.items()}  # type: ignore[arg-type]


def format_ci(result: dict[str, float], digits: int = 4) -> str:
    """Một dòng ``0.2647 [0.1804, 0.3512]`` để in ra bảng/báo cáo."""
    return (
        f"{result['point']:.{digits}f} "
        f"[{result['ci_low']:.{digits}f}, {result['ci_high']:.{digits}f}]"
    )


def default_metrics() -> dict[str, Callable[[np.ndarray, np.ndarray], float]]:
    """Bộ metric mặc định cho bảng CV của W3."""
    from src.eval.metrics import accuracy, balanced_accuracy, cohen_kappa, macro_f1

    return {
        "macro_f1": lambda t, p: macro_f1(t, p, NUM_CLASSES),
        "cohen_kappa": lambda t, p: cohen_kappa(t, p, NUM_CLASSES),
        "balanced_accuracy": lambda t, p: balanced_accuracy(t, p, NUM_CLASSES),
        "accuracy": accuracy,
    }
