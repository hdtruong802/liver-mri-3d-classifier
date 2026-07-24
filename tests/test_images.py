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
