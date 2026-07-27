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
    RandomRotateSmall,
    RandomTranslate3D,
    build_train_transform,
    resolve_axes,
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


def test_resolve_axes_maps_names_to_tensor_dims():
    assert resolve_axes(["x", "y", "z"]) == (1, 2, 3)
    assert resolve_axes(None) == (1, 2)  # mặc định: chỉ trong mặt phẳng


def test_resolve_axes_rejects_typos():
    """`flip_axes: [w]` phải nổ ngay, đừng lặng lẽ bỏ qua một trục."""
    with pytest.raises(ValueError, match="không hợp lệ"):
        resolve_axes(["x", "w"])


def test_flip_can_include_z_when_config_says_so():
    """Recipe official lật cả trục z (randomflip_z, p=0.5)."""
    original = _z_index_volume()
    out = RandomFlip(prob=1.0, axes=resolve_axes(["x", "y", "z"]))({"image": original.clone()})[
        "image"
    ]
    assert torch.equal(out, torch.flip(original, dims=(1, 2, 3)))


# --- Xoay góc nhỏ (thay rot90) ----------------------------------------------


def test_small_rotation_keeps_shape_and_is_finite():
    """`reshape=False` -> shape không đổi; nếu đổi thì batch vỡ giữa epoch."""
    original = torch.randn(8, 32, 32, 12)
    out = RandomRotateSmall(degrees=10, prob=1.0)({"image": original.clone()})["image"]

    assert out.shape == original.shape
    assert torch.isfinite(out).all()


def test_small_rotation_does_not_touch_z():
    """Xoay quanh trục z: khối 'giá trị = chỉ số z' phải gần như y nguyên."""
    original = _z_index_volume(shape=(2, 24, 24, 5))
    out = RandomRotateSmall(degrees=10, prob=1.0)({"image": original.clone()})["image"]

    # Vùng lõi không bị góc ảnh quay ra ngoài chạm tới -> phải khớp đúng chỉ số z.
    core = out[:, 6:18, 6:18, :]
    assert torch.allclose(core, original[:, 6:18, 6:18, :], atol=1e-4)


def test_small_rotation_is_identical_across_phases():
    """Biến đổi hình học phải đồng nhất cho cả 8 pha."""
    base = torch.randn(1, 24, 24, 4)
    original = base.repeat(8, 1, 1, 1)
    out = RandomRotateSmall(degrees=10, prob=1.0)({"image": original.clone()})["image"]

    for channel in range(1, 8):
        assert torch.allclose(out[channel], out[0])


def test_small_rotation_zero_degrees_is_identity():
    original = torch.randn(2, 16, 16, 4)
    out = RandomRotateSmall(degrees=0, prob=1.0)({"image": original.clone()})["image"]
    assert torch.equal(out, original)


# --- Tịnh tiến (thay random_crop của official) -------------------------------


def test_translate_keeps_shape():
    original = torch.randn(8, 32, 32, 12)
    out = RandomTranslate3D(max_shift=(8, 8, 4), prob=1.0)({"image": original.clone()})["image"]
    assert out.shape == original.shape


def test_translate_preserves_voxel_values_it_keeps():
    """Chỉ dịch và đệm 0 — giá trị giữ lại không được biến dạng."""
    original = torch.arange(2 * 8 * 8 * 4).reshape(2, 8, 8, 4).float()
    out = RandomTranslate3D(max_shift=(3, 3, 1), prob=1.0)({"image": original.clone()})["image"]

    kept = out[out != 0]
    assert torch.isin(kept, original).all()


def test_translate_zero_shift_is_identity():
    original = torch.randn(2, 8, 8, 4)
    out = RandomTranslate3D(max_shift=(0, 0, 0), prob=1.0)({"image": original.clone()})["image"]
    assert torch.equal(out, original)


def test_translate_actually_moves_content():
    torch.manual_seed(3)
    original = torch.ones(1, 8, 8, 4)
    shifted = [
        RandomTranslate3D(max_shift=(4, 4, 2), prob=1.0)({"image": original.clone()})["image"]
        for _ in range(10)
    ]
    # Ít nhất một lần phải sinh vùng đệm 0 -> tức là có dịch thật.
    assert any(float(out.min()) == 0.0 for out in shifted)


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


def test_build_train_transform_from_official_recipe_config():
    """Đúng khối augment trong `configs/baseline_3dpatch.yaml` sau khi theo recipe."""
    transform = build_train_transform(
        {
            "flip_prob": 0.5,
            "flip_axes": ["x", "y", "z"],
            "rotate_degrees": 10,
            "translate_voxels": [8, 8, 4],
            "rot90_prob": 0,
            "intensity_prob": 0,
        }
    )
    assert isinstance(transform, Compose)
    kinds = [type(t).__name__ for t in transform.transforms]
    assert kinds == ["RandomFlip", "RandomRotateSmall", "RandomTranslate3D"]

    out = transform({"image": torch.randn(8, 24, 24, 8)})["image"]
    assert out.shape == (8, 24, 24, 8)
    assert torch.isfinite(out).all()


def test_config_file_augment_block_builds_and_runs():
    """Chốt chặn: khối augment thật trong config phải dựng và chạy được."""
    from src.utils.io import load_yaml, repo_root

    config = load_yaml(repo_root() / "configs" / "baseline_3dpatch.yaml")
    transform = build_train_transform(config["data"]["augment"])

    assert transform is not None
    out = transform({"image": torch.randn(8, 24, 24, 8)})["image"]
    assert out.shape == (8, 24, 24, 8)
    assert torch.isfinite(out).all()
