"""Test phép thử tỉnh táo.

Phần chọn mẫu và phần đọc kết quả là logic thuần → chạy được không cần torch.
Riêng `overfit_check` cần torch nên chỉ chạy trên máy có deep-learning stack.
"""

import math

import pytest
from src.train.sanity import pick_diverse_subset, verdict

CHANCE = math.log(7)


def test_subset_spreads_across_classes():
    """Lấy n mẫu đầu danh sách là cách hỏng: dễ trúng toàn một lớp."""
    labels = [0] * 50 + [6] * 50
    picked = pick_diverse_subset(labels, 8)

    assert len(picked) == 8
    assert len({labels[i] for i in picked}) == 2
    assert sum(labels[i] == 0 for i in picked) == 4


def test_subset_covers_as_many_classes_as_possible():
    labels = [0, 1, 2, 3, 4, 5, 6] * 3
    picked = pick_diverse_subset(labels, 7)
    assert {labels[i] for i in picked} == set(range(7))


def test_subset_handles_rare_class_with_one_sample():
    """Áp-xe/FNH có thể chỉ vài ca — không được đòi nhiều hơn số có thật."""
    labels = [0] * 10 + [2]
    picked = pick_diverse_subset(labels, 6)

    assert len(picked) == 6
    assert 2 in {labels[i] for i in picked}
    assert len(set(picked)) == 6  # không lấy trùng một mẫu


def test_subset_caps_at_available_samples():
    picked = pick_diverse_subset([0, 1, 2], 10)
    assert sorted(picked) == [0, 1, 2]


def test_subset_indices_are_valid():
    labels = [3, 3, 5, 5, 1]
    picked = pick_diverse_subset(labels, 4)
    assert all(0 <= i < len(labels) for i in picked)


def test_verdict_learned_when_memorised():
    assert verdict({"loss_end": 0.01, "accuracy_end": 1.0}) == "HỌC ĐƯỢC"


def test_verdict_collapsed_at_chance_level():
    """Đúng chữ ký của bản InstanceNorm: loss đứng ở ln(7), đoán một lớp."""
    assert verdict({"loss_end": CHANCE, "accuracy_end": 0.125}) == "SẬP"


def test_verdict_slow_between_the_two():
    assert verdict({"loss_end": CHANCE * 0.5, "accuracy_end": 0.5}) == "CHẬM"


def test_verdict_uses_high_accuracy_even_if_loss_lingers():
    """Nhồi thuộc bài rồi thì accuracy là bằng chứng, loss có thể còn lơ lửng."""
    assert verdict({"loss_end": 0.5, "accuracy_end": 1.0}) == "HỌC ĐƯỢC"


@pytest.mark.parametrize("num_classes", [2, 7])
def test_verdict_scales_chance_with_class_count(num_classes):
    at_chance = {"loss_end": math.log(num_classes), "accuracy_end": 1.0 / num_classes}
    assert verdict(at_chance, num_classes=num_classes) == "SẬP"
