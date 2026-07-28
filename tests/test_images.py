"""Test image index: quét file NIfTI giả lập, map (patient_key, token) -> path."""

from pathlib import Path

import pytest
from src.data.images import phase_paths, scan_image_index


@pytest.fixture
def images_dir(tmp_path: Path) -> Path:
    d = tmp_path / "images"
    d.mkdir()
    names = [
        "MR-391135_1_C-pre_0000.nii.gz",
        "MR-391135_1_C+A_0000.nii.gz",
        "MR391135_1_T2WI_0000.nii.gz",  # cố tình khác hình thức ID (không gạch nối)
        "MR207602_2_C-pre_0000.nii.gz",
    ]
    for name in names:
        (d / name).write_bytes(b"")
    return d


def test_scan_image_index_keys_by_normalized_id(images_dir: Path):
    index = scan_image_index(images_dir)
    assert ("391135", "C-pre") in index
    assert ("391135", "C+A") in index
    assert ("391135", "T2WI") in index  # khác hình thức ID vẫn map cùng khoá
    assert ("207602", "C-pre") in index
    assert len(index) == 4


def test_phase_paths_returns_in_order(images_dir: Path):
    index = scan_image_index(images_dir)
    paths = phase_paths(index, "MR-391135", ["C-pre", "C+A"])
    assert len(paths) == 2
    assert paths[0].name.endswith("C-pre_0000.nii.gz")
    assert paths[1].name.endswith("C+A_0000.nii.gz")


def test_phase_paths_missing_raises(images_dir: Path):
    index = scan_image_index(images_dir)
    with pytest.raises(FileNotFoundError, match="DWI"):
        phase_paths(index, "MR-391135", ["C-pre", "DWI"])


# --- Bản Kaggle lưu .nii đã giải nén, không phải .nii.gz (WORKLOG S-025) ---


@pytest.fixture
def images_dir_plain_nii(tmp_path: Path) -> Path:
    """Thư mục ảnh kiểu Kaggle: `.nii` đã giải nén."""
    d = tmp_path / "images_nii"
    d.mkdir()
    for name in [
        "MR-391135_1_C-pre_0000.nii",
        "MR-391135_1_C+A_0000.nii",
        "MR-391135_1_InPhase_0000.nii",
    ]:
        (d / name).write_bytes(b"")
    return d


def test_scan_finds_plain_nii_files(images_dir_plain_nii: Path):
    """Bug đã gặp thật: chỉ tìm `.nii.gz` ⇒ index rỗng ⇒ mọi bước sau bị bỏ qua âm thầm."""
    index = scan_image_index(images_dir_plain_nii)
    assert len(index) == 3
    assert ("391135", "C-pre") in index
    assert ("391135", "InPhase") in index


def test_scan_handles_mixed_nii_and_gz(tmp_path: Path):
    """Thư mục lẫn hai đuôi: đếm đủ, không trùng lặp."""
    d = tmp_path / "mixed"
    d.mkdir()
    (d / "MR-1_1_C+A_0000.nii").write_bytes(b"")
    (d / "MR-2_1_C+A_0000.nii.gz").write_bytes(b"")
    index = scan_image_index(d)
    assert len(index) == 2
    assert index[("1", "C+A")].name.endswith(".nii")
    assert index[("2", "C+A")].name.endswith(".nii.gz")


def test_gz_wins_when_both_exist_for_same_phase(tmp_path: Path):
    """Cùng (bệnh nhân, pha) có cả hai đuôi -> chọn theo thứ tự ưu tiên, ổn định."""
    d = tmp_path / "dup"
    d.mkdir()
    (d / "MR-1_1_C+A_0000.nii").write_bytes(b"")
    (d / "MR-1_1_C+A_0000.nii.gz").write_bytes(b"")
    index = scan_image_index(d)
    assert len(index) == 1
    assert index[("1", "C+A")].name.endswith(".nii.gz")


def test_scan_accepts_single_suffix_string(images_dir_plain_nii: Path):
    """Vẫn nhận một chuỗi đơn (tương thích cách gọi cũ)."""
    index = scan_image_index(images_dir_plain_nii, "_0000.nii")
    assert len(index) == 3


def test_scans_masks_without_channel_suffix(tmp_path):
    """Mask theo quy ước nnU-Net không có `_0000`; phải quét được bằng label_suffixes.

    Dùng nhầm danh sách đuôi của ảnh thì khớp 0 file, và vì build_cache có đường
    lui về bbox nên cả mẻ vẫn chạy xong trong khi mask chưa từng được dùng
    (WORKLOG S-059).
    """
    from src.data.images import DEFAULT_IMAGE_SUFFIXES, DEFAULT_LABEL_SUFFIXES, scan_image_index

    labels = tmp_path / "labels"
    labels.mkdir()
    for token in ("C+V", "DWI", "InPhase"):
        (labels / f"MR-391135_1_{token}.nii").touch()

    assert scan_image_index(labels, DEFAULT_IMAGE_SUFFIXES) == {}, (
        "đuôi của ảnh KHÔNG được khớp file mask — nếu khớp thì test này vô nghĩa"
    )

    index = scan_image_index(labels, DEFAULT_LABEL_SUFFIXES)
    assert len(index) == 3
    # Khoá là phần chữ số của patient ID (xem src/utils/ids.py).
    assert ("391135", "C+V") in index


def test_label_suffix_order_prefers_compressed(tmp_path):
    """Có cả .nii.gz lẫn .nii cho cùng một pha thì bản nén được chọn."""
    from src.data.images import DEFAULT_LABEL_SUFFIXES, scan_image_index

    labels = tmp_path / "labels"
    labels.mkdir()
    (labels / "MR-1_1_C+V.nii").touch()
    (labels / "MR-1_1_C+V.nii.gz").touch()

    index = scan_image_index(labels, DEFAULT_LABEL_SUFFIXES)
    assert index[("1", "C+V")].name.endswith(".nii.gz")
