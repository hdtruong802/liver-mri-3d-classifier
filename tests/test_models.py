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
        # Khối nhỏ hơn 96×96×48 thật để test chạy nhanh, NHƯNG không nhỏ tuỳ ý:
        # DenseNet121-3D hạ mẫu 5 lần nên mọi chiều phải >= 32. Test này từng dùng
        # 32×32×16 và **luôn skip ở local vì thiếu torch**, nên lỗi chỉ lộ ra khi
        # chạy thật trên Kaggle (WORKLOG S-063).
        logits = model(torch.randn(2, 8, 32, 32, 32))

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


# --- E2: Siamese đa pha ------------------------------------------------------


def test_siamese_rejects_unknown_fusion():
    from src.models.siamese_fusion import build_siamese_fusion

    with pytest.raises(ValueError, match="fusion"):
        build_siamese_fusion(fusion="không-tồn-tại")


@pytest.mark.parametrize("bad", [0, -1, (2, 2), (2, 2, 0)])
def test_siamese_rejects_bad_downsample(bad):
    from src.models.siamese_fusion import build_siamese_fusion

    with pytest.raises(ValueError, match="input_downsample"):
        build_siamese_fusion(input_downsample=bad)


def test_siamese_default_downsample_keeps_z_axis():
    """Mặc định phải là (2, 2, 1) — hạ mẫu đều SẬP trên dữ liệu thật.

    96×96×48 chia đều cho 2 thành 48×48×24, mà 24 không sống nổi qua 5 lần hạ mẫu
    của DenseNet121-3D. Trục Z chỉ có 48 voxel ngay từ đầu (WORKLOG S-063).
    """
    import inspect

    from src.models.siamese_fusion import build_siamese_fusion

    default = inspect.signature(build_siamese_fusion).parameters["input_downsample"].default
    assert tuple(default) == (2, 2, 1)


def test_siamese_refuses_input_too_small_after_downsampling():
    """Báo lỗi rõ ràng thay vì để MONAI ném RuntimeError từ sâu trong mạng.

    Đây đúng là cấu hình sẽ chạy thật: khối 96×96×48 với hạ mẫu đều 2 cho 48×48×24,
    và chiều 24 làm sập transition layer thứ ba.
    """
    torch = pytest.importorskip("torch", reason="forward pass cần torch")
    pytest.importorskip("monai")

    model = build_model(
        {"name": "siamese_fusion", "embed_dim": 32, "fusion": "mean", "input_downsample": 2}
    )
    model.eval()
    with pytest.raises(ValueError, match="DenseNet121-3D cần"), torch.no_grad():
        model(torch.randn(1, 8, 96, 96, 48))


def test_siamese_real_input_shape_works_with_default_downsample():
    """Hợp đồng với dữ liệu THẬT: 96×96×48 và hệ số mặc định phải chạy trót lọt."""
    torch = pytest.importorskip("torch", reason="forward pass cần torch")
    pytest.importorskip("monai")

    model = build_model({"name": "siamese_fusion", "embed_dim": 32, "fusion": "attention"})
    model.eval()
    with torch.no_grad():
        logits = model(torch.randn(1, 8, 96, 96, 48))
    assert logits.shape == (1, 7)
    assert torch.isfinite(logits).all()


@pytest.mark.parametrize("fusion", ["attention", "mean", "concat"])
def test_siamese_maps_8_phases_to_7_classes(fusion):
    torch = pytest.importorskip("torch", reason="forward pass cần torch")
    pytest.importorskip("monai", reason="DenseNet121-3D lấy từ MONAI")

    # Khối 32³ là mức nhỏ nhất DenseNet121-3D chịu được; hạ mẫu 1 để test nhanh.
    # Đường hạ mẫu có test riêng ở trên với kích thước thật.
    model = build_model(
        {
            "name": "siamese_fusion",
            "num_phases": 8,
            "num_classes": 7,
            "embed_dim": 32,
            "fusion": fusion,
            "input_downsample": 1,
        }
    )
    model.eval()
    with torch.no_grad():
        logits = model(torch.randn(2, 8, 32, 32, 32))

    assert logits.shape == (2, 7)
    assert torch.isfinite(logits).all()


def test_siamese_shares_one_encoder_across_phases():
    """Trọng số DÙNG CHUNG là cả điểm của thiết kế.

    Tám encoder riêng là tám lần số tham số, gần như chắc chắn overfit với 316 mẫu
    train. Kiểm bằng cách đổi số thì: số tham số của encoder KHÔNG được đổi theo.
    """
    pytest.importorskip("torch", reason="đếm tham số cần torch")
    pytest.importorskip("monai")
    from src.models import count_parameters

    four = build_model(
        {
            "name": "siamese_fusion",
            "num_phases": 4,
            "embed_dim": 32,
            "fusion": "mean",
            "phase_embedding": False,
        }
    )
    eight = build_model(
        {
            "name": "siamese_fusion",
            "num_phases": 8,
            "embed_dim": 32,
            "fusion": "mean",
            "phase_embedding": False,
        }
    )
    assert count_parameters(four.encoder) == count_parameters(eight.encoder)
    assert count_parameters(four) == count_parameters(eight)


