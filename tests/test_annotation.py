"""Test Annotation trên fixture JSON tối giản (không cần data thật 83.7GB).

Schema fixture bám đúng cấu trúc đã xác minh trên bản dữ liệu thật
(docs/W2_plan.md §0): Category_info + Annotation_info[pid][phase]...
"""

import json
from pathlib import Path

import pytest
from src.data.annotation import Annotation

_CATEGORY_INFO = {
    "Hepatic_hemangioma": 0,
    "Intrahepatic_cholangiocarcinoma": 1,
    "Hepatic_abscess": 2,
    "Hepatic_metastasis": 3,
    "Hepatic_cyst": 4,
    "FOCAL_NODULAR_HYPERPLASIA": 5,
    "Hepatocellular_carcinoma": 6,
    "Benign": [0, 2, 4, 5],
    "Malignant": [1, 3, 6],
}


def _phase_entry(phase: str, category: int, boxes: list[dict]) -> dict:
    return {
        "studyUID": "1.2.3",
        "seriesUID": "1.2.3.0",
        "pixel_spacing": [0.7, 0.7],
        "slice_spacing": 5.0,
        "slice_thickness": 5.0,
        "origin": [0.0, 0.0, 0.0],
        "phase": phase,
        "annotation": {
            "num_targets": 1,
            "lesion": {"0": {"category": category, "bbox": {"2D_box": boxes, "3D_box": None}}},
        },
    }


@pytest.fixture
def fixture_path(tmp_path: Path) -> Path:
    boxes_hcc = [
        {"slice_idx": 10, "x_min": 10.0, "y_min": 20.0, "x_max": 30.0, "y_max": 40.0, "area": 400},
        {"slice_idx": 11, "x_min": 12.0, "y_min": 18.0, "x_max": 32.0, "y_max": 42.0, "area": 480},
    ]
    boxes_cyst = [
        {"slice_idx": 5, "x_min": 1.0, "y_min": 2.0, "x_max": 5.0, "y_max": 6.0, "area": 16},
    ]
    data = {
        "Category_info": _CATEGORY_INFO,
        "Annotation_info": {
            "MR-100001": [_phase_entry("C-pre", 6, boxes_hcc), _phase_entry("C+A", 6, boxes_hcc)],
            "MR100002": [_phase_entry("T2WI", 4, boxes_cyst)],
        },
    }
    path = tmp_path / "annotation.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_class_index_mapping(fixture_path: Path):
    ann = Annotation(fixture_path)
    assert ann.class_to_index["Hepatocellular_carcinoma"] == 6
    assert ann.index_to_class[6] == "Hepatocellular_carcinoma"
    assert "Benign" not in ann.class_to_index  # loại bỏ khoá list, chỉ giữ tên_lớp->int


def test_patient_ids(fixture_path: Path):
    ann = Annotation(fixture_path)
    assert set(ann.patient_ids()) == {"MR-100001", "MR100002"}
    assert len(ann) == 2


def test_category_of(fixture_path: Path):
    ann = Annotation(fixture_path)
    assert ann.category_of("MR-100001") == 6
    assert ann.category_of("MR100002") == 4


def test_is_malignant(fixture_path: Path):
    ann = Annotation(fixture_path)
    assert ann.is_malignant("MR-100001") is True  # HCC = ác
    assert ann.is_malignant("MR100002") is False  # nang = lành


def test_bbox3d_merges_2d_boxes_by_slice_idx(fixture_path: Path):
    ann = Annotation(fixture_path)
    box = ann.bbox3d("MR-100001", "C-pre")
    assert box.z_min == 10
    assert box.z_max == 11
    assert box.x_min == 10.0  # min qua các slice
    assert box.x_max == 32.0  # max qua các slice
    assert box.y_min == 18.0
    assert box.y_max == 42.0


def test_bbox3d_missing_phase_raises(fixture_path: Path):
    ann = Annotation(fixture_path)
    with pytest.raises(KeyError):
        ann.bbox3d("MR-100001", "DWI")  # bệnh nhân này fixture chỉ có C-pre/C+A
