"""Hai run khác kiến trúc không bao giờ được dùng chung thư mục checkpoint.

Lỗi thật đã gặp (WORKLOG S-038): `last.pt` của bản BatchNorm nằm sẵn trong
`fold1/`, bản InstanceNorm chạy sau nạp phải nó và nổ giữa `load_state_dict`.
Chốt kiểm fingerprint lúc resume là lưới thứ hai; lưới thứ nhất — và là lưới
thật sự chặn được — là tách thư mục theo hash kiến trúc.
"""

from pathlib import Path

from src.train.run import model_fingerprint, run_dir

BASE = {
    "output_dir": "artifacts/runs/x",
    "model": {"name": "densenet121_3d", "in_channels": 8, "num_classes": 7},
}


def _with_model(**overrides) -> dict:
    return {**BASE, "model": {**BASE["model"], **overrides}}


def test_same_config_gives_same_dir():
    """Resume của một run bị ngắt phải quay lại đúng chỗ cũ."""
    assert run_dir(BASE, 1) == run_dir(dict(BASE), 1)


def test_batchnorm_and_instancenorm_never_share_a_dir():
    batch = _with_model(norm="batch")
    instance = _with_model(norm=["instance", {"affine": True}])
    assert run_dir(batch, 1) != run_dir(instance, 1)


def test_instance_norm_with_and_without_affine_differ():
    """affine=False là kiến trúc khác (mất scale/shift) — không được lẫn checkpoint."""
    with_affine = _with_model(norm=["instance", {"affine": True}])
    without = _with_model(norm="instance")
    assert run_dir(with_affine, 1) != run_dir(without, 1)


def test_folds_are_separate():
    assert run_dir(BASE, 1) != run_dir(BASE, 2)


def test_non_model_hyperparams_keep_the_same_dir():
    """Đổi lr/epochs vẫn phải resume được — mất tiến trình trên Kaggle là mất thật."""
    a = {**BASE, "train": {"lr": 0.0003, "epochs": 60}}
    b = {**BASE, "train": {"lr": 0.001, "epochs": 120}}
    assert run_dir(a, 1) == run_dir(b, 1)


def test_dir_name_is_readable_and_stable():
    path = run_dir(BASE, 3)
    assert path.name.startswith("fold3_")
    assert len(path.name.split("_")[1]) == 8
    assert path == run_dir(BASE, 3)


def test_fingerprint_ignores_key_order():
    a = {"name": "densenet121_3d", "num_classes": 7}
    b = {"num_classes": 7, "name": "densenet121_3d"}
    assert model_fingerprint(a) == model_fingerprint(b)


def test_dir_sits_under_configured_output_dir(tmp_path: Path):
    config = {**BASE, "output_dir": str(tmp_path)}
    assert run_dir(config, 1).parent == tmp_path
