"""Test các cổng của nhánh encoder pretrained trong `siamese_fusion`.

Phần dựng mạng cần torch + monai nên sẽ skip ở máy này. Thứ test được mà không cần
chúng — và cũng là thứ đáng test hơn — là **các cổng**: một encoder bị hạ mẫu âm thầm,
một cặp `shortcut_type` sai, hay một `embed_dim` bị bỏ qua đều cho ra model chạy được và
số liệu trông hợp lý. E2 chết đúng theo cách đó và mất một tuần mới biết (WORKLOG S-065).

⚠️ Các test bám `configs/e13_siamese_pretrained.yaml` đã bỏ cùng config đó ở WORKLOG
S-197 — E13 chạy rồi bị loại và không có mặt trong báo cáo cuối. Phần còn lại kiểm chính
module, vốn vẫn sống vì `configs/e2_siamese.yaml` dùng nó.
"""

from __future__ import annotations

import inspect

import pytest
import yaml
from src.models import build_siamese_fusion
from src.models.siamese_fusion import (
    ENCODERS,
    MIN_SPATIAL,
    MIN_SPATIAL_RESNET,
    RESNET_FEATURE_DIM,
    resnet_feature_dim,
)
from src.utils.io import repo_root

# --- số chiều đặc trưng --------------------------------------------------------


def test_resnet18_cho_512_chieu():
    """``block_inplanes[3] * expansion``; BasicBlock (10/18/34) expansion 1."""
    assert resnet_feature_dim(18) == 512
    assert resnet_feature_dim(34) == 512
    assert resnet_feature_dim(50) == 2048  # Bottleneck expansion 4


def test_do_sau_chua_biet_thi_no():
    with pytest.raises(ValueError, match="chưa biết số chiều"):
        resnet_feature_dim(200)


def test_bang_do_sau_khong_rong():
    assert set(RESNET_FEATURE_DIM) >= {10, 18, 34}


# --- cổng tham số, chạy được KHÔNG cần torch -----------------------------------


def test_encoder_la_ngan_chan_truoc_khi_import_torch():
    """Cấu hình sai phải nổ ở local, không phải giữa một session Kaggle."""
    with pytest.raises(ValueError, match="encoder phải thuộc"):
        build_siamese_fusion(encoder="vit3d")
    assert ENCODERS == ("densenet121_3d", "resnet3d")


def test_embed_dim_khong_phai_tham_so_tu_do_voi_resnet():
    """Encoder chạy `feed_forward=False` nên số chiều do kiến trúc quyết định.

    Bỏ qua âm thầm thì `phase_embedding` và `attention` dựng ở 256 chiều trong khi
    encoder trả 512, và lỗi chỉ lộ ra ở dòng cộng tensor — rất muộn và rất khó đọc.
    """
    with pytest.raises(ValueError, match="embed_dim"):
        build_siamese_fusion(encoder="resnet3d", encoder_depth=18, embed_dim=256)


def test_input_downsample_van_bi_kiem():
    with pytest.raises(ValueError, match="input_downsample"):
        build_siamese_fusion(encoder="resnet3d", input_downsample=[1, 1])


# --- ngưỡng hình học ------------------------------------------------------------


def test_nguong_resnet_khac_nguong_densenet():
    """Dùng chung một hằng số là chỗ đã buộc E2 hạ mẫu xuống 48 in-plane.

    DenseNet121 hạ mẫu 5 lần và transition cuối cần >= 2 voxel, nên đòi >= 32.
    ResNet hạ mẫu 16 lần rồi adaptive-pool nên chỉ cần >= 16.
    """
    assert MIN_SPATIAL == 32
    assert MIN_SPATIAL_RESNET == 16
    assert MIN_SPATIAL_RESNET < MIN_SPATIAL


# --- config E13 -----------------------------------------------------------------


def test_e2_densenet_khong_doi_hanh_vi():
    """`embed_dim` đổi từ `int = 256` sang `int | None = None`. E2 khai 256 tường minh
    nên vẫn phải ra đúng mạng cũ."""
    e2 = yaml.safe_load((repo_root() / "configs/e2_siamese.yaml").read_text("utf-8"))
    assert e2["model"]["embed_dim"] == 256
    assert e2["model"].get("encoder", "densenet121_3d") == "densenet121_3d"
    nhan = set(inspect.signature(build_siamese_fusion).parameters)
    assert set(e2["model"]) - {"name"} <= nhan


def test_mac_dinh_van_la_densenet():
    """Thêm nhánh resnet không được đổi mặc định của hàm."""
    params = inspect.signature(build_siamese_fusion).parameters
    assert params["encoder"].default == "densenet121_3d"
    assert params["embed_dim"].default is None


# --- dựng thật, chỉ chạy nơi có torch + monai (Kaggle) ------------------------
