"""normalize_pid phải map mọi hình thức ID về cùng khoá chữ số."""

import pytest
from src.utils.ids import normalize_pid


def test_normalize_pid_strips_prefix_and_hyphen():
    assert normalize_pid("MR-391135") == "391135"


def test_normalize_pid_no_hyphen():
    assert normalize_pid("MR207602") == "207602"


def test_normalize_pid_agrees_across_forms():
    # Cùng bệnh nhân biểu diễn 2 cách khác nhau phải map về cùng khoá.
    assert normalize_pid("MR-207602") == normalize_pid("MR207602")


def test_normalize_pid_rejects_no_digits():
    with pytest.raises(ValueError):
        normalize_pid("MR-abcxyz")
