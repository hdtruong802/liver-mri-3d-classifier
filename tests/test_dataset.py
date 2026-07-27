"""Test CachedLesionDataset — cầu nối giữa cache và vòng train.

Kiểm cả điều kiện "sẵn sàng train": dựng được từ split official, shape đúng,
không lẫn bệnh nhân giữa train/val, và không chạm test-104.

**torch chỉ cần cho việc đọc mẫu** (`__getitem__`). Các test chống leakage và test
nối split — thứ quan trọng nhất — cố ý KHÔNG phụ thuộc torch, để chúng luôn chạy
kể cả trên máy chưa cài deep-learning stack.
"""

from pathlib import Path

import numpy as np
import pytest
from src.data.dataset import CachedLesionDataset, build_fold_datasets, build_test_dataset

SHAPE = (8, 6, 6, 4)


def _write_cache(cache_dir: Path, patient_ids: list[str], label: int = 3) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(0)
    for pid in patient_ids:
        np.savez_compressed(
            cache_dir / f"{pid}.npz",
            image=rng.normal(size=SHAPE).astype(np.float16),
            label=np.int64(label),
        )


def test_getitem_returns_tensor_and_label(tmp_path: Path):
    torch = pytest.importorskip("torch", reason="đọc mẫu cần torch")
    cache = tmp_path / "cache"
    _write_cache(cache, ["MR-1", "MR-2"])
    ds = CachedLesionDataset(cache, [("MR-1", 6), ("MR-2", 4)])

    assert len(ds) == 2
    item = ds[0]
    assert item["image"].shape == SHAPE
    assert item["image"].dtype == torch.float32  # cache float16 -> float32 cho train
    assert item["label"] == 6
    assert item["patient_id"] == "MR-1"


def test_matches_patient_id_across_hyphen_forms(tmp_path: Path):
    """Split ghi 'MR207602' còn cache ghi 'MR-207602' vẫn phải khớp."""
    cache = tmp_path / "cache"
    _write_cache(cache, ["MR-207602"])
    ds = CachedLesionDataset(cache, [("MR207602", 0)])
    assert len(ds) == 1


def test_missing_cache_file_raises_actionable_error(tmp_path: Path):
    cache = tmp_path / "cache"
    _write_cache(cache, ["MR-1"])
    with pytest.raises(FileNotFoundError, match="build_cache"):
        CachedLesionDataset(cache, [("MR-1", 0), ("MR-999", 0)])


def test_transform_is_applied(tmp_path: Path):
    pytest.importorskip("torch", reason="đọc mẫu cần torch")
    cache = tmp_path / "cache"
    _write_cache(cache, ["MR-1"])

    def mark(item):
        item["marked"] = True
        return item

    ds = CachedLesionDataset(cache, [("MR-1", 0)], transform=mark)
    assert ds[0]["marked"] is True


# --- Sẵn sàng train: dựng từ split official đã khoá -------------------------


@pytest.fixture
def full_cache(tmp_path: Path):
    """Cache giả cho toàn bộ 498 bệnh nhân trong splits/ thật của repo."""
    from src.data.splits import Splits

    splits = Splits("splits")
    cache = tmp_path / "cache"
    ids = [pid for pid, _ in splits.trainval] + [pid for pid, _ in splits.test]
    _write_cache(cache, ids)
    return cache, splits


def test_build_fold_datasets_from_official_split(full_cache):
    cache, splits = full_cache
    train_ds, val_ds = build_fold_datasets(cache, fold_index=1)

    assert len(train_ds) + len(val_ds) == len(splits.trainval) == 394
    assert len(train_ds) > len(val_ds)


def test_fold_datasets_do_not_share_patients(full_cache):
    """Không được có bệnh nhân vừa ở train vừa ở val (AGENTS.md §3.2)."""
    from src.utils.ids import normalize_pid

    cache, _ = full_cache
    train_ds, val_ds = build_fold_datasets(cache, fold_index=1)
    train_keys = {normalize_pid(p) for _, _, p in train_ds.samples}
    val_keys = {normalize_pid(p) for _, _, p in val_ds.samples}
    assert train_keys.isdisjoint(val_keys)


def test_fold_datasets_never_touch_test_split(full_cache):
    """test-104 là held-out khoá kín — không được lọt vào train/val của bất kỳ fold nào."""
    from src.utils.ids import normalize_pid

    cache, splits = full_cache
    test_keys = splits.test_keys()
    for fold_index in range(1, len(splits.folds) + 1):
        train_ds, val_ds = build_fold_datasets(cache, fold_index)
        used = {normalize_pid(p) for _, _, p in train_ds.samples + val_ds.samples}
        assert used.isdisjoint(test_keys), f"fold {fold_index} chạm test-104"


def test_build_test_dataset_has_104(full_cache):
    cache, _ = full_cache
    assert len(build_test_dataset(cache)) == 104


def test_invalid_fold_index_rejected(full_cache):
    cache, _ = full_cache
    with pytest.raises(ValueError, match="fold_index"):
        build_fold_datasets(cache, fold_index=0)


def test_dataloader_batch_is_train_ready(full_cache):
    """Smoke test cuối: DataLoader ra batch đúng dạng model nhận."""
    torch = pytest.importorskip("torch", reason="DataLoader cần torch")
    from torch.utils.data import DataLoader

    cache, _ = full_cache
    train_ds, _ = build_fold_datasets(cache, fold_index=1)
    batch = next(iter(DataLoader(train_ds, batch_size=4, shuffle=False)))

    assert batch["image"].shape == (4, *SHAPE)
    assert batch["image"].dtype == torch.float32
    assert batch["label"].shape == (4,)
    assert all(0 <= int(v) <= 6 for v in batch["label"])
