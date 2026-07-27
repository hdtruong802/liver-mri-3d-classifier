"""Khoá `configs/baseline_3dpatch.yaml` theo recipe của baseline official.

**Vì sao có file này.** Baseline official LLD-MMRI2023 đạt macro-F1 0.6083 trên
test-104; cấu hình của ta lệch khỏi nó ở 7 chỗ và đạt 0.27. Ba phiên debug trước đó
đều là suy đoán từ đường cong của một model mới chạy 26/300 epoch (WORKLOG S-043).

Mỗi assert dưới đây là **một dòng trong recipe đã được kiểm chứng**, kèm nguồn. File
này tồn tại để việc trôi khỏi recipe phải là hành động có ý thức, không phải một sửa
đổi lặt vặt lọt qua.

Nguồn: https://github.com/LMMMEng/LLD-MMRI2023 — `main/README.md`, `main/train.py`,
`main/datasets/transforms.py`.
"""

import pytest
import yaml
from src.utils.io import load_yaml, repo_root

CONFIG_PATH = "configs/baseline_3dpatch.yaml"


@pytest.fixture
def config() -> dict:
    return load_yaml(repo_root() / CONFIG_PATH)


def test_no_duplicate_keys_in_config():
    """YAML cho phép khoá trùng và lặng lẽ lấy giá trị cuối — đúng cách để mất một run.

    Đã xảy ra thật khi thêm recipe official: `early_stop_patience` xuất hiện hai lần,
    bản `0` bị bản `15` phía dưới đè mất.
    """

    class NoDuplicates(yaml.SafeLoader):
        pass

    def check(loader, node, deep=False):
        seen = set()
        for key_node, _ in node.value:
            key = loader.construct_object(key_node, deep=deep)
            assert key not in seen, f"khoá trùng trong {CONFIG_PATH}: {key!r}"
            seen.add(key)
        return yaml.SafeLoader.construct_mapping(loader, node, deep)

    NoDuplicates.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, check)
    with open(repo_root() / CONFIG_PATH, encoding="utf-8") as f:
        yaml.load(f, NoDuplicates)  # noqa: S506 — loader đã giới hạn ở SafeLoader


def test_schedule_matches_official(config):
    """official: `--epochs 300 --warmup-epochs 5`, best checkpoint của họ @ epoch 216."""
    train = config["train"]
    assert train["epochs"] >= 300, "official train 300 epoch, best @ 216 — cắt ngắn là vô nghĩa"
    assert train["warmup_epochs"] == 5


def test_early_stopping_is_disabled(config):
    """official không early stop. Patience 15 của ta từng dừng ở epoch 26/300."""
    assert config["train"]["early_stop_patience"] == 0


def test_optimizer_matches_official(config):
    """official: `--opt adamw --lr 1e-4 --weight-decay 0.05 --min-lr 1e-5 --warmup-lr 1e-6`."""
    train = config["train"]
    assert train["lr"] == pytest.approx(1e-4)
    assert train["weight_decay"] == pytest.approx(0.05)
    assert train["min_lr"] == pytest.approx(1e-5)
    assert train["warmup_lr"] == pytest.approx(1e-6)


def test_effective_batch_matches_official(config):
    """official: batch 4 × 2 GPU = 8. Ta: batch_size nhỏ vì VRAM, bù bằng accum."""
    effective = config["data"]["batch_size"] * config["train"]["accum_steps"]
    assert effective == 8


def test_loss_is_plain_cross_entropy(config):
    """official: `--smoothing 0` -> `nn.CrossEntropyLoss()`, không class weight."""
    loss = config["loss"]
    assert loss["class_weights"] == "none"
    assert loss["label_smoothing"] == 0


def test_augmentation_matches_official(config):
    """official: lật x/y/z p=0.5, xoay ±10°, random crop. KHÔNG có rot90/nhiễu cường độ."""
    augment = config["data"]["augment"]

    assert augment["flip_prob"] == pytest.approx(0.5)
    assert set(augment["flip_axes"]) == {"x", "y", "z"}
    assert augment["rotate_degrees"] == 10
    assert any(augment["translate_voxels"]), "cần tịnh tiến thay cho random_crop official"

    assert not augment.get("rot90_prob"), "rot90 là thứ ta tự thêm, official không dùng"
    assert not augment.get("intensity_prob"), "nhiễu cường độ là thứ ta tự thêm"


def test_still_not_touching_test_split(config):
    """Mọi thay đổi protocol vẫn phải nằm trong train/val fold (AGENTS.md §3.4)."""
    assert 1 <= config["fold"] <= 5
    assert config.get("splits_dir", "splits") == "splits"
