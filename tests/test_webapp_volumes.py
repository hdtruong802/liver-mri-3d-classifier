"""Đọc volume và render lát — `webapp/backend/volumes.py`.

Bản trước của file này dựng trên `data/sample/` (dữ liệu bệnh nhân thật) nên nó
**skip sạch ở mọi máy** vì `data/` bị .gitignore, và nó phụ thuộc `demo_cases` — module
đã gỡ ở WORKLOG S-197. Bản này dựng NIfTI tổng hợp trong `tmp_path`, nên nó **chạy
thật**. `volumes.py` vẫn là code sống: luồng tải ZIP lên gọi nó qua `upload_views`.

Đổi lại, những gì bản cũ khẳng định về dữ liệu thật (tám thì là tám chuỗi xung khác
nhau, mask có ít nhất một lát dương) không kiểm ở đây được nữa — chúng là tính chất
của dataset, không phải của hàm.
"""

from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("nibabel", reason="lớp serve chưa cài")
pytest.importorskip("PIL", reason="lớp serve chưa cài")

import nibabel as nib  # noqa: E402
from PIL import Image  # noqa: E402
from webapp.backend.phases import PHASES  # noqa: E402
from webapp.backend.volumes import (  # noqa: E402
    find_mask_files,
    find_phase_files,
    mask_slice_flags,
    n_slices,
    read_geometry,
    render_slice_png,
)

CASE_ID = "MR000000_1"
SHAPE = (16, 16, 6)
SPACING = (1.5, 1.5, 3.0)


def _affine() -> np.ndarray:
    return np.diag([*SPACING, 1.0])


def _write(path: Path, volume: np.ndarray) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    nib.save(nib.Nifti1Image(volume, _affine()), str(path))
    return path


@pytest.fixture
def case_dir(tmp_path: Path) -> Path:
    """Một ca tổng hợp đủ 8 thì, đúng quy ước tên của LLD-MMRI.

    Mỗi thì mang một cường độ nền khác nhau để phân biệt được ảnh của thì này với thì
    kia — đó là thứ hàm phải bảo đảm (đọc đúng file), khác với tính chất của dữ liệu.
    """
    rng = np.random.default_rng(20260819)
    for offset, phase in enumerate(PHASES):
        volume = rng.integers(0, 40, SHAPE).astype(np.int16) + offset * 100
        _write(tmp_path / f"{CASE_ID}_{phase.file_token}_0000.nii", volume)

    mask = np.zeros(SHAPE, dtype=np.uint8)
    mask[6:10, 6:10, 2:4] = 1  # tổn thương chỉ ở lát 2 và 3
    _write(tmp_path / "labels" / f"{CASE_ID}_C+V.nii", mask)
    return tmp_path


# --- tìm file ---------------------------------------------------------------


def test_tim_du_tam_thi(case_dir: Path) -> None:
    files = find_phase_files(case_dir, CASE_ID)
    assert set(files) == {p.file_token for p in PHASES}


def test_thu_muc_khong_ton_tai_tra_ve_rong(tmp_path: Path) -> None:
    assert find_phase_files(tmp_path / "khong-co", CASE_ID) == {}
    assert find_mask_files(tmp_path / "khong-co", CASE_ID) == {}


def test_mask_nam_o_labels_va_khong_mang_hau_to_kenh(case_dir: Path) -> None:
    """Mask KHÔNG mang hậu tố `_0000` như ảnh — dùng nhầm quy ước sẽ khớp 0 file."""
    masks = find_mask_files(case_dir, CASE_ID)
    assert set(masks) == {"C+V"}
    assert all("_0000" not in p.name for p in masks.values())


# --- hình học ---------------------------------------------------------------


def test_geometry_doc_tu_header(case_dir: Path) -> None:
    shape, spacing = read_geometry(find_phase_files(case_dir, CASE_ID)["C+V"])
    assert shape == SHAPE
    assert spacing == pytest.approx(SPACING)


