"""Test dựng DataLoader — đặc biệt các khoá chỉ hợp lệ khi có worker.

`persistent_workers` và `prefetch_factor` ném lỗi nếu truyền lúc ``num_workers=0``.
Đây là loại lỗi chỉ nổ trên Kaggle (nơi ta đặt workers > 0) hoặc chỉ nổ ở local (nơi
Windows hay phải hạ về 0), nên đáng khoá bằng test.
"""

from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("torch", reason="DataLoader cần torch")

from src.train.run import build_loaders  # noqa: E402
from src.utils.io import repo_root  # noqa: E402


@pytest.fixture
def cache_dir(tmp_path: Path) -> Path:
    """Cache giả cho toàn bộ 394 bệnh nhân trainval."""
    from src.data.splits import Splits

    cache = tmp_path / "cache"
    cache.mkdir()
    for pid, label in Splits(repo_root() / "splits").trainval:
        np.savez_compressed(
            cache / f"{pid}.npz",
            image=np.zeros((8, 4, 4, 2), dtype=np.float16),
            label=np.int64(label),
        )
    return cache


def _config(cache: Path, **data_overrides) -> dict:
    return {
        "cache_dir": str(cache),
        "splits_dir": str(repo_root() / "splits"),
        "data": {"batch_size": 2, "num_workers": 0, **data_overrides},
    }


def test_builds_loaders_without_workers(cache_dir: Path):
    """num_workers=0: KHÔNG được truyền persistent_workers/prefetch_factor."""
    train_loader, val_loader, labels = build_loaders(_config(cache_dir), fold=1)

    assert len(train_loader.dataset) + len(val_loader.dataset) == 394
    assert len(labels) == len(train_loader.dataset)
    assert train_loader.num_workers == 0


def test_worker_options_applied_when_workers_requested(cache_dir: Path):
    config = _config(cache_dir, num_workers=2, persistent_workers=True, prefetch_factor=4)
    train_loader, _, _ = build_loaders(config, fold=1)

    assert train_loader.num_workers == 2
    assert train_loader.persistent_workers is True
    assert train_loader.prefetch_factor == 4


def test_worker_options_default_on_when_workers_present(cache_dir: Path):
    """300 epoch × dựng lại worker mỗi epoch là lãng phí thật (WORKLOG S-044)."""
    train_loader, _, _ = build_loaders(_config(cache_dir, num_workers=2), fold=1)
    assert train_loader.persistent_workers is True


def test_train_loader_shuffles_and_val_does_not(cache_dir: Path):
    from torch.utils.data import RandomSampler, SequentialSampler

    train_loader, val_loader, _ = build_loaders(_config(cache_dir), fold=1)

    assert isinstance(train_loader.sampler, RandomSampler)
    assert isinstance(val_loader.sampler, SequentialSampler)


def test_augmentation_applied_to_train_only(cache_dir: Path):
    """Val không bao giờ được augment — nếu không thì metric đo trên dữ liệu méo."""
    config = _config(cache_dir)
    config["data"]["augment"] = {"flip_prob": 0.5, "flip_axes": ["x", "y", "z"]}
    train_loader, val_loader, _ = build_loaders(config, fold=1)

    assert train_loader.dataset.transform is not None
    assert val_loader.dataset.transform is None


def test_labels_come_from_train_split_only(cache_dir: Path):
    """Nhãn trả về dùng để tính class weight — lẫn val vào là leakage (AGENTS.md §3.3)."""
    train_loader, val_loader, labels = build_loaders(_config(cache_dir), fold=1)

    assert len(labels) == len(train_loader.dataset)
    assert len(labels) != len(val_loader.dataset)
