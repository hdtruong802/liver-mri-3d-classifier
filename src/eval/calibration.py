"""Calibration: xác suất model đưa ra có khớp tần suất đúng thực tế không.

Đây là một nửa đóng góp headline của dự án (nửa kia ở `src/eval/selective.py`).

## Vấn đề

Softmax cho ra các số cộng lại bằng 1 nên **trông** như xác suất, nhưng không có
gì trong quá trình train ép chúng khớp thực tế. Cross-entropy luôn thưởng cho việc
đẩy xác suất của lớp đúng về 1, và với model đủ lớn nó tiếp tục đẩy cả sau khi
accuracy đã ngừng cải thiện. Kết quả: mạng deep hiện đại **tự tin quá mức một cách
hệ thống**.

## "Đã hiệu chỉnh" nghĩa là gì

Gom tất cả ca model nói 0,80 thì trong nhóm đó phải đúng khoảng 80%. Lưu ý đây là
tính chất của **một nhóm dự đoán**, không phải của một ca: với một ca đơn lẻ chỉ có
đúng hoặc sai, không kiểm được.

## Vì sao quan trọng với dự án này

Ngưỡng `defer` được đặt trên chính các xác suất này. Xác suất chưa hiệu chỉnh thì
ngưỡng vô nghĩa — model sẽ im lặng bỏ qua đúng những ca lẽ ra phải cảnh báo, vì nó
tưởng mình đang chắc 0,95.

## Quy ước

Mọi hàm nhận `probs` dạng ``(N, K)`` đã chuẩn hoá theo hàng và `labels` dạng
``(N,)`` số nguyên. Không hàm nào tự fit gì trên dữ liệu được truyền vào, trừ
`fit_temperature` — và hàm đó **chỉ được gọi trên validation** (AGENTS.md §3.3).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

__all__ = [
    "ReliabilityCurve",
    "adaptive_calibration_error",
    "apply_temperature",
    "brier_score",
    "expected_calibration_error",
    "fit_temperature",
    "fit_temperature_min_ece",
    "maximum_calibration_error",
    "negative_log_likelihood",
    "per_class_calibration_error",
    "reliability_curve",
]

_EPS = 1e-12


def _check(probs: np.ndarray, labels: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    probs = np.asarray(probs, dtype=np.float64)
    labels = np.asarray(labels).ravel().astype(int)
    if probs.ndim != 2:
        raise ValueError(f"probs phải có dạng (N, K), nhận {probs.shape}")
    if probs.shape[0] != labels.shape[0]:
        raise ValueError(f"probs có {probs.shape[0]} hàng nhưng labels có {labels.shape[0]}")
    if probs.shape[0] == 0:
        raise ValueError("probs rỗng")
    row_sums = probs.sum(axis=1)
    if not np.allclose(row_sums, 1.0, atol=1e-3):
        raise ValueError(
            "probs phải chuẩn hoá theo hàng (mỗi hàng cộng lại bằng 1). "
            f"min={row_sums.min():.4f} max={row_sums.max():.4f}"
        )
    if labels.min() < 0 or labels.max() >= probs.shape[1]:
        raise ValueError(f"labels ngoài khoảng [0, {probs.shape[1] - 1}]")
    return probs, labels


@dataclass(frozen=True)
class ReliabilityCurve:
    """Dữ liệu để vẽ reliability diagram. Đường hoàn hảo là đường chéo.

    Bin nào nằm **dưới** đường chéo (`accuracy < confidence`) là bin model đang
    tự tin quá mức.
    """

    bin_lower: np.ndarray
    bin_upper: np.ndarray
    confidence: np.ndarray
    accuracy: np.ndarray
    count: np.ndarray

    @property
    def gap(self) -> np.ndarray:
        """`confidence - accuracy`. Dương = tự tin quá mức."""
        return self.confidence - self.accuracy


def _bin_edges_equal_width(n_bins: int) -> np.ndarray:
    return np.linspace(0.0, 1.0, n_bins + 1)


def _bin_edges_equal_mass(confidence: np.ndarray, n_bins: int) -> np.ndarray:
    """Biên bin sao cho **số mẫu** mỗi bin xấp xỉ bằng nhau.

    Ổn định hơn bin đều bề rộng khi độ tự tin dồn cục ở gần 1 — chuyện luôn xảy
    ra với model tự tin quá mức, tức đúng trường hợp ta cần đo.
    """
    quantiles = np.linspace(0.0, 1.0, n_bins + 1)
    edges = np.quantile(confidence, quantiles)
    edges[0], edges[-1] = 0.0, 1.0
    return np.unique(edges)


def reliability_curve(
    probs: np.ndarray, labels: np.ndarray, n_bins: int = 15, adaptive: bool = False
) -> ReliabilityCurve:
    """Chia dự đoán theo độ tự tin thành bin, so độ tự tin với accuracy thật."""
    probs, labels = _check(probs, labels)
    if n_bins < 1:
        raise ValueError(f"n_bins phải ≥ 1, nhận {n_bins}")

    confidence = probs.max(axis=1)
    correct = (probs.argmax(axis=1) == labels).astype(np.float64)
    if adaptive:
        edges = _bin_edges_equal_mass(confidence, n_bins)
    else:
        edges = _bin_edges_equal_width(n_bins)

    lowers, uppers, confs, accs, counts = [], [], [], [], []
    for lo, hi in zip(edges[:-1], edges[1:], strict=True):
        # Bin cuối lấy cả biên phải để không bỏ sót các ca có confidence đúng 1.0.
        in_bin = (confidence > lo) & (confidence <= hi) if lo > 0 else (confidence <= hi)
        n = int(in_bin.sum())
        lowers.append(lo)
        uppers.append(hi)
        counts.append(n)
        confs.append(float(confidence[in_bin].mean()) if n else 0.0)
        accs.append(float(correct[in_bin].mean()) if n else 0.0)

    return ReliabilityCurve(
        bin_lower=np.array(lowers),
        bin_upper=np.array(uppers),
        confidence=np.array(confs),
        accuracy=np.array(accs),
        count=np.array(counts),
    )


def expected_calibration_error(
    probs: np.ndarray, labels: np.ndarray, n_bins: int = 15, adaptive: bool = False
) -> float:
    """ECE: trung bình có trọng số của ``|độ tự tin − accuracy|`` trên các bin.

    Càng thấp càng tốt; 0 nghĩa là hiệu chỉnh hoàn hảo ở độ phân giải bin đã chọn.
    ECE **không** đo độ chính xác: một model đoán mò nhưng luôn báo đúng mức tự tin
    thấp vẫn có ECE tốt. Luôn đọc kèm macro-F1.
    """
    curve = reliability_curve(probs, labels, n_bins, adaptive)
    total = curve.count.sum()
    if total == 0:
        return 0.0
    return float(np.sum(curve.count / total * np.abs(curve.gap)))


def adaptive_calibration_error(probs: np.ndarray, labels: np.ndarray, n_bins: int = 15) -> float:
    """ECE với bin chia đều **số mẫu**. Ổn định hơn khi độ tự tin dồn cục."""
    return expected_calibration_error(probs, labels, n_bins, adaptive=True)


def maximum_calibration_error(
    probs: np.ndarray, labels: np.ndarray, n_bins: int = 15, adaptive: bool = False
) -> float:
    """MCE: khoảng cách **tệ nhất** ở một bin — đo trường hợp xấu nhất.

    Bin rỗng bị bỏ qua: không có mẫu thì không có bằng chứng về sai lệch.
    """
    curve = reliability_curve(probs, labels, n_bins, adaptive)
    nonempty = curve.count > 0
    if not nonempty.any():
        return 0.0
    return float(np.abs(curve.gap[nonempty]).max())


def brier_score(probs: np.ndarray, labels: np.ndarray) -> float:
    """Brier đa lớp: trung bình của ``Σ_k (p_k − y_k)²`` trên các mẫu.

    Càng thấp càng tốt. Gộp cả độ chính xác lẫn độ hiệu chỉnh vào một số, nên
    không thay thế được ECE — hai model cùng Brier có thể khác hẳn nhau về
    calibration.

    Dùng dạng **tổng bình phương** (không chia cho K), khoảng giá trị ``[0, 2]``.
    Có tài liệu chia thêm cho K; ghi rõ ở đây để không so nhầm với số của họ.
    """
    probs, labels = _check(probs, labels)
    onehot = np.zeros_like(probs)
    onehot[np.arange(len(labels)), labels] = 1.0
    return float(np.mean(np.sum((probs - onehot) ** 2, axis=1)))


def negative_log_likelihood(probs: np.ndarray, labels: np.ndarray) -> float:
    """NLL: ``−mean(log p_đúng)``. Phạt rất nặng khi model **tự tin nhưng sai**.

    Đây là hàm mục tiêu mà `fit_temperature` tối thiểu hoá.
    """
    probs, labels = _check(probs, labels)
    p_true = probs[np.arange(len(labels)), labels]
    return float(-np.mean(np.log(np.clip(p_true, _EPS, 1.0))))


def apply_temperature(probs: np.ndarray, temperature: float) -> np.ndarray:
    """Chia logit cho `temperature` rồi softmax lại.

    Nhận **xác suất** chứ không phải logit, vì pipeline chỉ lưu `val_probs_*.npz`.
    Hợp lệ về mặt toán học: ``softmax(log(p) / T)`` cho đúng kết quả như chia
    logit gốc, do softmax bất biến với việc cộng thêm hằng số vào logit.

    `T > 1` làm phân bố mềm đi (chữa tự tin quá mức), `T < 1` làm nhọn thêm.
    **Không đổi thứ hạng các lớp**, nên macro-F1, accuracy và AUROC giữ nguyên —
    calibration là thứ nhận được mà không phải đánh đổi độ chính xác.
    """
    if temperature <= 0:
        raise ValueError(f"temperature phải dương, nhận {temperature}")
    probs = np.asarray(probs, dtype=np.float64)
    scaled = np.log(np.clip(probs, _EPS, 1.0)) / float(temperature)
    scaled -= scaled.max(axis=1, keepdims=True)  # ổn định số học
    exp = np.exp(scaled)
    return exp / exp.sum(axis=1, keepdims=True)


def fit_temperature(
    probs: np.ndarray,
    labels: np.ndarray,
    bounds: tuple[float, float] = (0.05, 10.0),
    tolerance: float = 1e-4,
) -> float:
    """Học `T` tối thiểu hoá NLL bằng tìm kiếm mặt cắt vàng.

    ⚠️ **Chỉ gọi trên tập validation.** Fit `T` trên test là data leakage và làm
    hỏng tính hợp lệ của toàn bộ đánh giá (AGENTS.md §3.3).

    Dùng tìm kiếm mặt cắt vàng thay vì scipy: NLL theo `T` là hàm một biến, trơn
    và lồi một cực tiểu trên khoảng này, nên 60 dòng phụ thuộc là không cần thiết.
    """
    probs, labels = _check(probs, labels)
    lo, hi = bounds
    if lo <= 0 or hi <= lo:
        raise ValueError(f"bounds không hợp lệ: {bounds}")

    def nll(t: float) -> float:
        return negative_log_likelihood(apply_temperature(probs, t), labels)

    inv_phi = (np.sqrt(5.0) - 1.0) / 2.0
    a, b = lo, hi
    c, d = b - inv_phi * (b - a), a + inv_phi * (b - a)
    fc, fd = nll(c), nll(d)
    while abs(b - a) > tolerance:
        if fc < fd:
            b, d, fd = d, c, fc
            c = b - inv_phi * (b - a)
            fc = nll(c)
        else:
            a, c, fc = c, d, fd
            d = a + inv_phi * (b - a)
            fd = nll(d)
    return float((a + b) / 2.0)


def fit_temperature_min_ece(
    probs: np.ndarray,
    labels: np.ndarray,
    bounds: tuple[float, float] = (0.5, 8.0),
    n_points: int = 151,
) -> float:
    """Học `T` tối thiểu hoá **ECE** thay vì NLL, bằng quét lưới.

    Vì sao cần hàm này bên cạnh `fit_temperature`: hai mục tiêu **không** cùng cực
    tiểu. Trên out-of-fold của E4, NLL nhỏ nhất ở `T≈3.3` còn ECE nhỏ nhất ở
    `T≈2.1`; lấy `T` của NLL thì độ tự tin trung bình tụt xuống 0.61 trong khi
    accuracy là 0.70, tức là model chuyển từ tự tin quá mức sang **thiếu** tự tin,
    và ECE dừng ở 0.18 thay vì 0.139 (WORKLOG S-079).

    Quét lưới chứ không dùng mặt cắt vàng như `fit_temperature`: ECE tính trên bin
    nên là hàm bậc thang, không trơn và không lồi — thuật toán giả định tính trơn
    sẽ dừng ở chỗ vô nghĩa.

    ⚠️ Đánh đổi: ECE là hàm mục tiêu **đã rời rạc hoá**, nên fit trực tiếp lên nó
    dễ bám vào cách chia bin cụ thể hơn là NLL (một proper scoring rule). Dùng khi
    thứ cần tối ưu đúng là chất lượng hiệu chỉnh; giữ `fit_temperature` làm mặc
    định cho báo cáo theo chuẩn văn liệu (Guo và cs. 2017).

    ⚠️ Cùng ràng buộc như `fit_temperature`: **chỉ gọi trên validation**.
    """
    probs, labels = _check(probs, labels)
    lo, hi = bounds
    if lo <= 0 or hi <= lo:
        raise ValueError(f"bounds không hợp lệ: {bounds}")
    if n_points < 2:
        raise ValueError(f"n_points phải ≥ 2, nhận {n_points}")

    grid = np.linspace(lo, hi, n_points)
    scores = [adaptive_calibration_error(apply_temperature(probs, float(t)), labels) for t in grid]
    return float(grid[int(np.argmin(scores))])


def per_class_calibration_error(
    probs: np.ndarray, labels: np.ndarray, n_bins: int = 10, adaptive: bool = True
) -> dict[int, float]:
    """ECE tính riêng cho từng lớp, theo kiểu một-đấu-phần-còn-lại.

    Bắt buộc với dự án này: LLD-MMRI mất cân bằng (HCC 157 ca, FNH 46), và model
    thường hiệu chỉnh tốt ở lớp nhiều dữ liệu, tệ ở lớp hiếm — đúng những lớp mà
    sai lầm tốn kém nhất. Một ECE tổng đẹp có thể đang che một lớp hiếm hỏng nặng.

    Lớp không có mẫu nào trong `labels` sẽ bị bỏ khỏi kết quả, không trả về 0 —
    0 sẽ bị đọc nhầm thành "hiệu chỉnh hoàn hảo".
    """
    probs, labels = _check(probs, labels)
    out: dict[int, float] = {}
    for k in range(probs.shape[1]):
        if not (labels == k).any():
            continue
        binary = np.column_stack([1.0 - probs[:, k], probs[:, k]])
        out[k] = expected_calibration_error(binary, (labels == k).astype(int), n_bins, adaptive)
    return out
