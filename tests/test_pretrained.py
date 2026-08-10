"""Test các cổng chặn của đường pretrained MedicalNet.

Phần dựng mạng cần torch + monai nên không chạy được ở máy này. Thứ test được, và
cũng là thứ đáng test hơn, là **các cổng**: chế độ hỏng của pretrained không phải
crash mà là *im lặng* — model vẫn train, vẫn ra số, chỉ là một phần trọng số ngẫu
nhiên. Một cổng hỏng ở đây không để lại dấu vết nào trong kết quả.
"""

from __future__ import annotations

import pytest
import yaml
from src.models.resnet3d import (
    MEDICALNET_ARGS,
    medicalnet_args,
    resolve_pretrained_path,
    unexpected_missing_keys,
)
from src.utils.io import repo_root

# --- bảng biến thể ------------------------------------------------------------


def test_resnet18_can_shortcut_A():
    """Đây chính là lỗi đã có thật trong config: resnet18 để "B"/false.

    Nguồn: MONAI `get_medicalnet_pretrained_resnet_args` (bias_downsample = depth in
    (18, 34); shortcut_type = "A" nếu depth in (18, 34) ngược lại "B"), khớp với
    README của Tencent/MedicalNet.
    """
    assert medicalnet_args(18) == ("A", True)
    assert medicalnet_args(34) == ("A", True)


def test_cac_do_sau_con_lai_can_shortcut_B():
    for depth in (10, 50, 101, 152, 200):
        assert medicalnet_args(depth) == ("B", False), depth


def test_do_sau_khong_co_thi_no():
    with pytest.raises(ValueError, match="MedicalNet không có resnet"):
        medicalnet_args(19)


def test_bang_khong_rong_va_du_cac_do_sau_medicalnet():
    assert set(MEDICALNET_ARGS) == {10, 18, 34, 50, 101, 152, 200}


# --- cổng "khoá nào thiếu" ----------------------------------------------------


def test_thieu_dau_phan_loai_la_hop_le():
    """MedicalNet là model segmentation (`conv_seg`), không có `fc`, và 7 lớp của ta
    cũng không nhận được đầu cũ dù có. Đây là khoá DUY NHẤT được phép thiếu."""
    assert unexpected_missing_keys(["fc.weight", "fc.bias"]) == []


def test_thieu_downsample_bi_bat():
    """Đúng dấu vết mà `shortcut_type: B` sai để lại.

    Tỉ lệ khớp trong tình huống này khoảng 85%, tức ngưỡng 50% không bắt được. Cổng
    phải dựa trên *khoá nào* thiếu chứ không phải *bao nhiêu* khoá thiếu.
    """
    missing = [
        "fc.weight",
        "fc.bias",
        "layer2.0.downsample.0.weight",
        "layer2.0.downsample.1.weight",
        "layer3.0.downsample.0.weight",
        "layer4.0.downsample.0.weight",
    ]
    assert unexpected_missing_keys(missing) == [
        "layer2.0.downsample.0.weight",
        "layer2.0.downsample.1.weight",
        "layer3.0.downsample.0.weight",
        "layer4.0.downsample.0.weight",
    ]


def test_khong_thieu_gi_thi_rong():
    assert unexpected_missing_keys([]) == []


# --- resolve đường dẫn trọng số -----------------------------------------------


def test_env_thang_config(monkeypatch):
    """Cùng quy ước với LLDMMRI_CACHE_DIR: env thắng, để config không phải ghi cứng
    đường dẫn mount của Kaggle (lớp lỗi đã sửa bốn lần, S-081 → S-084)."""
    monkeypatch.setenv("LLDMMRI_PRETRAINED_PATH", "/mount/that/resnet_18_23dataset.pth")
    got = resolve_pretrained_path("/duong/dan/trong/config.pth")
    assert got is not None
    assert got.name == "resnet_18_23dataset.pth"


def test_khong_env_thi_lay_config(monkeypatch):
    monkeypatch.delenv("LLDMMRI_PRETRAINED_PATH", raising=False)
    got = resolve_pretrained_path("weights/a.pth")
    assert got is not None and got.name == "a.pth"


def test_ca_hai_trong_thi_None(monkeypatch):
    """None nghĩa là from-scratch. Phải phân biệt được với "" để `build_resnet3d`
    còn in được cảnh báo thay vì im lặng bỏ qua pretrained."""
    monkeypatch.delenv("LLDMMRI_PRETRAINED_PATH", raising=False)
    assert resolve_pretrained_path("") is None
    assert resolve_pretrained_path(None) is None


# --- config E8 ----------------------------------------------------------------


def test_config_e8_khop_bang_bien_the():
    """Neo lỗi đã sửa: file này từng ghi shortcut_type B cho resnet18."""
    cfg = yaml.safe_load((repo_root() / "configs" / "e8_pretrained.yaml").read_text("utf-8"))
    model = cfg["model"]
    assert model["name"] == "resnet3d"
    need_shortcut, need_bias = medicalnet_args(int(model["depth"]))
    assert model["shortcut_type"] == need_shortcut
    assert bool(model["bias_downsample"]) is need_bias


def test_config_e8_khong_ghi_cung_duong_dan_kaggle():
    cfg = yaml.safe_load((repo_root() / "configs" / "e8_pretrained.yaml").read_text("utf-8"))
    assert not cfg["model"]["pretrained_path"], (
        "pretrained_path phải để trống và truyền qua LLDMMRI_PRETRAINED_PATH lúc chạy"
    )


def test_moi_config_co_khoi_model_ma_builder_nhan_duoc():
    """Mọi khoá trong `model:` phải là tham số của builder tương ứng.

    Lỗi đã dính thật trên Kaggle: `e8_pretrained.yaml` kế thừa `norm: batch` từ
    baseline, nhưng `build_resnet3d` chưa khai `norm` → `TypeError` ngay ở cell dựng
    model, sau khi đã tốn công mount cache và tải 132 MB trọng số.

    Đây là lớp lỗi *bắt được ở local trong một giây* mà nếu không có test thì chỉ lộ
    ra giữa một session Kaggle. Quét mọi config nên config mới cũng được che.
    """
    import inspect

    from src.models import _BUILDERS

    loi = []
    for path in sorted((repo_root() / "configs").glob("*.yaml")):
        cfg = yaml.safe_load(path.read_text("utf-8")) or {}
        block = cfg.get("model")
        if not isinstance(block, dict) or "name" not in block:
            continue  # configs/preprocess_*.yaml, data.yaml
        builder = _BUILDERS.get(block["name"])
        assert builder is not None, f"{path.name}: model.name {block['name']!r} không có builder"
        nhan = set(inspect.signature(builder).parameters)
        thua = sorted(set(block) - {"name"} - nhan)
        if thua:
            loi.append(f"{path.name} -> {builder.__name__} không nhận {thua}")

    assert not loi, "config mang khoá builder không nhận:\n  " + "\n  ".join(loi)


def test_config_e8_giu_dropout_cho_mc_dropout():
    """ResNet của MONAI không có dropout sẵn. Mất nó là mất bất định epistemic, tức
    mất đóng góp headline của dự án."""
    cfg = yaml.safe_load((repo_root() / "configs" / "e8_pretrained.yaml").read_text("utf-8"))
    assert float(cfg["model"]["dropout_prob"]) > 0
