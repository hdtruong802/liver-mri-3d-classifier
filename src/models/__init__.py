"""Registry model: `configs/*.yaml` chọn kiến trúc bằng tên, code không hardcode.

Mỗi biến thể mới (2.5D ở W2 ngày 6, fusion ở W4) chỉ cần thêm một dòng vào
`_BUILDERS` — vòng train không phải sửa.
"""

from __future__ import annotations

from typing import Any

from src.models.cghnet import build_cghnet
from src.models.densenet3d import build_densenet3d, count_parameters
from src.models.resnet3d import build_resnet3d
from src.models.siamese_fusion import build_siamese_fusion
from src.models.uniformer3d import build_uniformer3d
from src.models.uniformerv2 import build_uniformerv2

_BUILDERS = {
    "densenet121_3d": build_densenet3d,
    "siamese_fusion": build_siamese_fusion,
    "resnet3d": build_resnet3d,
    "cghnet": build_cghnet,
    "uniformer3d": build_uniformer3d,
    "uniformerv2": build_uniformerv2,
}

# Model trả về **dict** ở chế độ train (deep supervision). Vòng train phải biết để lấy
# `main` cho metric và truyền cả dict cho criterion; xem `src/train/loop.py::run_epoch`.
DEEP_SUPERVISION_MODELS = frozenset({"cghnet"})


def build_model(config: dict[str, Any]) -> Any:
    """Dựng model từ khối ``model:`` của config YAML.

    Ví dụ khối config::

        model:
          name: densenet121_3d
          in_channels: 8
          num_classes: 7
          dropout_prob: 0.2
    """
    params = dict(config)
    name = params.pop("name", None)
    if name not in _BUILDERS:
        raise ValueError(f"model.name phải thuộc {sorted(_BUILDERS)}, nhận {name!r}")
    return _BUILDERS[name](**params)


__all__ = [
    "DEEP_SUPERVISION_MODELS",
    "build_cghnet",
    "build_densenet3d",
    "build_model",
    "build_resnet3d",
    "build_siamese_fusion",
    "build_uniformer3d",
    "build_uniformerv2",
    "count_parameters",
]
