"""Nhãn trong cache phải khớp nhãn trong `splits/`.

Đây là lỗi tốn kém nhất mà pipeline có thể mắc **mà không báo gì**: `CachedLesionDataset`
lấy nhãn từ split và bỏ qua nhãn lưu trong `.npz`. Nếu build cache ghi nhầm file của
bệnh nhân khác, train vẫn chạy trơn tru, loss vẫn giảm, metric vẫn ra số — chỉ là toàn
bộ kết quả vô nghĩa và không ai biết cho tới lúc viết báo cáo.
"""

from pathlib import Path

import numpy as np
from src.data.dataset import CachedLesionDataset, find_label_mismatches


def _write(cache: Path, pid: str, label: int) -> None:
    cache.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        cache / f"{pid}.npz",
        image=np.zeros((8, 2, 2, 2), dtype=np.float16),
        label=np.int64(label),
    )


def test_no_mismatch_when_labels_agree(tmp_path: Path):
    cache = tmp_path / "cache"
    _write(cache, "MR-1", 6)
    _write(cache, "MR-2", 4)
    ds = CachedLesionDataset(cache, [("MR-1", 6), ("MR-2", 4)])

    assert find_label_mismatches(ds) == []


def test_detects_a_swapped_label(tmp_path: Path):
    """Cache nói HCC, split nói nang -> phải bắt được, kèm cả hai giá trị."""
    cache = tmp_path / "cache"
    _write(cache, "MR-1", 6)
    ds = CachedLesionDataset(cache, [("MR-1", 4)])

    assert find_label_mismatches(ds) == [("MR-1", 4, 6)]


def test_reports_every_mismatch_not_just_the_first(tmp_path: Path):
    cache = tmp_path / "cache"
    for i in range(5):
        _write(cache, f"MR-{i}", 0)
    ds = CachedLesionDataset(cache, [(f"MR-{i}", 1) for i in range(5)])

    assert len(find_label_mismatches(ds)) == 5


def test_cache_without_label_key_is_skipped_not_crashed(tmp_path: Path):
    """Cache đời cũ có thể không lưu nhãn — không có gì để so thì bỏ qua, đừng nổ."""
    cache = tmp_path / "cache"
    cache.mkdir(parents=True)
    np.savez_compressed(cache / "MR-1.npz", image=np.zeros((8, 2, 2, 2), dtype=np.float16))
    ds = CachedLesionDataset(cache, [("MR-1", 3)])

    assert find_label_mismatches(ds) == []
