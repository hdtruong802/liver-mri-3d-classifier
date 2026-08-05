"""Test lớp đọc/vẽ Grad-CAM của web app.

Chạy trên `.npz` giả trong `tmp_path` — **không cần torch**, đúng ràng buộc của backend
(AGENTS.md §4). Phần tính bản đồ (cần torch) test ở `tests/test_xai_gradcam.py`.
"""

from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("PIL", reason="lớp serve chưa cài")

from webapp.backend import gradcam  # noqa: E402

SHAPE = (12, 12, 6)


def _write(directory: Path, pid: str, *, wrong: bool = False, true_status: str = "") -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(abs(hash(pid)) % 2**32)
    payload = {
        "cam_pred": rng.random(SHAPE).astype(np.float16),
        "crop_ref": (rng.random(SHAPE) * 255).astype(np.uint8),
        "phase_importance": (lambda v: v / v.sum())(rng.random(8)).astype(np.float32),
        "pred_index": np.int64(3),
        "true_index": np.int64(1 if wrong else 3),
        "fold": np.str_("fold_2"),
        "layer": np.str_("denseblock3"),
        "cam_native_shape": np.asarray([7, 7, 2], dtype=np.int64),
        "cam_true_status": np.str_(true_status or ("ok" if wrong else "khong-can")),
    }
    if wrong and (true_status or "ok") == "ok":
        payload["cam_true"] = rng.random(SHAPE).astype(np.float16)
    path = directory / f"{pid}.npz"
    np.savez_compressed(path, **payload)
    return path


@pytest.fixture(autouse=True)
def _clear_cache():
    gradcam.load_all.cache_clear()
    gradcam._png_cache.clear()
    yield
    gradcam.load_all.cache_clear()
    gradcam._png_cache.clear()


@pytest.fixture
def store(tmp_path: Path) -> str:
    _write(tmp_path, "MR001")
    _write(tmp_path, "MR002", wrong=True)
    return str(tmp_path)


def test_thu_muc_khong_ton_tai_thi_rong_chu_khong_no(tmp_path: Path) -> None:
    """App phải xuống thang tử tế khi chưa chạy notebook — đây là trạng thái mặc định."""
    assert gradcam.load_all(str(tmp_path / "chua-co")) == {}
    assert gradcam.get("MR001", str(tmp_path / "chua-co")) is None


def test_nap_dung_so_ca_va_sieu_du_lieu(store: str) -> None:
    cam = gradcam.get("MR001", store)
    assert cam is not None
    assert cam.n_slices == SHAPE[2]
    assert cam.native_shape == (7, 7, 2)
    assert cam.layer == "denseblock3" and cam.fold == "fold_2"


def test_doan_dung_thi_KHONG_co_ban_do_lop_that(store: str) -> None:
    """`target='true'` chỉ có nghĩa khi mô hình sai. Trả bản đồ khác đi là nói dối."""
    cam = gradcam.get("MR001", store)
    assert cam.map_for("true") is None
    with pytest.raises(KeyError):
        gradcam.render_png(cam, "true", 0)


def test_doan_sai_thi_co_ca_hai_ban_do_va_chung_khac_nhau(store: str) -> None:
    cam = gradcam.get("MR002", store)
    assert cam.map_for("true") is not None
    a = gradcam.render_png(cam, "pred", 2)
    b = gradcam.render_png(cam, "true", 2)
    assert a != b, "hai lớp cho cùng một ảnh nghĩa là target không được dùng"


def test_target_la_khong_hop_le_thi_no(store: str) -> None:
    with pytest.raises(ValueError, match="target"):
        gradcam.get("MR001", store).map_for("khong-ton-tai")


def test_lat_ngoai_khoang_thi_no(store: str) -> None:
    cam = gradcam.get("MR001", store)
    for bad in (-1, SHAPE[2]):
        with pytest.raises(IndexError):
            gradcam.render_png(cam, "pred", bad)


def test_render_ra_PNG_hop_le(store: str) -> None:
    payload = gradcam.render_png(gradcam.get("MR001", store), "pred", 3)
    assert payload.startswith(bytes([0x89]) + b"PNG")


def test_cache_khong_tron_hai_target(store: str) -> None:
    """Khoá cache phải gồm target; thiếu nó thì bản này đè bản kia."""
    cam = gradcam.get("MR002", store)
    a1 = gradcam.render_png(cam, "pred", 1)
    b1 = gradcam.render_png(cam, "true", 1)
    a2 = gradcam.render_png(cam, "pred", 1)
    assert a1 == a2 and a1 != b1


def test_chan_cam_lech_hinh_hoc_so_voi_anh_nen(tmp_path: Path) -> None:
    """Phủ lệch nhau còn tệ hơn không phủ — phải nổ lúc nạp, không phải lúc vẽ."""
    np.savez_compressed(
        tmp_path / "MR009.npz",
        cam_pred=np.zeros((4, 4, 4), dtype=np.float16),
        crop_ref=np.zeros((8, 8, 8), dtype=np.uint8),
        phase_importance=np.full(8, 0.125, dtype=np.float32),
        pred_index=np.int64(0),
        fold=np.str_("fold_1"),
        layer=np.str_("denseblock3"),
        cam_native_shape=np.asarray([2, 2, 2], dtype=np.int64),
    )
    with pytest.raises(ValueError, match="khác ảnh nền"):
        gradcam.load_all(str(tmp_path))


def test_case_detail_bao_available_false_khi_chua_co(tmp_path: Path, monkeypatch) -> None:
    from webapp.backend import demo_cases

    monkeypatch.setattr(gradcam, "GRADCAM_DIR", tmp_path / "chua-co")
    gradcam.load_all.cache_clear()
    info = demo_cases.get_case_detail(demo_cases.DEMO_CASES[0].case_id).gradcam
    assert info is not None and info.available is False
    assert "10_gradcam" in info.note, "phải chỉ ra cách tạo dữ liệu, không chỉ báo thiếu"


def test_ban_do_lop_that_suy_bien_duoc_ghi_nhan_chu_khong_mat_tich(tmp_path: Path) -> None:
    """Ca `MR207769` thật: model đoán sai VÀ không có voxel nào ủng hộ lớp đúng.

    Trạng thái đó phải đi ra tới API. Nếu chỉ thiếu `cam_true` mà không kèm lý do thì
    UI không phân biệt được "chưa tính" với "đã tính, và kết quả là không có gì" —
    hai điều rất khác nhau về mặt khoa học.
    """
    _write(tmp_path, "MR207769", wrong=True, true_status="suy-bien")
    cam = gradcam.get("MR207769", str(tmp_path))

    assert cam.true_status == "suy-bien"
    assert cam.map_for("true") is None
    assert gradcam.render_png(cam, "pred", 2), "bản đồ lớp đã đoán vẫn phải render được"


def test_npz_cu_khong_co_truong_trang_thai_van_nap_duoc(tmp_path: Path) -> None:
    """Tương thích ngược: `.npz` sinh trước S-097 không có `cam_true_status`."""
    np.savez_compressed(
        tmp_path / "MR008.npz",
        cam_pred=np.zeros(SHAPE, dtype=np.float16),
        crop_ref=np.zeros(SHAPE, dtype=np.uint8),
        phase_importance=np.full(8, 0.125, dtype=np.float32),
        pred_index=np.int64(0),
        fold=np.str_("fold_1"),
        layer=np.str_("denseblock3"),
        cam_native_shape=np.asarray([7, 7, 2], dtype=np.int64),
    )
    assert gradcam.get("MR008", str(tmp_path)).true_status == "khong-can"
