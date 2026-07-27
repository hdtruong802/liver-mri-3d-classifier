"""Test gate geometry với file NIfTI tổng hợp (nhỏ, tạo trong tmp_path).

Dùng NIfTI thật (không mock) để test đúng đường đọc header — chính chỗ dễ sai
khi bản dữ liệu bị resample.
"""

from pathlib import Path

import numpy as np
import pytest
from src.data.annotation import Annotation
from src.data.geometry_gate import check_phase, run_gate

PHASES = [{"name": "C+V", "file": "C+V"}, {"name": "DWI", "file": "DWI"}]


def _write_nifti(path: Path, shape: tuple[int, int, int], spacing: tuple[float, float, float]):
    """Ghi NIfTI tổng hợp với spacing chỉ định."""
    import nibabel as nib

    data = np.zeros(shape, dtype=np.int16)
    affine = np.diag([spacing[0], spacing[1], spacing[2], 1.0])
    img = nib.Nifti1Image(data, affine)
    img.header.set_zooms(spacing)
    nib.save(img, str(path))


@pytest.fixture
def good_images(tmp_path: Path) -> dict:
    """Ảnh khớp annotation fixture: spacing đúng, bbox lọt biên."""
    d = tmp_path / "images"
    d.mkdir()
    cv = d / "MR-100001_1_C+V_0000.nii.gz"
    dwi = d / "MR-100001_1_DWI_0000.nii.gz"
    _write_nifti(cv, (64, 64, 20), (0.7, 0.7, 5.0))
    _write_nifti(dwi, (32, 32, 10), (2.8, 2.8, 6.0))
    return {("100001", "C+V"): cv, ("100001", "DWI"): dwi}


def test_check_phase_passes_when_geometry_matches(annotation_path: Path, good_images: dict):
    ann = Annotation(annotation_path)
    check = check_phase("MR-100001", "C+V", "C+V", ann, good_images)
    assert check.spacing_matches
    assert check.bbox_z_in_bounds
    assert check.bbox_in_bounds_xy
    assert check.passed
    assert check.image_shape == (64, 64, 20)


def test_check_phase_detects_spacing_mismatch(annotation_path: Path, tmp_path: Path):
    """Ảnh đã bị resample (spacing 1.5) trong khi annotation ghi 0.7 -> phải FAIL."""
    d = tmp_path / "resampled"
    d.mkdir()
    path = d / "MR-100001_1_C+V_0000.nii.gz"
    _write_nifti(path, (64, 64, 20), (1.5, 1.5, 3.0))
    ann = Annotation(annotation_path)

    check = check_phase("MR-100001", "C+V", "C+V", ann, {("100001", "C+V"): path})
    assert not check.spacing_matches
    assert not check.passed
    assert any("pixel_spacing lệch" in n for n in check.notes)


def test_check_phase_detects_slice_out_of_bounds(annotation_path: Path, tmp_path: Path):
    """Ảnh chỉ 5 slice nhưng annotation trỏ slice 10-12 -> FAIL."""
    d = tmp_path / "short"
    d.mkdir()
    path = d / "MR-100001_1_C+V_0000.nii.gz"
    _write_nifti(path, (64, 64, 5), (0.7, 0.7, 5.0))
    ann = Annotation(annotation_path)

    check = check_phase("MR-100001", "C+V", "C+V", ann, {("100001", "C+V"): path})
    assert not check.bbox_z_in_bounds
    assert not check.passed
    assert any("slice_idx ngoài biên" in n for n in check.notes)


def test_check_phase_detects_bbox_out_of_plane_bounds(annotation_path: Path, tmp_path: Path):
    """Ảnh 16x16 nhưng bbox tới x=40 -> vượt biên theo cả 2 axis order."""
    d = tmp_path / "small"
    d.mkdir()
    path = d / "MR-100001_1_C+V_0000.nii.gz"
    _write_nifti(path, (16, 16, 20), (0.7, 0.7, 5.0))
    ann = Annotation(annotation_path)

    check = check_phase("MR-100001", "C+V", "C+V", ann, {("100001", "C+V"): path})
    assert not check.bbox_in_bounds_xy
    assert not check.bbox_in_bounds_xy_swapped
    assert not check.passed
    assert any("VƯỢT BIÊN" in n for n in check.notes)


def test_check_phase_missing_file_raises(annotation_path: Path):
    ann = Annotation(annotation_path)
    with pytest.raises(FileNotFoundError):
        check_phase("MR-100001", "C+V", "C+V", ann, {})


def test_run_gate_aggregates_and_passes(annotation_path: Path, good_images: dict):
    ann = Annotation(annotation_path)
    report = run_gate(["MR-100001"], ann, good_images, PHASES)
    assert len(report.checks) == 2
    assert report.passed
    assert report.n_failed == 0
    assert "PASS" in report.summary()


def test_run_gate_skips_missing_files_silently(annotation_path: Path, good_images: dict):
    """Bệnh nhân không có file -> bỏ qua, không làm hỏng cả gate."""
    ann = Annotation(annotation_path)
    report = run_gate(["MR-100001", "MR100002"], ann, good_images, PHASES)
    assert len(report.checks) == 2  # chỉ MR-100001 có file


def test_run_gate_reports_failure(annotation_path: Path, tmp_path: Path):
    d = tmp_path / "bad"
    d.mkdir()
    path = d / "MR-100001_1_C+V_0000.nii.gz"
    _write_nifti(path, (64, 64, 3), (0.7, 0.7, 5.0))  # quá ít slice
    ann = Annotation(annotation_path)

    report = run_gate(["MR-100001"], ann, {("100001", "C+V"): path}, PHASES)
    assert not report.passed
    assert report.n_failed == 1
    assert "FAIL" in report.summary()


def test_empty_gate_is_not_passed(annotation_path: Path):
    """Gate không có check nào KHÔNG được coi là đạt (tránh pass giả khi thiếu data)."""
    ann = Annotation(annotation_path)
    report = run_gate([], ann, {}, PHASES)
    assert not report.passed
    assert report.axis_order_verdict() == "none"
