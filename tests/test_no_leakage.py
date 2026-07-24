"""Test chống leakage cho official split (AGENTS.md §3.2 — bắt buộc, không ngoại lệ).

Kiểm:
- kích thước đúng 316(=train_fold1 size khác theo fold)/78/104 tổng quát 394/104/498;
- giao tập bệnh nhân giữa MỌI cặp fold = rỗng (train vs val cùng fold, và test vs mọi fold);
- hợp các tập con luôn tái tạo đúng toàn bộ 498.

Nếu test này fail: DỪNG, sửa `splits/`, không đi tiếp (không phải lỗi có thể bỏ qua).
"""

from itertools import combinations

import pytest
from src.data.splits import N_FOLDS, N_TEST, N_TOTAL, N_TRAINVAL, Splits

SPLITS_DIR = "splits"


@pytest.fixture(scope="module")
def splits() -> Splits:
    return Splits(SPLITS_DIR)


def test_trainval_size(splits: Splits):
    assert len(splits.trainval) == N_TRAINVAL


def test_test_size(splits: Splits):
    assert len(splits.test) == N_TEST


def test_no_duplicate_ids_within_each_file(splits: Splits):
    assert len(splits.trainval_keys()) == N_TRAINVAL
    assert len(splits.test_keys()) == N_TEST


def test_trainval_test_disjoint(splits: Splits):
    """Bệnh nhân KHÔNG được vừa ở train+val vừa ở test-104."""
    assert splits.trainval_keys().isdisjoint(splits.test_keys())


def test_union_covers_all_patients(splits: Splits):
    assert len(splits.trainval_keys() | splits.test_keys()) == N_TOTAL


def test_num_folds(splits: Splits):
    assert len(splits.folds) == N_FOLDS


def test_each_fold_train_val_disjoint(splits: Splits):
    """Trong 1 fold, bệnh nhân không được vừa train vừa val."""
    for fold in splits.folds:
        tr = {pid for pid, _ in fold.train}
        va = {pid for pid, _ in fold.val}
        assert not (tr & va), f"fold {fold.index}: leak train∩val"


def test_each_fold_union_equals_trainval(splits: Splits):
    """train ∪ val của mỗi fold phải đúng bằng toàn bộ 394 trainval."""
    tv = splits.trainval_keys()
    for fold in splits.folds:
        from src.utils.ids import normalize_pid

        tr = {normalize_pid(pid) for pid, _ in fold.train}
        va = {normalize_pid(pid) for pid, _ in fold.val}
        assert tr | va == tv, f"fold {fold.index}: union != trainval"


def test_no_fold_touches_test(splits: Splits):
    """test-104 khoá kín: không được lọt vào bất kỳ fold train/val nào."""
    te = splits.test_keys()
    from src.utils.ids import normalize_pid

    for fold in splits.folds:
        tr = {normalize_pid(pid) for pid, _ in fold.train}
        va = {normalize_pid(pid) for pid, _ in fold.val}
        assert tr.isdisjoint(te), f"fold {fold.index}: train chạm test-104"
        assert va.isdisjoint(te), f"fold {fold.index}: val chạm test-104"


def test_all_fold_pairs_disjoint_val_sets(splits: Splits):
    """val của các fold khác nhau không nhất thiết rời nhau tuyệt đối theo lý
    thuyết CV thông thường (val fold i có thể trùng train fold j), nhưng test-104
    phải rời khỏi TẤT CẢ. Test này chỉ khẳng định lại tính toàn vẹn tổng quát:
    mỗi bệnh nhân trainval xuất hiện ở đúng 1 val duy nhất qua 5 fold (đúng 5-fold CV).
    """
    from collections import Counter

    from src.utils.ids import normalize_pid

    counts: Counter[str] = Counter()
    for fold in splits.folds:
        for pid, _ in fold.val:
            counts[normalize_pid(pid)] += 1
    assert set(counts) == splits.trainval_keys()
    assert all(c == 1 for c in counts.values()), "mỗi bệnh nhân phải nằm val đúng 1 fold"


def test_validate_passes(splits: Splits):
    """Gọi thẳng Splits.validate() — cổng kiểm chính dùng ở CLI/CI."""
    splits.validate()


def test_all_split_files_exist_and_are_disjoint_pairs():
    """Kiểm tổng thể mọi cặp file split KHÔNG trùng lặp lẫn nhau ngoài quan hệ đã biết."""
    splits = Splits(SPLITS_DIR)
    all_sets = {"trainval": splits.trainval_keys(), "test": splits.test_keys()}
    for (name_a, set_a), (name_b, set_b) in combinations(all_sets.items(), 2):
        assert set_a.isdisjoint(set_b), f"{name_a} và {name_b} không rời nhau"