def test_siamese_attention_weights_are_a_distribution_over_phases():
    """Trọng số attention là đầu ra khoa học, không phải chi tiết nội bộ.

    Đây chính là số dùng cho ablation phase-importance ở W4 và để đối chiếu với
    LI-RADS (kỳ vọng arterial/venous nổi bật).
    """
    torch = pytest.importorskip("torch", reason="forward pass cần torch")
    pytest.importorskip("monai")

    model = build_model(
        {"name": "siamese_fusion", "embed_dim": 32, "fusion": "attention", "input_downsample": 1}
    )
    model.eval()
    with torch.no_grad():
        model(torch.randn(3, 8, 32, 32, 32))

    weights = model.last_phase_weights
    assert weights.shape == (3, 8)
    assert torch.allclose(weights.sum(dim=1), torch.ones(3), atol=1e-5)
    assert (weights >= 0).all()


def test_siamese_rejects_wrong_phase_count():
    torch = pytest.importorskip("torch", reason="forward pass cần torch")
    pytest.importorskip("monai")

    model = build_model({"name": "siamese_fusion", "num_phases": 8, "embed_dim": 32})
    model.eval()
    with pytest.raises(ValueError, match="thì"), torch.no_grad():
        model(torch.randn(2, 5, 32, 32, 16))


def test_e2_config_differs_from_e1_only_in_model_block():
    """So sánh có kiểm soát: E2 vs E1 chỉ được khác ĐÚNG kiến trúc.

    Nếu test này đỏ thì kết quả E2 không còn quy về kiến trúc được nữa.
    """
    from src.utils.io import load_yaml

    e1 = load_yaml("configs/baseline_3dpatch.yaml")
    e2 = load_yaml("configs/e2_siamese.yaml")
    differing = {k for k in set(e1) | set(e2) if e1.get(k) != e2.get(k)}
    assert differing == {"model", "output_dir"}, (
        f"khác ngoài dự kiến: {differing - {'model', 'output_dir'}}"
    )
    assert e2["model"]["name"] == "siamese_fusion"
    assert e2["model"]["num_classes"] == e1["model"]["num_classes"]


# --- Ràng buộc hình học giữa cache và backbone -------------------------------


def test_every_preprocess_config_fits_densenet_minimum():
    """`target_size` của MỌI cache phải >= 32 ở mọi chiều.

    DenseNet121-3D hạ mẫu 5 lần; dưới ngưỡng này nó chết bằng `RuntimeError` sâu
    trong transition layer, không nói gì về nguyên nhân (WORKLOG S-063). Test này
    tồn tại vì hình học 16 lát của CGHNet nghe rất hấp dẫn nhưng **không dùng
    được với backbone hiện tại** — họ dùng ViT + CNN, ta dùng DenseNet.
    """

    from src.models.siamese_fusion import MIN_SPATIAL
    from src.utils.io import load_yaml, repo_root

    configs = sorted((repo_root() / "configs").glob("preprocess*.yaml"))
    assert configs, "không tìm thấy config tiền xử lý nào"
    for path in configs:
        size = load_yaml(path)["target_size"]
        assert all(d >= MIN_SPATIAL for d in size), (
            f"{path.name}: target_size {size} có chiều < {MIN_SPATIAL}, DenseNet121-3D sẽ sập"
        )


def test_preprocess_configs_write_to_separate_caches():
    """Mỗi hình học phải có cache_dir riêng.

    `build_cache` có resume (bỏ qua ca đã có `.npz`). Hai config trỏ chung một
    thư mục sẽ TRỘN hai hình học vào cùng một mẻ, và không có gì trong file cảnh
    báo điều đó.
    """
    from pathlib import Path

    from src.utils.io import load_yaml, repo_root

    configs = sorted((repo_root() / "configs").glob("preprocess*.yaml"))
    seen: dict[str, Path] = {}
    for path in configs:
        cache_dir = load_yaml(path)["cache_dir"]
        assert cache_dir not in seen, (
            f"{path.name} và {seen[cache_dir].name} cùng ghi vào {cache_dir!r}"
        )
        seen[cache_dir] = path


def test_e3_geometry_matches_published_in_plane_size():
    """E3 tồn tại để khớp hình học của văn liệu, nên khoá lại con số đó.

    Baseline official crop 112x112x14; CGHNet resize 16x128x128 rồi crop
    14x112x112. Cả hai dùng in-plane 112 sau crop. Z=32 là nhượng bộ với
    DenseNet, không phải lựa chọn khoa học — ghi rõ để không ai tưởng 32 là con
    số văn liệu.
    """
    from src.utils.io import load_yaml

    size = load_yaml("configs/preprocess_e3.yaml")["target_size"]
    assert size[0] == size[1] == 112, "in-plane phải là 112, khớp baseline official và CGHNet"
    assert size[2] == 32, "Z=32 là mức thấp nhất DenseNet chịu được"
