"""Test phán quyết thứ tự trục bằng toạ độ thế giới.

Dựng NIfTI tổng hợp có affine thật, mô phỏng đúng tình huống của dữ liệu:
nhiều pha, KHÁC spacing/origin, nhưng cùng hệ toạ độ bệnh nhân.
"""

import json
from pathlib import Path

import numpy as np
import pytest
from src.data.annotation import Annotation
from src.preprocess.geometry import (
    bbox_center_voxel,
    lesion_center_world,
    resolve_axis_order,
    voxel_to_world,
)

from tests.conftest import CATEGORY_INFO, make_boxes, make_phase_entry

PHASES = [{"name": "C+V", "file": "C+V"}, {"name": "DWI", "file": "DWI"}]


def _affine(spacing: tuple[float, float, float], origin: tuple[float, float, float]) -> np.ndarray:
    a = np.diag([*spacing, 1.0])
    a[:3, 3] = origin
    return a


def _write(path: Path, shape, spacing, origin) -> None:
    import nibabel as nib

    nib.save(nib.Nifti1Image(np.zeros(shape, dtype=np.int16), _affine(spacing, origin)), str(path))


def test_voxel_to_world_applies_affine():
    affine = _affine((2.0, 2.0, 5.0), (-100.0, -50.0, 10.0))
    assert np.allclose(voxel_to_world(affine, [0, 0, 0]), [-100.0, -50.0, 10.0])
    assert np.allclose(voxel_to_world(affine, [10, 5, 2]), [-80.0, -40.0, 20.0])


def test_bbox_center_voxel_swaps_only_first_two_axes():
    from src.data.annotation import BBox3D

    box = BBox3D(x_min=10, y_min=20, z_min=4, x_max=30, y_max=40, z_max=6)
    assert np.allclose(bbox_center_voxel(box, "xy"), [20, 30, 5])
    assert np.allclose(bbox_center_voxel(box, "yx"), [30, 20, 5])  # trục z không đổi


def test_bbox_center_voxel_rejects_bad_order():
    from src.data.annotation import BBox3D

    with pytest.raises(ValueError, match="axis_order"):
        bbox_center_voxel(BBox3D(0, 0, 0, 1, 1, 1), "zz")


@pytest.fixture
def two_phase_case(tmp_path: Path):
    """Một bệnh nhân, 2 pha khác spacing/origin, bbox trỏ CÙNG điểm vật lý.

    **Origin phải BẤT ĐỐI XỨNG (x ≠ y)**, nếu không thì hoán vị x/y cũng hội tụ và
    test mất hết sức phân biệt. Đây đúng là điểm yếu của dữ liệu thật: origin có
    x≈y nên nhiều ca không phân biệt được (xem DECISIVE_MARGIN_MM).

    - C+V: spacing 1mm, origin (0, 0)    -> tâm voxel (100, 40) = world (100, 40)
    - DWI: spacing 2mm, origin (-50,-30) -> tâm voxel  (75, 35) = world (100, 40)
    Hoán vị x/y: C+V -> (40, 100); DWI -> (20, 120). Lệch 28mm.
    """
    d = tmp_path / "img"
    d.mkdir()
    cv, dwi = d / "MR-1_1_C+V_0000.nii", d / "MR-1_1_DWI_0000.nii"
    _write(cv, (256, 256, 20), (1.0, 1.0, 5.0), (0.0, 0.0, 0.0))
    _write(dwi, (128, 128, 20), (2.0, 2.0, 5.0), (-50.0, -30.0, 0.0))

    data = {
        "Category_info": CATEGORY_INFO,
        "Annotation_info": {
            "MR-1": [
                make_phase_entry("C+V", 6, make_boxes([9, 10, 11], 90.0, 30.0, 110.0, 50.0)),
                make_phase_entry(
                    "DWI", 6, make_boxes([9, 10, 11], 70.0, 30.0, 80.0, 40.0), (2.0, 2.0), 5.0, 5.0
                ),
            ]
        },
    }
    ann_path = tmp_path / "annotation.json"
    ann_path.write_text(json.dumps(data), encoding="utf-8")
    index = {("1", "C+V"): cv, ("1", "DWI"): dwi}
    return Annotation(ann_path), index


