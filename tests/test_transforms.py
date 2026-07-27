"""Test augmentation.

Hai ràng buộc y học được khoá ở đây:
- **không lật/xoay theo trục Z** (hướng đầu-chân, lát dày 3mm — biến đổi ở đó tạo
  giải phẫu không có thật);
- **biến đổi hình học phải giống nhau cho cả 8 pha**, nếu không sẽ phá chính tín
  hiệu động học mà model cần học.
"""

import pytest
from src.data.transforms import (
    Compose,
    RandomFlip,
    RandomIntensity,
    RandomRot90InPlane,
    build_train_transform,
)

pytest.importorskip("torch", reason="transform chạy trên tensor torch")
import torch  # noqa: E402


def _item(shape=(8, 4, 6, 3)):
    return {"image": torch.arange(torch.tensor(shape).prod()).reshape(shape).float()}


def _z_index_volume(shape=(8, 4, 6, 3)):
    """Khối mà giá trị mỗi voxel = chỉ số Z của nó.

    Bất kỳ phép biến đổi nào **chỉ trong mặt phẳng** đều để khối này y nguyên; hễ
    có thao tác chạm trục Z là giá trị đổi ngay.
    """
    return torch.arange(shape[3]).float().expand(shape).clone()


def test_flip_applies_the_same_geometry_to_all_8_phases():
    original = torch.randn(8, 4, 6, 3)
    out = RandomFlip(prob=1.0)({"image": original.clone()})["image"]

    # prob=1.0 -> lật cả hai trục trong mặt phẳng, kết quả xác định.
    assert torch.equal(out, torch.flip(original, dims=(1, 2)))


def test_flip_never_touches_z_axis():
    """Lát cắt theo Z phải giữ nguyên thứ tự — lật theo Z tạo giải phẫu không có thật."""
    original = _z_index_volume()
    out = RandomFlip(prob=1.0)({"image": original.clone()})["image"]
    assert torch.equal(out, original)


def test_rot90_rotates_in_plane_only():
    original = _z_index_volume(shape=(8, 4, 4, 3))
    out = RandomRot90InPlane(prob=1.0)({"image": original.clone()})["image"]

    assert out.shape == (8, 4, 4, 3)
    assert torch.equal(out, original), "xoay đã chạm trục Z"


def test_rot90_with_zero_prob_is_identity():
    original = _item()["image"]
    out = RandomRot90InPlane(prob=0.0)({"image": original.clone()})["image"]
    assert torch.equal(out, original)


def test_intensity_varies_per_phase():
    """Nhiễu cường độ cố ý khác nhau giữa các pha (mô phỏng dao động máy chụp)."""
    torch.manual_seed(0)
    original = torch.ones(8, 2, 2, 2)
    out = RandomIntensity(shift=0.5, scale=0.5, prob=1.0)({"image": original.clone()})["image"]

    per_phase = out.flatten(1).mean(dim=1)
    assert per_phase.std() > 0, "8 pha nhận cùng một hệ số -> không mô phỏng được dao động"
    # Nhưng trong một pha thì hệ số là hằng số.
    assert out[0].std() == pytest.approx(0.0, abs=1e-6)


def test_compose_applies_in_order():
    calls = []
    transform = Compose([lambda i: (calls.append("a"), i)[1], lambda i: (calls.append("b"), i)[1]])
    transform({"image": torch.zeros(1)})
    assert calls == ["a", "b"]


def test_build_train_transform_none_when_no_augment_config():
    assert build_train_transform(None) is None
    assert build_train_transform({}) is None
    assert build_train_transform({"flip_prob": 0, "rot90_prob": 0}) is None


def test_build_train_transform_from_config():
    transform = build_train_transform(
        {"flip_prob": 0.5, "rot90_prob": 0.5, "intensity_prob": 0.5, "intensity_shift": 0.1}
    )
    assert isinstance(transform, Compose)
    assert len(transform.transforms) == 3
    out = transform(_item())
    assert out["image"].shape[0] == 8
