"""Test registry model + hợp đồng shape của baseline.

Registry là numpy/dict thuần nên test tên model luôn chạy; forward pass cần
torch + monai nên sẽ skip nếu chưa cài.
"""

import pytest
from src.models import build_model


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

    # BatchNorm với batch nhỏ làm val loss phân kỳ (WORKLOG S-036). Nếu ai đó đổi
    # norm về "batch" thì phải đồng thời nâng batch_size lên mức BN dùng được.
    if config["model"].get("norm", "batch") == "batch":
        assert config["data"]["batch_size"] >= 8, (
            "BatchNorm cần batch >= 8; với khối 3D thì dùng norm: instance"
        )
    # Batch hiệu dụng phải nằm trong 16–32 theo ràng buộc Kaggle (AGENTS.md §7).
    effective = config["data"]["batch_size"] * config["train"]["accum_steps"]
    assert 16 <= effective <= 32
