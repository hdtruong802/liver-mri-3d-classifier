"""Selective prediction: cho model quyền **từ chối** ca không chắc.

Nửa còn lại của đóng góp headline (nửa kia ở `src/eval/calibration.py`).

## Câu hỏi vận hành

Bảng xếp hạng trả lời "model gọi nhãn đúng bao nhiêu phần trăm". Câu mà bác sĩ và
người triển khai thực sự hỏi là khác: *model tự quyết được bao nhiêu phần ca mà
vẫn giữ sai số dưới mức chấp nhận được, và phần còn lại chuyển ai?*

Từ chối là **kết quả hợp lệ**, không phải thất bại cần giấu (PRODUCT.md §Product
Principles).

## Vì sao chỗ này quan trọng với mục tiêu của dự án

Bề rộng CI của macro-F1 ở n=104 là ±0,077 (WORKLOG S-057), nên **không thể chứng
minh vượt 0,8322 trên test-104** dù model có tốt thật. Chỗ còn lại để có một con số
mạnh mà bảo vệ được là *metric ở một mức coverage*: "macro-F1 0,82 ở coverage 100%,
0,91 ở coverage 80%". Đó là phát biểu trung thực, và là thứ không đội nào trên
leaderboard trả lời.

Mức tăng khi giảm coverage phụ thuộc **hoàn toàn** vào chất lượng điểm tin cậy dùng
để xếp hạng. Xếp hạng đúng thì điểm nhảy mạnh; xếp hạng kém thì bỏ 20% ca gần như
ngẫu nhiên và điểm gần như không đổi. Vì vậy calibration không phải phần trang trí
thêm vào sau — nó quyết định con số này.

## Quy ước

`scores` là **điểm tin cậy**: cao = chắc chắn hơn = giữ lại trước. Với điểm bất
định (entropy, mutual information) phải đổi dấu trước khi truyền vào.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

__all__ = [
    "RiskCoverage",
    "aurc",
    "coverage_at_risk",
    "metric_at_coverage",
    "predictive_entropy",
    "risk_coverage_curve",
    "selective_accuracy",
    "uncertainty_decomposition",
]

_EPS = 1e-12


def predictive_entropy(probs: np.ndarray, normalise: bool = True) -> np.ndarray:
    """Entropy Shannon của từng dự đoán — bất định **toàn phần**.

    `normalise=True` chia cho ``log(K)`` để đưa về thang ``[0, 1]``, giúp so được
    giữa các bài toán khác số lớp. 0 = dồn hết vào một lớp, 1 = đoán mò đều.
    """
    probs = np.asarray(probs, dtype=np.float64)
    if probs.ndim != 2:
        raise ValueError(f"probs phải có dạng (N, K), nhận {probs.shape}")
    entropy = -np.sum(probs * np.log(np.clip(probs, _EPS, 1.0)), axis=1)
    return entropy / np.log(probs.shape[1]) if normalise else entropy


def uncertainty_decomposition(
    member_probs: np.ndarray, normalise: bool = True
) -> dict[str, np.ndarray]:
    """Tách bất định toàn phần thành **aleatoric** và **epistemic**.

    `member_probs` dạng ``(K_models, N, C)`` — dự đoán của từng thành viên ensemble
    (hoặc từng lượt MC-dropout) trên cùng một tập ca.

    ::

        tổng      = H( trung bình các dự đoán )
        aleatoric = trung bình của ( entropy từng thành viên )
        epistemic = tổng − aleatoric          (chính là mutual information)

    Ý nghĩa của việc tách:

    - **Aleatoric cao** — ảnh mơ hồ thật, mọi thành viên đều lưỡng lự như nhau.
      Thêm dữ liệu huấn luyện không cứu được ca này.
    - **Epistemic cao** — các thành viên **bất đồng**. Dấu hiệu ca nằm ngoài miền
      huấn luyện (OOD), thứ sẽ nổi lên khi đổi máy chụp hoặc đổi bệnh viện.

    Hai ca có thể có **cùng** bất định toàn phần nhưng cấu tạo ngược nhau, và
    chúng đòi hai cách xử lý khác nhau. Một model đơn lẻ không có epistemic
    uncertainty theo định nghĩa: cần nhiều hơn một ý kiến mới đo được bất đồng.
    """
    member_probs = np.asarray(member_probs, dtype=np.float64)
    if member_probs.ndim != 3:
        raise ValueError(f"member_probs phải có dạng (K, N, C), nhận {member_probs.shape}")
    if member_probs.shape[0] < 2:
        raise ValueError(
            "cần ít nhất 2 thành viên: epistemic uncertainty đo bằng mức bất đồng, "
            "một model đơn lẻ luôn cho 0"
        )

    mean_probs = member_probs.mean(axis=0)
    total = predictive_entropy(mean_probs, normalise)
    aleatoric = np.mean([predictive_entropy(p, normalise) for p in member_probs], axis=0)
    return {
        "total": total,
        "aleatoric": aleatoric,
        # Kẹp về 0: mutual information không âm về lý thuyết, sai số dấu phẩy động
        # có thể tạo ra giá trị âm rất nhỏ và nó sẽ gây khó hiểu khi hiển thị.
        "epistemic": np.maximum(total - aleatoric, 0.0),
    }


@dataclass(frozen=True)
class RiskCoverage:
    """Đường risk–coverage. `risk[i]` là sai số khi chỉ quyết trên `coverage[i]`."""

    coverage: np.ndarray
    risk: np.ndarray

    @property
    def aurc(self) -> float:
        return float(np.trapezoid(self.risk, self.coverage))


def _check_scores(scores: np.ndarray, n: int) -> np.ndarray:
    scores = np.asarray(scores, dtype=np.float64).ravel()
    if scores.shape[0] != n:
        raise ValueError(f"scores có {scores.shape[0]} phần tử nhưng dữ liệu có {n}")
    if not np.isfinite(scores).all():
        raise ValueError("scores chứa NaN hoặc inf")
    return scores


def risk_coverage_curve(correct: np.ndarray, scores: np.ndarray) -> RiskCoverage:
    """Sai số thay đổi ra sao khi model được phép từ chối dần.

    `correct` là mảng bool: dự đoán có đúng không. `scores` là điểm tin cậy, cao =
    giữ lại trước.

    Sắp giảm dần theo `scores` rồi tính sai số tích luỹ. Điểm đầu là coverage nhỏ
    nhất (chỉ giữ ca chắc nhất), điểm cuối là coverage 100%.
    """
    correct = np.asarray(correct).ravel().astype(bool)
    scores = _check_scores(scores, len(correct))
    if len(correct) == 0:
        raise ValueError("mảng rỗng")

    order = np.argsort(-scores, kind="stable")
    errors = (~correct[order]).astype(np.float64)
    n = len(correct)
    kept = np.arange(1, n + 1)
    return RiskCoverage(coverage=kept / n, risk=np.cumsum(errors) / kept)


def aurc(correct: np.ndarray, scores: np.ndarray) -> float:
    """Diện tích dưới đường risk–coverage. **Càng thấp càng tốt.**

    Tóm tắt chất lượng xếp hạng bất định thành một số: điểm tin cậy tốt đẩy ca sai
    xuống cuối, làm sai số tích luỹ ở coverage thấp gần 0.
    """
    return risk_coverage_curve(correct, scores).aurc


def selective_accuracy(correct: np.ndarray, scores: np.ndarray, coverage: float) -> float:
    """Accuracy khi chỉ quyết trên `coverage` phần ca tự tin nhất."""
    if not 0.0 < coverage <= 1.0:
        raise ValueError(f"coverage phải trong (0, 1], nhận {coverage}")
    correct = np.asarray(correct).ravel().astype(bool)
    scores = _check_scores(scores, len(correct))
    keep = max(1, int(round(coverage * len(correct))))
    order = np.argsort(-scores, kind="stable")[:keep]
    return float(correct[order].mean())


def coverage_at_risk(correct: np.ndarray, scores: np.ndarray, max_risk: float) -> float:
    """Tỷ lệ ca model tự quyết được trong khi giữ sai số ≤ `max_risk`.

    Trả về 0.0 nếu ngay cả ca chắc chắn nhất cũng không đạt — nghĩa là ở mức sai
    số đó, model không được phép tự quyết ca nào.
    """
    if not 0.0 <= max_risk <= 1.0:
        raise ValueError(f"max_risk phải trong [0, 1], nhận {max_risk}")
    curve = risk_coverage_curve(correct, scores)
    feasible = curve.risk <= max_risk
    return float(curve.coverage[feasible].max()) if feasible.any() else 0.0


def metric_at_coverage(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    scores: np.ndarray,
    coverage: float,
    metric: Callable[[np.ndarray, np.ndarray], float],
) -> float:
    """Một metric bất kỳ, tính trên `coverage` phần ca tự tin nhất.

    Đây là hàm dùng để báo **macro-F1 ở coverage 80%** — con số trung tâm của dự
    án. Nhận thẳng được các hàm trong `src.eval.metrics`, và ghép được với
    `src.eval.bootstrap.bootstrap_metric` để ra khoảng tin cậy.

    ⚠️ Ở coverage thấp, một lớp hiếm có thể **biến mất hoàn toàn** khỏi tập giữ
    lại. Macro-F1 khi đó tính trên ít lớp hơn, nên **không so trực tiếp được** với
    macro-F1 ở coverage 100%. Luôn báo kèm coverage và số lớp còn lại.
    """
    if not 0.0 < coverage <= 1.0:
        raise ValueError(f"coverage phải trong (0, 1], nhận {coverage}")
    y_true = np.asarray(y_true).ravel()
    y_pred = np.asarray(y_pred).ravel()
    if y_true.shape != y_pred.shape:
        raise ValueError(f"y_true {y_true.shape} và y_pred {y_pred.shape} khác độ dài")
    scores = _check_scores(scores, len(y_true))

    keep = max(1, int(round(coverage * len(y_true))))
    order = np.argsort(-scores, kind="stable")[:keep]
    return float(metric(y_true[order], y_pred[order]))
