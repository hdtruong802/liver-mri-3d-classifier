"""Đọc volume thật và render lát.

Toàn bộ file skip sạch khi không có `data/sample/` — thư mục đó bị .gitignore vì
chứa dữ liệu bệnh nhân, nên máy khác clone repo về sẽ không có. Test phải phản ánh
đúng điều đó thay vì fail.
"""

from __future__ import annotations

import io

import pytest

pytest.importorskip("nibabel", reason="lớp serve chưa cài")
pytest.importorskip("PIL", reason="lớp serve chưa cài")

from PIL import Image  # noqa: E402
from webapp.backend import demo_cases  # noqa: E402
from webapp.backend.config import SAMPLE_DIR  # noqa: E402
from webapp.backend.phases import PHASES  # noqa: E402
from webapp.backend.volumes import (  # noqa: E402
    find_phase_files,
    n_slices,
    read_geometry,
    render_slice_png,
)

CASE_ID = "MR-391135_1"

pytestmark = pytest.mark.skipif(
    not SAMPLE_DIR.is_dir(),
    reason=f"không có dữ liệu mẫu ở {SAMPLE_DIR} (data/ bị gitignore — đúng như thiết kế)",
)


@pytest.fixture(scope="module")
def phase_files() -> dict:
    files = find_phase_files(SAMPLE_DIR, CASE_ID)
    if len(files) != len(PHASES):
        pytest.skip(f"ca mẫu chỉ có {len(files)}/{len(PHASES)} thì")
    return files


def test_sample_case_has_all_eight_phases(phase_files: dict) -> None:
    assert set(phase_files) == {p.file_token for p in PHASES}


def test_geometry_is_read_from_header(phase_files: dict) -> None:
    shape, spacing = read_geometry(phase_files["C+V"])
    assert len(shape) == 3 and all(v > 0 for v in shape)
    assert len(spacing) == 3 and all(v > 0 for v in spacing)


def test_render_slice_returns_grayscale_png(phase_files: dict) -> None:
    path = phase_files["C+V"]
    payload = render_slice_png(path, n_slices(path) // 2)
    picture = Image.open(io.BytesIO(payload))
    assert picture.format == "PNG"
    assert picture.mode == "L", "ảnh MRI là thang xám, không tô màu giả"


def test_render_slice_is_cached_and_stable(phase_files: dict) -> None:
    path = phase_files["C+V"]
    z = n_slices(path) // 2
    assert render_slice_png(path, z) == render_slice_png(path, z)


def test_render_slice_rejects_out_of_range(phase_files: dict) -> None:
    path = phase_files["C+V"]
    with pytest.raises(IndexError):
        render_slice_png(path, n_slices(path))
    with pytest.raises(IndexError):
        render_slice_png(path, -1)


def test_different_phases_render_different_images(phase_files: dict) -> None:
    """Tám thì là tám chuỗi xung khác nhau; nếu ra ảnh giống hệt là đang đọc nhầm file."""
    z_ratio = 0.5
    pre = render_slice_png(phase_files["C-pre"], int(n_slices(phase_files["C-pre"]) * z_ratio))
    t2 = render_slice_png(phase_files["T2WI"], int(n_slices(phase_files["T2WI"]) * z_ratio))
    assert pre != t2


def test_case_detail_reports_real_geometry() -> None:
    detail = demo_cases.get_case_detail(CASE_ID)
    assert detail.case_id == CASE_ID
    assert len(detail.volumes) == len(PHASES)
    assert detail.reference_phase == "C+V"
    for volume in detail.volumes:
        assert volume.n_slices > 0
        assert all(s > 0 for s in volume.spacing_mm)


def test_case_detail_is_marked_simulated() -> None:
    """Ảnh thật, dự đoán giả lập. Ghép hai thứ làm số giả đáng tin hơn, nên phải đánh dấu."""
    detail = demo_cases.get_case_detail(CASE_ID)
    assert detail.provenance.source.value == "simulated"
    assert "thật" in detail.source_note and "minh hoạ" in detail.source_note
