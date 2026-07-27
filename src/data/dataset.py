"""Dataset đọc cache đã tiền xử lý — đầu vào trực tiếp cho vòng train.

Bản trước đọc thẳng 8 volume thô rồi `np.stack`. Cách đó **không dùng được**: 8 pha
có lưới voxel khác nhau (pha động 512²×88, T2WI 512²×24, DWI 256²×24 — WORKLOG S-029)
nên `np.stack` sẽ ném lỗi shape. Việc đưa 8 pha về cùng lưới thuộc về
`src/preprocess/build_cache.py`; module này chỉ đọc kết quả đó.

Nhãn và danh sách bệnh nhân lấy từ `splits/` đã khoá — không tự sinh (AGENTS.md §3.6).
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np

from src.data.splits import Splits
from src.utils.ids import normalize_pid
from src.utils.io import resolve_repo_path


class CachedLesionDataset:
    """Đọc các patch đã tiền xử lý; trả về dict dùng được cho vòng train.

    Trả về ``{"image": tensor[8, X, Y, Z] float32, "label": int, "patient_id": str}``.
    `torch` được import **lười** để module vẫn nạp được khi chưa cài deep-learning stack.
    """

    def __init__(
        self,
        cache_dir: str | Path,
        samples: Sequence[tuple[str, int]],
        transform: Any | None = None,
    ) -> None:
        self.cache_dir = Path(cache_dir)
        self.transform = transform
        self.samples: list[tuple[Path, int, str]] = []

        missing: list[str] = []
        for patient_id, label in samples:
            path = self._find_file(patient_id)
            if path is None:
                missing.append(patient_id)
            else:
                self.samples.append((path, int(label), patient_id))

        if missing:
            raise FileNotFoundError(
                f"thiếu {len(missing)}/{len(samples)} file cache trong {self.cache_dir} "
                f"(vd {missing[:3]}). Chạy `python -m src.preprocess.build_cache` trước."
            )

    def _find_file(self, patient_id: str) -> Path | None:
        """Tìm file cache; khớp cả khi ID viết có/không gạch nối."""
        direct = self.cache_dir / f"{patient_id}.npz"
        if direct.exists():
            return direct
        key = normalize_pid(patient_id)
        for candidate in self.cache_dir.glob("*.npz"):
            if normalize_pid(candidate.stem) == key:
                return candidate
        return None

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, index: int) -> dict[str, Any]:
        import torch

        path, label, patient_id = self.samples[index]
        with np.load(path) as data:
            image = np.asarray(data["image"], dtype=np.float32)

        item: dict[str, Any] = {
            "image": torch.from_numpy(image),
            "label": label,
            "patient_id": patient_id,
        }
        if self.transform is not None:
            item = self.transform(item)
        return item


def build_fold_datasets(
    cache_dir: str | Path,
    fold_index: int,
    splits_dir: str | Path = "splits",
    train_transform: Any | None = None,
    val_transform: Any | None = None,
) -> tuple[CachedLesionDataset, CachedLesionDataset]:
    """Dựng cặp (train, val) cho một fold của CV chính thức.

    `fold_index` đếm từ 1 (khớp tên file `train_fold1.txt`). Split đã khoá và đã có
    test chống leakage ở `tests/test_no_leakage.py`.

    `splits_dir` tương đối được hiểu theo **gốc repo**, không phải CWD — xem
    `resolve_repo_path`.
    """
    splits = Splits(resolve_repo_path(splits_dir))
    if not 1 <= fold_index <= len(splits.folds):
        raise ValueError(f"fold_index phải trong 1..{len(splits.folds)}, nhận {fold_index}")

    fold = splits.folds[fold_index - 1]
    return (
        CachedLesionDataset(cache_dir, fold.train, train_transform),
        CachedLesionDataset(cache_dir, fold.val, val_transform),
    )


def build_test_dataset(
    cache_dir: str | Path,
    splits_dir: str | Path = "splits",
    transform: Any | None = None,
) -> CachedLesionDataset:
    """Dựng dataset cho **test-104 official**.

    ⚠️ Held-out khoá kín, **chạm đúng một lần** sau khi đã khoá protocol/model/threshold.
    Phải ghi WORKLOG trước khi dùng (AGENTS.md §3.4 và §10).
    """
    return CachedLesionDataset(cache_dir, Splits(resolve_repo_path(splits_dir)).test, transform)