def test_lesion_center_world_matches_across_phases_under_correct_order(two_phase_case):
    """Cách hiểu đúng ⇒ hai pha chỉ về cùng một điểm mm."""
    import nibabel as nib

    ann, index = two_phase_case
    c_cv = lesion_center_world(ann, "MR-1", "C+V", nib.load(str(index[("1", "C+V")])).affine, "xy")
    c_dwi = lesion_center_world(ann, "MR-1", "DWI", nib.load(str(index[("1", "DWI")])).affine, "xy")
    assert np.allclose(c_cv[:2], [100.0, 40.0])
    assert np.allclose(c_dwi[:2], [100.0, 40.0])


def test_resolve_axis_order_picks_converging_interpretation(two_phase_case):
    ann, index = two_phase_case
    verdict = resolve_axis_order(["MR-1"], ann, index, PHASES)
    assert verdict.n_compared == 1
    assert verdict.n_decisive == 1
    assert verdict.verdict == "xy"
    assert verdict.votes["xy"] == 1
    # cách hiểu đúng phải tán rất nhỏ, cách sai tán lớn
    assert verdict.median_spread_mm["xy"] < verdict.median_spread_mm["yx"]
    assert "xy" in verdict.summary()


def test_resolve_axis_order_needs_at_least_two_phases(tmp_path: Path, annotation_path: Path):
    """Một pha thì không có gì để so -> không tính vào phiếu."""
    d = tmp_path / "one"
    d.mkdir()
    p = d / "MR-100001_1_C+V_0000.nii"
    _write(p, (64, 64, 20), (0.7, 0.7, 5.0), (0.0, 0.0, 0.0))

    verdict = resolve_axis_order(
        ["MR-100001"], Annotation(annotation_path), {("100001", "C+V"): p}, PHASES
    )
    assert verdict.n_compared == 0
    assert verdict.verdict == "inconclusive"


def test_verdict_inconclusive_when_no_data():
    from src.preprocess.geometry import AxisOrderVerdict

    assert AxisOrderVerdict().verdict == "inconclusive"


def test_verdict_inconclusive_when_split_vote():
    """Phiếu chia đôi -> KHÔNG đoán."""
    from src.preprocess.geometry import AxisOrderVerdict

    v = AxisOrderVerdict(
        n_compared=100,
        n_decisive=100,
        votes={"xy": 55, "yx": 45},
        median_spread_mm={"xy": 2.0, "yx": 3.0},
    )
    assert v.verdict == "inconclusive"
    assert "DỪNG" in v.summary()


def test_verdict_inconclusive_when_winner_still_scattered():
    """Thắng áp đảo nhưng vẫn tán rộng -> có vấn đề khác, không được tin."""
    from src.preprocess.geometry import AxisOrderVerdict

    v = AxisOrderVerdict(
        n_compared=100,
        n_decisive=100,
        votes={"xy": 98, "yx": 2},
        median_spread_mm={"xy": 120.0, "yx": 300.0},
    )
    assert v.verdict == "inconclusive"


# --- Phép đo phải bỏ trục Z (S-031) -----------------------------------------


def test_spread_ignores_z_axis():
    """Chênh lệch thuần theo Z KHÔNG được tính vào độ tán.

    Hoán vị thứ tự trục chỉ đụng X/Y; Z giống hệt nhau ở cả hai cách hiểu và bị
    chuyển động hô hấp chi phối (~23mm trên dữ liệu thật). Tính Z vào chỉ làm
    loãng tín hiệu phân biệt.
    """
    from src.preprocess.geometry import _spread_mm

    points = [np.array([0.0, 0.0, 0.0]), np.array([0.0, 0.0, 100.0])]
    assert _spread_mm(points) == pytest.approx(0.0)


def test_spread_measures_in_plane_distance():
    from src.preprocess.geometry import _spread_mm

    points = [np.array([0.0, 0.0, 5.0]), np.array([3.0, 4.0, 999.0])]
    assert _spread_mm(points) == pytest.approx(5.0)  # 3-4-5, Z bị bỏ qua


def test_breathing_motion_alone_does_not_block_verdict():
    """Ca thật: phiếu áp đảo + độ tán trong mặt phẳng hợp lý -> phải KẾT LUẬN được.

    Trước đây tính cả Z nên tổng độ tán 26.3mm vượt ngưỡng 25mm và bị gắn
    'inconclusive' dù phiếu đã 92% (WORKLOG S-031).
    """
    from src.preprocess.geometry import AxisOrderVerdict

    v = AxisOrderVerdict(
        n_compared=498,
        n_decisive=180,
        votes={"xy": 166, "yx": 14},
        median_spread_mm={"xy": 12.4, "yx": 17.8},
    )
    assert v.verdict == "xy"