def test_n_slices_khop_truc_z(case_dir: Path) -> None:
    assert n_slices(find_phase_files(case_dir, CASE_ID)["C+V"]) == SHAPE[2]


# --- render -----------------------------------------------------------------


def test_render_tra_ve_png_thang_xam(case_dir: Path) -> None:
    payload = render_slice_png(find_phase_files(case_dir, CASE_ID)["C+V"], 2)
    picture = Image.open(io.BytesIO(payload))
    assert picture.format == "PNG"
    assert picture.mode == "L", "ảnh MRI là thang xám, không tô màu giả"


def test_render_on_dinh_va_duoc_cache(case_dir: Path) -> None:
    path = find_phase_files(case_dir, CASE_ID)["C+V"]
    assert render_slice_png(path, 2) == render_slice_png(path, 2)


def test_render_tu_choi_lat_ngoai_bien(case_dir: Path) -> None:
    path = find_phase_files(case_dir, CASE_ID)["C+V"]
    with pytest.raises(IndexError):
        render_slice_png(path, SHAPE[2])
    with pytest.raises(IndexError):
        render_slice_png(path, -1)


def test_hai_thi_khac_file_cho_anh_khac_nhau(case_dir: Path) -> None:
    """Ra ảnh giống hệt nghĩa là đang đọc nhầm file."""
    files = find_phase_files(case_dir, CASE_ID)
    assert render_slice_png(files["C-pre"], 2) != render_slice_png(files["T2WI"], 2)


def test_phu_mask_doi_anh_va_van_la_png_hop_le(case_dir: Path) -> None:
    path = find_phase_files(case_dir, CASE_ID)["C+V"]
    mask = find_mask_files(case_dir, CASE_ID)["C+V"]
    tran = render_slice_png(path, 2)
    phu = render_slice_png(path, 2, mask)
    assert tran != phu, "phủ mask mà ảnh không đổi là dấu hiệu mask rỗng hoặc lệch"
    assert phu.startswith(bytes([0x89]) + b"PNG")


def test_cache_khong_tron_ban_co_mask_voi_ban_khong(case_dir: Path) -> None:
    """Khoá cache phải gồm cả đường dẫn mask, nếu không hai bản đè lên nhau."""
    path = find_phase_files(case_dir, CASE_ID)["C+V"]
    mask = find_mask_files(case_dir, CASE_ID)["C+V"]
    a1 = render_slice_png(path, 2)
    b1 = render_slice_png(path, 2, mask)
    a2 = render_slice_png(path, 2)  # lấy lại từ cache
    assert a1 == a2 and a1 != b1


def test_mask_lech_hinh_hoc_thi_no(case_dir: Path, tmp_path: Path) -> None:
    """Mask khác lưới với ảnh phải nổ, không được lặng lẽ phủ lệch chỗ."""
    path = find_phase_files(case_dir, CASE_ID)["C+V"]
    lech = _write(tmp_path / "lech.nii", np.ones((8, 8, 3), dtype=np.uint8))
    with pytest.raises(ValueError):
        render_slice_png(path, 2, lech)


# --- lát nào có tổn thương --------------------------------------------------


def test_mask_slice_flags_dung_do_dai_va_dung_lat(case_dir: Path) -> None:
    flags = mask_slice_flags(find_mask_files(case_dir, CASE_ID)["C+V"])
    assert len(flags) == SHAPE[2]
    assert flags == (False, False, True, True, False, False)


def test_mask_slice_flags_duoc_cache(case_dir: Path) -> None:
    """Tính lại mỗi request phải đọc cả khối — cache là điều kiện để dùng được."""
    mask = find_mask_files(case_dir, CASE_ID)["C+V"]
    assert mask_slice_flags(mask) is mask_slice_flags(mask)


def test_mask_rong_thi_toan_false_chu_khong_no(tmp_path: Path) -> None:
    path = _write(tmp_path / "rong.nii", np.zeros((8, 8, 5), dtype=np.uint8))
    flags = mask_slice_flags(path)
    assert len(flags) == 5 and not any(flags)
