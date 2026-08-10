"""Test nhánh encoder pretrained của Siamese (E13).

Phần dựng mạng cần torch + monai nên sẽ skip ở máy này. Thứ test được mà không cần
chúng — và cũng là thứ đáng test hơn — là **các cổng**: một encoder bị hạ mẫu âm thầm,
một cặp `shortcut_type` sai, hay một `embed_dim` bị bỏ qua đều cho ra model chạy được và
số liệu trông hợp lý. E2 chết đúng theo cách đó và mất một tuần mới biết (WORKLOG S-065).
"""

from __future__ import annotations

import inspect

import pytest
import yaml
from src.models import build_model, build_siamese_fusion
from src.models.siamese_fusion import (
    ENCODERS,
    MIN_SPATIAL,
    MIN_SPATIAL_RESNET,
    RESNET_FEATURE_DIM,
    resnet_feature_dim,
)
from src.utils.io import repo_root

CFG_PATH = "configs/e13_siamese_pretrained.yaml"


def _e13() -> dict:
    return yaml.safe_load((repo_root() / CFG_PATH).read_text("utf-8"))


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


def test_e13_khong_ha_mau_dau_vao():
    """Cổng quan trọng nhất. E2 để [2,2,1] và chạy ở 48 in-plane trong khi văn liệu
    dùng 112-128; WORKLOG S-065 kết luận đó là thủ phạm, không phải ý tưởng Siamese."""
    model = _e13()["model"]
    assert model["input_downsample"] == [1, 1, 1], (
        "E13 phải nhận đủ 112x112x32. Hạ mẫu ở đây là lặp lại đúng lỗi của E2."
    )


def test_e13_khop_bien_the_medicalnet():
    from src.models.resnet3d import medicalnet_args

    model = _e13()["model"]
    need_shortcut, need_bias = medicalnet_args(int(model["encoder_depth"]))
    assert model["shortcut_type"] == need_shortcut
    assert bool(model["bias_downsample"]) is need_bias


def test_e13_khong_ghi_cung_duong_dan_kaggle():
    assert not _e13()["model"]["pretrained_path"], (
        "truyền qua LLDMMRI_PRETRAINED_PATH lúc chạy, không ghi cứng đường dẫn mount"
    )


def test_e13_khong_khai_embed_dim():
    assert "embed_dim" not in _e13()["model"]


def test_e13_giu_dropout_cho_mc_dropout():
    assert float(_e13()["model"]["dropout_prob"]) > 0


def test_e13_chi_khac_baseline_trong_khoi_model():
    """E13 là phép đổi kiến trúc. Một khoá lọt sang `data.` hay `train.` biến nó thành
    phép đổi hai cụm biến, và sai đó không để lại dấu vết nào trong kết quả."""

    def flat(d, prefix=""):
        out = {}
        for k, v in d.items():
            name = f"{prefix}{k}"
            out.update(flat(v, name + ".")) if isinstance(v, dict) else out.update({name: v})
        return out

    base = yaml.safe_load((repo_root() / "configs/baseline_3dpatch.yaml").read_text("utf-8"))
    fa, fb = flat(base), flat(_e13())
    ngoai = [
        k
        for k in set(fa) | set(fb)
        if str(fa.get(k)) != str(fb.get(k))
        and not k.startswith("model.")
        and k not in ("output_dir", "fold")
    ]
    assert not ngoai, f"khác baseline NGOÀI khối model: {sorted(ngoai)}"


def test_e13_giu_recipe_official_tung_chu_so():
    """Recipe train phải trùng khít baseline — nếu không thì E13 so E4 là hai biến."""
    base = yaml.safe_load((repo_root() / "configs/baseline_3dpatch.yaml").read_text("utf-8"))
    e13 = _e13()
    assert e13["train"] == base["train"]
    assert e13["loss"] == base["loss"]
    assert e13["data"] == base["data"]
    assert e13["seed"] == base["seed"]


# --- hồi quy cho nhánh DenseNet cũ ---------------------------------------------


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


def test_e13_dung_that_va_khong_ha_mau():
    """Phép kiểm cuối: dựng đúng khối config của E13 rồi cho một batch thật đi qua.

    Ba điều nó khẳng định, và cả ba đều là chỗ E2 hoặc E8 đã sai:

    1. ``pre_pool`` là ``Identity`` — encoder nhận đủ 112×112×32, không hạ mẫu.
    2. Đặc trưng đúng 512 chiều, tức `feed_forward=False` có tác dụng và
       `phase_embedding`/`attention` được dựng ở cùng số chiều với encoder.
    3. Trọng số attention có 8 phần tử và tổng bằng 1 trên trục thì.
    """
    torch = pytest.importorskip("torch", reason="dựng mạng cần torch")
    pytest.importorskip("monai", reason="ResNet-3D lấy từ MONAI")

    model = build_model(_e13()["model"])  # pretrained_path trống -> from scratch
    model.eval()

    assert isinstance(model.pre_pool, torch.nn.Identity), (
        "pre_pool không phải Identity -> encoder đang bị hạ mẫu, đúng lỗi của E2"
    )
    assert model.embed_dim == 512

    x = torch.zeros(2, 8, 112, 112, 32)
    with torch.no_grad():
        y = model(x)
    assert tuple(y.shape) == (2, 7)

    weights = model.last_phase_weights
    assert weights is not None and tuple(weights.shape) == (2, 8)
    torch.testing.assert_close(weights.sum(dim=1), torch.ones(2))


def test_encoder_nhan_dung_mot_kenh():
    """Trọng số MedicalNet là một kênh. Encoder phải nhận đúng 1, không phải 8 —
    đó chính là chỗ Siamese tốt hơn early-concat ở đây."""
    pytest.importorskip("torch", reason="dựng mạng cần torch")
    pytest.importorskip("monai", reason="ResNet-3D lấy từ MONAI")

    model = build_model(_e13()["model"])
    assert model.encoder.conv1.in_channels == 1, (
        "conv đầu của encoder phải nhận 1 kênh; 8 kênh nghĩa là đang chạy early-concat"
    )
