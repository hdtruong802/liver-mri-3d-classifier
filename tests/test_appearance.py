"""Test ba augment lọc không gian (`edge` · `emboss` · `filter`) của đội hạng 2 LLD-MMRI 2023.

File **riêng** khỏi `tests/test_transforms.py` vì file kia có `importorskip("torch")` ở mức
module, còn phần đáng neo nhất ở đây chạy trên numpy thuần — nên nó **thật sự chạy ở local**,
nơi dự án không cài torch.

Hai điều file này tồn tại để khoá lại:

1. **Cùng một tham số cho cả 8 pha.** Bài học đắt nhất của dự án (E6, WORKLOG S-102):
   `RandomIntensity` áp scale/shift **độc lập từng pha** làm ICC −0.085 và di căn −0.111, vì
   chẩn đoán u gan dựa vào cường độ *tương đối giữa các pha*.
2. **Mặc định TẮT.** `build_train_transform` là hàm mà mọi thí nghiệm của dự án đi qua. Nếu
   nhóm augment mới tự bật thì mọi con số cũ mất tính so sánh, và điều đó không lộ ra ở đâu.
"""

from __future__ import annotations

import numpy as np
import pytest
from src.data.transforms import (
    RandomAppearance,
    _sigma_4d,
    build_train_transform,
    pil_kernel_filter,
    sobel_magnitude,
    unsharp_mask,
)

SHAPE = (8, 12, 12, 4)  # [pha, X, Y, Z]


