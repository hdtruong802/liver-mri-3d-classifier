"""Đường dẫn tương đối trong config phải neo vào **gốc repo**, không phải CWD.

Bug thật đã gặp (WORKLOG S-035): trên Kaggle, notebook chạy ở `/kaggle/working`
còn code clone vào `/kaggle/working/repo`, nên `splits_dir: splits` trỏ vào chỗ
trống và vòng train chết ngay dòng đọc split đầu tiên.

Mọi test dưới đây **đổi CWD** trước khi gọi — đó chính là điều kiện tái hiện lỗi.
"""

import os
from pathlib import Path

import pytest
from src.utils.io import repo_root, resolve_cache_dir, resolve_output_dir, resolve_repo_path


def test_repo_root_points_at_this_repo():
    root = repo_root()
    assert (root / "AGENTS.md").is_file()
    assert (root / "splits" / "labels_trainval.txt").is_file()


def test_relative_path_resolves_against_repo_not_cwd(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert resolve_repo_path("splits") == repo_root() / "splits"
    assert resolve_repo_path("splits").is_dir()


def test_absolute_path_is_left_alone(tmp_path: Path):
    assert resolve_repo_path(tmp_path) == tmp_path


def test_cache_and_output_dirs_survive_a_foreign_cwd(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("LLDMMRI_CACHE_DIR", raising=False)
    monkeypatch.delenv("LLDMMRI_OUTPUT_DIR", raising=False)
    monkeypatch.chdir(tmp_path)
    config = {"cache_dir": "artifacts/cache", "output_dir": "artifacts/runs/x"}

    assert resolve_cache_dir(config) == repo_root() / "artifacts" / "cache"
    assert resolve_output_dir(config) == repo_root() / "artifacts" / "runs" / "x"


def test_env_override_still_wins(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("LLDMMRI_CACHE_DIR", str(tmp_path / "mounted"))
    monkeypatch.setenv("LLDMMRI_OUTPUT_DIR", str(tmp_path / "out"))
    monkeypatch.chdir(tmp_path)

    assert resolve_cache_dir({"cache_dir": "artifacts/cache"}) == tmp_path / "mounted"
    assert resolve_output_dir({"output_dir": "artifacts/runs/x"}) == tmp_path / "out"


def test_build_fold_datasets_works_from_a_foreign_cwd(tmp_path: Path, monkeypatch):
    """Đúng kịch bản Kaggle: CWD không phải repo, splits_dir để mặc định."""
    pytest.importorskip("numpy")
    import numpy as np
    from src.data.dataset import build_fold_datasets
    from src.data.splits import Splits

    cache = tmp_path / "cache"
    cache.mkdir()
    splits = Splits(repo_root() / "splits")
    for pid, _ in splits.trainval:
        np.savez_compressed(
            cache / f"{pid}.npz",
            image=np.zeros((8, 2, 2, 2), dtype=np.float16),
            label=np.int64(0),
        )

    monkeypatch.chdir(tmp_path)
    assert Path(os.getcwd()) != repo_root()

    train_ds, val_ds = build_fold_datasets(cache, fold_index=1)
    assert len(train_ds) + len(val_ds) == 394
