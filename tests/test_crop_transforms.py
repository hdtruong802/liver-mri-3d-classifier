"""Test cắt ngẫu nhiên / cắt giữa từ cache có lề dư (E12).

Bất biến trung tâm của cả nhóm test này: **khối ra không bao giờ chứa voxel đệm**.
Đó là toàn bộ lý do `RandomCrop3D` tồn tại. `RandomTranslate3D` mà nó thay thế làm
~100% mẫu train mang một dải 0 ở rìa trong khi mẫu val không có, tức lệch phân bố
train/val ở mọi bước huấn luyện.

Phần cắt là thao tác chỉ số thuần nên chạy được với `numpy`; những test đó **không**
skip ở máy phát triển. Chỉ phần cần sinh số ngẫu nhiên qua torch mới skip.
"""

from __future__ import annotations

import numpy as np
import pytest
from src.data.transforms import (
    CenterCrop3D,
    RandomCrop3D,
    build_train_transform,
    build_val_transform,
)

try:
    import torch
except ImportError:  # pragma: no cover - phụ thuộc môi trường
    torch = None

requires_torch = pytest.mark.skipif(torch is None, reason="cần torch")

INNER = (112, 112, 32)
MARGIN = (12, 12, 4)
GRID = tuple(s + 2 * m for s, m in zip(INNER, MARGIN, strict=True))


def _np_volume(shape=(8, *GRID), seed=0):
    """Khối numpy toàn giá trị > 0, để mọi số 0 xuất hiện sau đó đều là đệm."""
    return {"image": np.random.default_rng(seed).random(shape).astype(np.float32) + 1.0}


# --- không cần torch -----------------------------------------------------------


def test_center_crop_lay_dung_giua():
    """Cắt giữa cache có lề PHẢI trùng khối mà cache không lề tạo ra.

    Đây là tính chất khiến val của E12 so trực tiếp được với val của E4. Mất nó thì
    phép so E12–E4 có hai biến chứ không phải một.
    """
    big = _np_volume()["image"]
    out = CenterCrop3D(INNER)({"image": big})["image"]
    expected = big[
        :,
        MARGIN[0] : MARGIN[0] + INNER[0],
        MARGIN[1] : MARGIN[1] + INNER[1],
        MARGIN[2] : MARGIN[2] + INNER[2],
    ]
    np.testing.assert_array_equal(out, expected)


def test_center_crop_tat_dinh():
    item = _np_volume()
    a = CenterCrop3D(INNER)({"image": item["image"]})["image"]
    b = CenterCrop3D(INNER)({"image": item["image"]})["image"]
    np.testing.assert_array_equal(a, b)


def test_center_crop_khong_sinh_voxel_dem():
    out = CenterCrop3D(INNER)(_np_volume())["image"]
    assert tuple(out.shape[1:]) == INNER
    assert (out > 0).all()


def test_khoi_vao_nho_hon_kich_thuoc_cat_thi_bao_loi_ro_rang():
    """Chạy config E12 trên cache E4 cũ phải nổ ngay, kèm lý do đọc được."""
    small = {"image": np.ones((8, *INNER), dtype=np.float32)}
    with pytest.raises(ValueError, match="nhỏ hơn kích thước cắt"):
        CenterCrop3D((128, 128, 40))(small)


def test_kich_thuoc_cat_khong_hop_le_thi_raise():
    for bad in ((112, 112), (112, 112, 0), (-1, 8, 8)):
        with pytest.raises(ValueError, match="3 số dương"):
            CenterCrop3D(bad)


def test_bat_ca_crop_lan_translate_thi_raise():
    """Bật cả hai là nhân đôi phép dịch VÀ đưa đệm 0 trở lại. Phải chặn ở config."""
    with pytest.raises(ValueError, match="nhân đôi phép dịch"):
        build_train_transform({"flip_prob": 0.5, "translate_voxels": [8, 8, 4]}, crop_size=INNER)


def test_crop_dat_sau_xoay():
    """Xoay lấp góc bằng 0; cắt phải đi SAU để vứt đúng phần lấp đó.

    Cắt trước rồi xoay sau sẽ đưa dải đen trở lại, tức mất trắng mục đích của E12.
    """
    t = build_train_transform({"flip_prob": 0.5, "rotate_degrees": 10}, crop_size=INNER)
    names = [type(x).__name__ for x in t.transforms]
    assert names.index("RandomCrop3D") > names.index("RandomRotateSmall")


def test_val_transform_chi_co_cat_giua():
    assert [type(x).__name__ for x in build_val_transform(INNER).transforms] == ["CenterCrop3D"]


def test_khong_co_crop_size_thi_giu_nguyen_hanh_vi_cu():
    """Config cũ (E4 và trước đó) không được đổi hành vi."""
    assert build_val_transform(None) is None
    t = build_train_transform({"flip_prob": 0.5, "translate_voxels": [8, 8, 4]})
    assert [type(x).__name__ for x in t.transforms] == ["RandomFlip", "RandomTranslate3D"]


