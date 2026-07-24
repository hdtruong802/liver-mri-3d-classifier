"""Nạp + validate official split (đã tái lập, khoá ở `splits/`).

Split là official LLD-MMRI 316/78/104 (xem `splits/README.md`). Module này **chỉ
đọc và kiểm tra**, KHÔNG sinh split (split bất biến — AGENTS.md §3.6).

ID trong file split lưu theo key annotation; mọi so khớp đi qua `normalize_pid`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.utils.ids import normalize_pid
from src.utils.io import read_id_class_file

N_TRAINVAL = 394
N_TEST = 104
N_TOTAL = 498
N_FOLDS = 5


@dataclass(frozen=True)
class Fold:
    """Một fold CV: danh sách (patient_id, class) cho train và val."""

    index: int
    train: list[tuple[str, int]]
    val: list[tuple[str, int]]


class Splits:
    """Truy cập official split đã khoá."""

    def __init__(self, splits_dir: str | Path) -> None:
        self.dir = Path(splits_dir)
        self.trainval = read_id_class_file(self.dir / "labels_trainval.txt")
        self.test = read_id_class_file(self.dir / "test_official.txt")
        self.folds: list[Fold] = []
        for i in range(1, N_FOLDS + 1):
            train = read_id_class_file(self.dir / f"train_fold{i}.txt")
            val = read_id_class_file(self.dir / f"val_fold{i}.txt")
            self.folds.append(Fold(index=i, train=train, val=val))

    @staticmethod
    def _keys(rows: list[tuple[str, int]]) -> set[str]:
        return {normalize_pid(pid) for pid, _ in rows}

    def test_keys(self) -> set[str]:
        """Tập chữ số-hoá của test-104 (held-out khoá kín, chạm 1 lần)."""
        return self._keys(self.test)

    def trainval_keys(self) -> set[str]:
        return self._keys(self.trainval)

    def validate(self) -> None:
        """Kiểm bất biến của split; raise AssertionError nếu sai (dùng ở test & CLI).

        - đếm đúng 394 / 104 / 498, không trùng lặp trong từng file;
        - trainval ∩ test = ∅;
        - mỗi fold: train ∩ val = ∅ và train ∪ val = trainval;
        - test-104 không lọt vào bất kỳ fold nào.
        """
        tv, te = self.trainval_keys(), self.test_keys()
        assert len(self.trainval) == N_TRAINVAL, f"trainval={len(self.trainval)} != {N_TRAINVAL}"
        assert len(tv) == N_TRAINVAL, "trainval có ID trùng lặp"
        assert len(self.test) == N_TEST, f"test={len(self.test)} != {N_TEST}"
        assert len(te) == N_TEST, "test có ID trùng lặp"
        assert tv.isdisjoint(te), "LEAK: trainval ∩ test != ∅"
        assert len(tv | te) == N_TOTAL, f"union != {N_TOTAL}"

        for fold in self.folds:
            tr, va = self._keys(fold.train), self._keys(fold.val)
            assert tr.isdisjoint(va), f"LEAK fold{fold.index}: train ∩ val != ∅"
            assert tr | va == tv, f"fold{fold.index}: train ∪ val != trainval"
            assert va.isdisjoint(te), f"LEAK fold{fold.index}: val chạm test-104"
