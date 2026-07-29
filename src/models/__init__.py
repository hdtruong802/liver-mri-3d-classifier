"""Registry model: `configs/*.yaml` chọn kiến trúc bằng tên, code không hardcode.

Mỗi biến thể mới (2.5D ở W2 ngày 6, fusion ở W4) chỉ cần thêm một dòng vào
`_BUILDERS` — vòng train không phải sửa.
"""

from __future__ import annotations

from typing import Any

from src.models.densenet3d import build_densenet3d, count_parameters
from src.models.siamese_fusion import build_siamese_fusion

_BUILDERS = {
    "densenet121_3d": build_densenet3d,
    "siamese_fusion": build_siamese_fusion,
}


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


__all__ = ["build_densenet3d", "build_model", "build_siamese_fusion", "count_parameters"]
