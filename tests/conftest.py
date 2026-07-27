"""Fixture dùng chung: annotation JSON tối giản (không cần data thật 83.7GB)."""

import json
from pathlib import Path

import pytest

CATEGORY_INFO = {
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


def make_phase_entry(
    phase: str,
    category: int,
    boxes: list[dict],
    pixel_spacing: tuple[float, float] = (0.7, 0.7),
    slice_spacing: float = 5.0,
    slice_thickness: float = 5.0,
) -> dict:
    """Dựng một phase-entry đúng schema annotation thật."""
    return {
        "studyUID": "1.2.3",
        "seriesUID": "1.2.3.0",
        "pixel_spacing": list(pixel_spacing),
        "slice_spacing": slice_spacing,
        "slice_thickness": slice_thickness,
        "origin": [0.0, 0.0, 0.0],
        "phase": phase,
        "annotation": {
            "num_targets": 1,
            "lesion": {"0": {"category": category, "bbox": {"2D_box": boxes, "3D_box": None}}},
        },
    }


def make_boxes(slices: list[int], x0: float, y0: float, x1: float, y1: float) -> list[dict]:
    """Danh sách 2D_box giống nhau trải trên các slice cho trước."""
    return [
        {"slice_idx": s, "x_min": x0, "y_min": y0, "x_max": x1, "y_max": y1, "area": 1.0}
        for s in slices
    ]


@pytest.fixture
def annotation_path(tmp_path: Path) -> Path:
    """Annotation 3 bệnh nhân: 2 HCC + 1 nang, mỗi ca 2 pha (C+V, DWI)."""
    data = {
        "Category_info": CATEGORY_INFO,
        "Annotation_info": {
            "MR-100001": [
                make_phase_entry("C+V", 6, make_boxes([10, 11, 12], 20.0, 30.0, 40.0, 50.0)),
                make_phase_entry(
                    "DWI", 6, make_boxes([5], 8.0, 9.0, 12.0, 13.0), (2.8, 2.8), 6.0, 6.0
                ),
            ],
            "MR100002": [
                make_phase_entry("C+V", 6, make_boxes([7, 8], 10.0, 10.0, 20.0, 24.0)),
                make_phase_entry(
                    "DWI", 6, make_boxes([3], 4.0, 4.0, 8.0, 8.0), (2.8, 2.8), 6.0, 6.0
                ),
            ],
            "MR100003": [
                make_phase_entry("C+V", 4, make_boxes([15], 5.0, 5.0, 11.0, 9.0)),
            ],
        },
    }
    path = tmp_path / "annotation.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path
