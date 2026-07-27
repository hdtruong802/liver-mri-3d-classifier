"""Test thống kê EDA trên fixture annotation (không cần data thật)."""

from pathlib import Path

from src.data.annotation import Annotation
from src.data.eda import (
    bbox_stats,
    class_distribution,
    format_class_distribution,
    geometry_summary_by_phase,
    missing_phase_report,
    phase_geometry,
    recommend_crop_size,
)


def test_class_distribution_counts_all_seven_classes(annotation_path: Path):
    dist = class_distribution(Annotation(annotation_path))
    assert set(dist) == set(range(7))  # mọi lớp đều có key, kể cả lớp 0 ca
    assert dist[6] == 2  # 2 HCC
    assert dist[4] == 1  # 1 nang
    assert dist[0] == 0
    assert sum(dist.values()) == 3


def test_format_class_distribution_includes_total(annotation_path: Path):
    text = format_class_distribution(class_distribution(Annotation(annotation_path)))
    assert "TỔNG" in text
    assert "HCC" in text


def test_phase_geometry_one_row_per_patient_phase(annotation_path: Path):
    geoms = phase_geometry(Annotation(annotation_path))
    assert len(geoms) == 5  # 2 + 2 + 1 phase-entry
    dwi = [g for g in geoms if g.phase == "DWI"]
    assert len(dwi) == 2
    assert dwi[0].pixel_spacing == (2.8, 2.8)  # DWI thô hơn, đúng như PDF mô tả


def test_geometry_summary_separates_phases(annotation_path: Path):
    summary = geometry_summary_by_phase(phase_geometry(Annotation(annotation_path)))
    assert set(summary) == {"C+V", "DWI"}
    assert summary["C+V"]["pixel_spacing_x"]["p50"] == 0.7
    assert summary["DWI"]["pixel_spacing_x"]["p50"] == 2.8
    assert summary["DWI"]["slice_spacing"]["p50"] == 6.0


def test_bbox_stats_converts_to_mm(annotation_path: Path):
    stats = bbox_stats(Annotation(annotation_path), "C+V")
    assert len(stats) == 3
    first = next(s for s in stats if s.patient_id == "MR-100001")
    # bbox x: 20->40 = 20px, spacing 0.7 => 14mm
    assert first.width_px == 20.0
    assert first.width_mm == 14.0
    # slice 10..12 inclusive = 3 slice, spacing 5.0 => 15mm
    assert first.depth_slices == 3
    assert first.depth_mm == 15.0


def test_bbox_stats_skips_patients_without_phase(annotation_path: Path):
    """MR-100003 không có pha DWI -> bỏ qua, không raise."""
    stats = bbox_stats(Annotation(annotation_path), "DWI")
    assert len(stats) == 2
    assert all(s.patient_id != "MR-100003" for s in stats)


def test_recommend_crop_size_scales_with_margin(annotation_path: Path):
    stats = bbox_stats(Annotation(annotation_path), "C+V")
    rec = recommend_crop_size(stats, target_spacing=(1.5, 1.5, 3.0), margin=1.0)
    rec_margin = recommend_crop_size(stats, target_spacing=(1.5, 1.5, 3.0), margin=2.0)
    assert rec_margin["voxels_x"] > rec["voxels_x"]
    assert rec["n_cases"] == 3


def test_recommend_crop_size_empty_input():
    assert recommend_crop_size([]) == {}


def test_missing_phase_report_detects_gaps(annotation_path: Path):
    ann = Annotation(annotation_path)
    # index giả: MR-100001 đủ 2 pha, MR100002 thiếu DWI, MR100003 thiếu cả hai
    image_index = {
        ("100001", "C+V"): Path("a.nii.gz"),
        ("100001", "DWI"): Path("b.nii.gz"),
        ("100002", "C+V"): Path("c.nii.gz"),
    }
    report = missing_phase_report(ann, image_index, ["C+V", "DWI"])
    assert report.n_patients == 3
    assert report.n_complete == 1
    assert report.n_incomplete == 2
    assert report.missing_by_phase["DWI"] == 2
    assert report.missing_by_phase["C+V"] == 1


def test_missing_phase_report_all_present(annotation_path: Path):
    ann = Annotation(annotation_path)
    image_index = {
        (key, tok): Path("x.nii.gz")
        for key in ("100001", "100002", "100003")
        for tok in ("C+V", "DWI")
    }
    report = missing_phase_report(ann, image_index, ["C+V", "DWI"])
    assert report.n_incomplete == 0
    assert report.incomplete_patients == []
