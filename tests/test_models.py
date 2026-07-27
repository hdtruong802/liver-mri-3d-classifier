"""Test registry model + hợp đồng shape của baseline.

Registry là numpy/dict thuần nên test tên model luôn chạy; forward pass cần
torch + monai nên sẽ skip nếu chưa cài.
"""

import pytest
from src.models import build_model
from src.models.densenet3d import DEFAULT_NORM, normalize_norm_spec


def test_default_norm_is_the_one_with_evidence():
    """Mặc định phải là phương án có số thật, không phải phương án nghe hợp lý.

    `instance` từng là mặc định và **sập** (macro-F1 0.0668 đứng yên, WORKLOG S-039);
    `batch` là lựa chọn duy nhất đã cho macro-F1 val 0.2725.
    """
    assert DEFAULT_NORM == "batch"


def test_norm_spec_from_yaml_list_becomes_tuple():
    """YAML không có tuple: `norm: [instance, {affine: true}]` đọc ra list."""
    assert normalize_norm_spec(["instance", {"affine": True}]) == ("instance", {"affine": True})
    assert normalize_norm_spec("batch") == "batch"


def test_unknown_model_name_rejected():
    with pytest.raises(ValueError, match="model.name"):
        build_model({"name": "resnet-không-tồn-tại"})


def test_missing_model_name_rejected():
    with pytest.raises(ValueError, match="model.name"):
        build_model({"in_channels": 8})


def test_densenet3d_maps_8_phases_to_7_classes():
    torch = pytest.importorskip("torch", reason="forward pass cần torch")
    pytest.importorskip("monai", reason="DenseNet121-3D lấy từ MONAI")
    from src.models import count_parameters

    model = build_model(
        {"name": "densenet121_3d", "in_channels": 8, "num_classes": 7, "dropout_prob": 0.2}
    )
    model.eval()
    with torch.no_grad():
        # Khối nhỏ hơn 96×96×48 thật để test chạy nhanh; DenseNet không cố định kích thước.
        logits = model(torch.randn(2, 8, 32, 32, 16))

    assert logits.shape == (2, 7)
    assert torch.isfinite(logits).all()
    assert count_parameters(model) > 0


def test_config_yaml_matches_model_contract():
    """Config baseline phải khớp taxonomy 7 lớp và 8 pha — bắt lệch sớm."""
    from src.data.taxonomy import NUM_CLASSES
    from src.models.densenet3d import IN_CHANNELS
    from src.utils.io import load_yaml

    config = load_yaml("configs/baseline_3dpatch.yaml")
    assert config["model"]["num_classes"] == NUM_CLASSES
    assert config["model"]["in_channels"] == IN_CHANNELS
    assert 1 <= config["fold"] <= 5

    # `norm` phải được khai báo tường minh — mặc định của MONAI là "batch" và một
    # lựa chọn ngầm ở đây từng tốn hai run GPU để phát hiện (WORKLOG S-036, S-039).
    assert "norm" in config["model"], "khai báo norm tường minh, đừng dựa vào mặc định"

    # Với instance/group thì affine PHẢI bật: nn.InstanceNorm3d và nn.GroupNorm đều
    # có thể chạy affine=False, và khi đó mọi lớp norm mất scale/shift học được.
    norm = normalize_norm_spec(config["model"]["norm"])
    if not isinstance(norm, str):
        name, args = norm
        assert name in {"instance", "group"}
        assert args.get("affine") is True, f"{name} không affine = mất scale/shift học được"
    # Batch hiệu dụng: trần 32 là ràng buộc VRAM (AGENTS.md §7).
    # Giá trị chính xác do `tests/test_protocol_conformance.py` khoá theo recipe
    # official. Ở đây từng có thêm ràng buộc "≥ 40 bước cập nhật/epoch" — nó mã hoá
    # giả thuyết "thiếu bước cập nhật" của S-040, mà giả thuyết đó **đã bị bác bỏ**
    # bằng thực nghiệm ở S-041 (gấp 4 lần số bước, kết quả không đổi).
    effective = config["data"]["batch_size"] * config["train"]["accum_steps"]
    assert 2 <= effective <= 32