def _volume(seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.standard_normal(SHAPE).astype(np.float32)


# --- ràng buộc 1: mọi phép áp GIỐNG NHAU cho 8 pha -------------------------------------


@pytest.mark.parametrize(
    "phep",
    [
        sobel_magnitude,
        lambda a: pil_kernel_filter(a, "emboss"),
        lambda a: pil_kernel_filter(a, "sharpen"),
        lambda a: unsharp_mask(a, spatial_only=True),
    ],
)
def test_hai_pha_giong_nhau_thi_dau_ra_giong_nhau(phep):
    """Đây LÀ ràng buộc y học, không phải chi tiết cài đặt.

    Kernel dạng ``(1, 3, 3, 1)`` bảo đảm điều này **về mặt cấu trúc**, nhưng ai đó đổi sang
    vòng lặp có `rng` bên trong sẽ phá nó mà kết quả nhìn vẫn hợp lý.
    """
    arr = _volume()
    arr[3] = arr[0]  # pha 3 sao chép pha 0
    out = phep(arr)
    assert np.allclose(out[0], out[3], atol=1e-5)


@pytest.mark.parametrize("phep", [sobel_magnitude, lambda a: pil_kernel_filter(a, "emboss")])
def test_chi_tac_dong_trong_mat_phang_XY(phep):
    """Khối chỉ biến thiên theo Z (hằng số trong mặt phẳng) phải cho gradient/emboss bằng 0.

    Bắt được lỗi dùng `ndimage.sobel(axis=...)` — hàm đó làm mượt [1,2,1] dọc **mọi trục
    khác**, tức trộn cả pha lẫn lát, và kết quả nhìn qua vẫn "giống một bản đồ biên".
    """
    arr = np.zeros(SHAPE, dtype=np.float32)
    arr += np.arange(SHAPE[3], dtype=np.float32)  # chỉ biến thiên theo Z
    assert np.allclose(phep(arr), 0.0, atol=1e-5)


# --- kernel phải khớp PIL từng con số ---------------------------------------------------


def test_kernel_khop_dinh_nghia_cua_PIL():
    """Neo lại giá trị lấy từ `PIL/ImageFilter.py`. Sai một số là một phép augment khác."""
    from src.data.transforms import _PIL_KERNELS_3X3

    assert _PIL_KERNELS_3X3["emboss"] == ((-1, 0, 0, 0, 1, 0, 0, 0, 0), 1.0)
    assert _PIL_KERNELS_3X3["sharpen"] == ((-2, -2, -2, -2, 32, -2, -2, -2, -2), 16.0)
    assert _PIL_KERNELS_3X3["detail"] == ((0, -1, 0, -1, 10, -1, 0, -1, 0), 10.0)
    assert _PIL_KERNELS_3X3["edge_enhance"] == ((-1, -1, -1, -1, 10, -1, -1, -1, -1), 2.0)
    assert _PIL_KERNELS_3X3["edge_enhance_more"] == ((-1, -1, -1, -1, 9, -1, -1, -1, -1), 1.0)


def test_emboss_xoa_sach_thanh_phan_DC():
    """Kernel tổng = 0 ⇒ ảnh hằng số ra 0. Nghĩa là **cường độ tuyệt đối biến mất hoàn toàn**
    — phép mạnh nhất trong nhóm, và họ áp nó cho 10% mẫu."""
    assert np.allclose(pil_kernel_filter(np.full(SHAPE, 3.7, np.float32), "emboss"), 0.0)


def test_sharpen_giu_nguyen_anh_hang_so():
    """Kernel tổng 16 chia scale 16 ⇒ gain 1, ảnh phẳng đi qua không đổi."""
    arr = np.full(SHAPE, 3.7, np.float32)
    assert np.allclose(pil_kernel_filter(arr, "sharpen"), arr, atol=1e-4)


def test_kernel_khong_ton_tai_thi_no():
    with pytest.raises(ValueError, match="kernel PIL"):
        pil_kernel_filter(_volume(), "blur")


def test_sobel_khong_am():
    assert (sobel_magnitude(_volume()) >= 0).all()


# --- chỗ dễ hiểu sai nhất: blur/unsharp của họ TRỘN CÁC PHA -----------------------------


def test_sigma_4d_mac_dinh_lam_mo_ca_truc_pha():
    """Tái lập đúng hành vi của họ: `ndimage.gaussian_filter(image_4d, sigma=1)` broadcast σ
    ra **mọi** trục, kể cả trục pha."""
    assert _sigma_4d(1.0, spatial_only=False) == (1.0, 1.0, 1.0, 1.0)
    assert _sigma_4d(1.0, spatial_only=True) == (0.0, 1.0, 1.0, 1.0)


def test_unsharp_mac_dinh_lam_ro_ri_giua_cac_pha():
    """Bằng chứng hành vi cho điều trên, không chỉ là kiểm tuple.

    Chỉ pha 0 khác 0. Với mặc định (trung thực với họ) thì pha 1 **phải** nhiễm tín hiệu; với
    `spatial_only=True` thì không. Đây là ablation MỘT khoá cho giả thuyết đắt nhất của dự án.
    """
    arr = np.zeros(SHAPE, dtype=np.float32)
    arr[0] = 1.0
    assert not np.allclose(unsharp_mask(arr, spatial_only=False)[1], 0.0)
    assert np.allclose(unsharp_mask(arr, spatial_only=True)[1], 0.0, atol=1e-6)


def test_unsharp_dung_cong_thuc_cua_ho_khong_phai_unsharp_chuan():
    """Của họ là ``g₃ + 6·(g₃ − g₁)``, KHÔNG phải ``x + a·(x − g)`` chuẩn. Giữ nguyên vì đó
    là recipe đã cho 0.8078."""
    from scipy import ndimage

    arr = _volume()
    sig = _sigma_4d(1.0, True)
    near = ndimage.gaussian_filter(arr, sigma=sig)
    far = ndimage.gaussian_filter(arr, sigma=_sigma_4d(3.0, True))
    assert np.allclose(unsharp_mask(arr, spatial_only=True), far + 6.0 * (far - near), atol=1e-5)


# --- cây quyết định loại trừ nhau -------------------------------------------------------


def test_mac_dinh_la_TAT():
    """Ràng buộc 2 của module, và phải đúng **về mặt cấu trúc** chứ không nhờ người gọi.

    Bản đầu tiên của lớp này để mặc định bằng giá trị trung thực của repo hạng 2 (0.10 /
    0.10 / 0.40) — tức `RandomAppearance()` trần là ĐANG BẬT. `build_train_transform` khi đó
    vẫn an toàn vì nó truyền `.get(..., 0.0)`, nhưng an toàn kiểu đó là một quy ước, và quy
    ước thì hỏng lặng lẽ. Test này bắt được nó.
    """
    assert RandomAppearance().enabled is False
    assert (
        RandomAppearance().edge_prob,
        RandomAppearance().emboss_prob,
        RandomAppearance().filter_prob,
    ) == (0.0, 0.0, 0.0)


def test_xac_suat_cua_ba_nhanh_khop_cay_cua_ho_khi_duoc_truyen():
    a = RandomAppearance(edge_prob=0.10, emboss_prob=0.10, filter_prob=0.40)
    assert (a.edge_prob, a.emboss_prob, a.filter_prob) == (0.10, 0.10, 0.40)
    assert (a.blur_prob, a.sharpen_prob, a.unsharp_prob) == (0.20, 0.20, 0.10)
    assert a.enabled is True


def test_tong_ba_nhanh_vuot_1_thi_no():
    """Ba nhánh LOẠI TRỪ NHAU (`elif`), nên tổng > 1 là người viết config hiểu sai mô hình."""
    with pytest.raises(ValueError, match="LOẠI TRỪ NHAU"):
        RandomAppearance(edge_prob=0.5, emboss_prob=0.4, filter_prob=0.3)


def test_tong_ba_phep_trong_nhanh_filter_vuot_1_thi_no():
    with pytest.raises(ValueError, match="loại trừ nhau"):
        RandomAppearance(filter_prob=0.4, blur_prob=0.5, sharpen_prob=0.4, unsharp_prob=0.3)


@pytest.mark.parametrize("gia_tri", [-0.1, 1.5])
def test_xac_suat_ngoai_khoang_thi_no(gia_tri: float):
    with pytest.raises(ValueError, match="phải trong"):
        RandomAppearance(edge_prob=gia_tri)


# --- tương thích ngược: build_train_transform -------------------------------------------


def test_config_cu_khong_sinh_ra_RandomAppearance():
    """Con số của E0..E6b phải so được với con số mới. Nếu nhóm này tự bật thì không."""
    chain = build_train_transform({"flip_prob": 0.5, "rotate_degrees": 10})
    assert chain is not None
    assert not any(isinstance(t, RandomAppearance) for t in chain.transforms)


def test_config_co_khoa_thi_sinh_ra_va_nam_o_CUOI():
    """Phải chạy sau `RandomCrop3D`: chạy trước thì kernel liếm vào lề rồi lề bị cắt bỏ."""
    chain = build_train_transform(
        {"flip_prob": 0.5, "rotate_degrees": 10, "edge_prob": 0.1, "filter_prob": 0.4},
        crop_size=(8, 8, 2),
    )
    assert chain is not None
    assert isinstance(chain.transforms[-1], RandomAppearance)


def test_khoa_cua_uniformer_config_di_duoc_toi_transform():
    """Đường từ YAML tới đối tượng phải thông. Sai tên khoá thì augment lặng lẽ không chạy —
    và đó chính là biến ta đang muốn đo."""
    import yaml
    from src.utils.io import repo_root

    cfg = yaml.safe_load((repo_root() / "configs" / "uniformer_s.yaml").read_text("utf-8"))
    chain = build_train_transform(cfg["data"]["augment"], cfg["data"]["crop_size"])
    assert chain is not None
    app = [t for t in chain.transforms if isinstance(t, RandomAppearance)]
    assert len(app) == 1
    assert (app[0].edge_prob, app[0].emboss_prob, app[0].filter_prob) == (0.10, 0.10, 0.40)
    assert app[0].filter_spatial_only is False