def test_chi_co_crop_size_ma_khong_co_augment():
    """`crop_size` phải tự nó dựng được transform, kể cả khi khối augment rỗng."""
    t = build_train_transform(None, crop_size=INNER)
    assert [type(x).__name__ for x in t.transforms] == ["RandomCrop3D"]


def test_config_e12_khop_voi_cache_e12():
    """Hai file config phải nhất quán, nếu không thì lỗi chỉ lộ ra giữa job Kaggle."""
    from src.utils.io import load_yaml

    train = load_yaml("configs/e12_randomcrop.yaml")
    pre = load_yaml("configs/preprocess_e12.yaml")
    assert list(train["data"]["crop_size"]) == list(pre["target_size"])
    assert any(pre["crop_margin_voxels"]), "cache E12 phải có lề dư"
    assert not any(train["data"]["augment"]["translate_voxels"]), "phải tắt tịnh tiến"


# --- cần torch (chạy trên Kaggle) ----------------------------------------------


def _t_volume(shape=(8, *GRID)):
    return {"image": torch.ones(shape)}


@requires_torch
def test_random_crop_khong_bao_gio_sinh_voxel_dem():
    crop = RandomCrop3D(INNER)
    for _ in range(50):
        out = crop(_t_volume())["image"]
        assert tuple(out.shape[1:]) == INNER
        assert (out != 0).all(), "có voxel 0 — nghĩa là đang đệm chứ không cắt"


@requires_torch
def test_random_translate_THI_CO_dem_day_la_van_de_dang_sua():
    """Neo hành vi cũ, để thấy rõ E12 sửa cái gì. Không phải test hồi quy hỏng."""
    from src.data.transforms import RandomTranslate3D

    shift = RandomTranslate3D(max_shift=(8, 8, 4), prob=1.0)
    padded = sum(
        bool((shift({"image": torch.ones(8, *INNER)})["image"] == 0).any()) for _ in range(30)
    )
    assert padded >= 25, (
        "RandomTranslate3D phải đệm 0 ở gần như mọi mẫu; test này đỏ nghĩa là hành vi "
        "cũ đã đổi và lý do tồn tại của E12 cần đọc lại"
    )


@requires_torch
def test_random_crop_co_dich_that_su():
    """Nếu offset luôn bằng 0 thì đây không còn là augmentation."""
    big = torch.from_numpy(np.random.default_rng(1).random((8, *GRID)).astype(np.float32))
    crop = RandomCrop3D(INNER)
    seen = {crop({"image": big})["image"][0, 0, 0, 0].item() for _ in range(40)}
    assert len(seen) > 1, "mọi lần cắt cho cùng một offset"


@requires_torch
def test_chuoi_train_day_du_khong_de_lot_voxel_dem():
    """Bài kiểm tổng: lật + xoay 10° + cắt, khối ra vẫn không có voxel bị lấp 0.

    Đây là test chứng minh lề 12 voxel đủ che phần góc mà phép xoay lấp. Đỏ nghĩa là
    phải tăng `crop_margin_voxels`, không phải sửa test.
    """
    t = build_train_transform(
        {
            "flip_prob": 0.5,
            "flip_axes": ["x", "y", "z"],
            "rotate_degrees": 10,
            "rotate_mode": "nearest",
        },
        crop_size=INNER,
    )
    for _ in range(20):
        out = t(_t_volume())["image"]
        assert tuple(out.shape[1:]) == INNER
        assert (out > 0.5).all(), "còn voxel bị xoay lấp 0 lọt vào khối ra"


def test_rotate_mode_constant_VAN_de_lot_o_offset_bien():
    """Ghi lại vì sao E12 buộc phải dùng `nearest`, không phải sở thích.

    Với `constant`, cắt GIỮA thì sạch nhưng cắt NGẪU NHIÊN ở offset biên để lọt tới
    hàng trăm voxel bị lấp 0. Đây là lỗi đã suýt lọt qua: lề 12 voxel đủ cho cắt
    giữa nên nhìn qua tưởng ổn.
    """
    from scipy import ndimage

    grid = INNER[0] + 2 * MARGIN[0]
    rotated = ndimage.rotate(
        np.ones((grid, grid), np.float32),
        angle=10,
        reshape=False,
        order=1,
        mode="constant",
        cval=0.0,
    )
    at_edge = rotated[0 : INNER[0], 0 : INNER[0]]
    at_center = rotated[MARGIN[0] : MARGIN[0] + INNER[0], MARGIN[0] : MARGIN[0] + INNER[0]]
    assert (at_edge < 0.999).sum() > 100, "kỳ vọng offset biên bị lấp nhiều"
    assert (at_center < 0.999).sum() == 0, "cắt giữa phải sạch — đó là chỗ dễ nhầm"
