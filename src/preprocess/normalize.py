"""Chuẩn hoá cường độ MRI.

MRI **không có đơn vị chuẩn** như HU của CT: cùng một mô cho giá trị khác nhau giữa
các máy, các lần chụp, thậm chí các chuỗi. Nên phải chuẩn hoá theo từng chuỗi.

**Về leakage (AGENTS.md §3.3):** thống kê ở đây lấy từ *chính volume của bệnh nhân đó*
(per-sample), không gộp qua nhiều bệnh nhân, nên **không** tạo rò rỉ giữa train và
test. Đây là điểm khác với việc chuẩn hoá bằng mean/std toàn tập — thứ đó bắt buộc
phải tính trên train.
"""

from __future__ import annotations

import numpy as np


def clip_and_zscore(
    volume: np.ndarray,
    stats_source: np.ndarray | None = None,
    clip_percentile: tuple[float, float] = (0.5, 99.5),
) -> np.ndarray:
    """Cắt ngưỡng theo phân vị rồi z-score.

    Args:
        volume: khối cần chuẩn hoá (thường là patch đã cắt).
        stats_source: khối dùng để tính phân vị/mean/std. Mặc định là chính `volume`.
            Truyền volume gốc (trước khi cắt) để giữ tương phản tổn thương-so-với-gan;
            nếu chỉ dùng patch, patch nào cũng bị kéo về mean 0 và mất thông tin
            "tổn thương sáng hơn nhu mô quanh nó".
        clip_percentile: cặp phân vị dưới/trên, chống nhiễu ngoại lai.

    Trả về mảng float32, mean≈0 std≈1 (theo `stats_source`).
    """
    source = volume if stats_source is None else stats_source
    lo, hi = np.percentile(source, clip_percentile)
    if not np.isfinite([lo, hi]).all() or hi <= lo:
        # Volume phẳng (toàn 0) — trả về 0 thay vì sinh NaN.
        return np.zeros_like(volume, dtype=np.float32)

    clipped_source = np.clip(source, lo, hi)
    mean = float(clipped_source.mean())
    std = float(clipped_source.std())
    if std <= 0:
        return np.zeros_like(volume, dtype=np.float32)

    return ((np.clip(volume, lo, hi) - mean) / std).astype(np.float32)
