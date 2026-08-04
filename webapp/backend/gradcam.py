"""Đọc bản đồ Grad-CAM đã tính sẵn và render ra PNG. Không cần torch.

Cùng khuôn với `webapp/backend/predictions.py`: phần cần deep-learning stack chạy
**offline trên Kaggle** (`notebooks/10_gradcam.ipynb`), backend chỉ đọc `.npz` và vẽ.
Backend bị ràng buộc không kéo theo torch/monai (AGENTS.md §4).

## Ảnh ở đây KHÁC ảnh ở bộ xem chính

Bộ xem chính hiển thị lát gốc 480×480. Mô hình **chưa từng thấy ảnh đó**: nó nhận một
khối 112×112×32 đã cắt bám tổn thương và căn từng thì (`configs/preprocess_e4.yaml`).
Bản đồ chú ý vì thế sống trong không gian crop, và ảnh nền đi kèm cũng phải là crop.
Phủ nó lên lát gốc sẽ là một tuyên bố sai về những gì mô hình nhìn thấy.

## Đây là phỏng đoán của mô hình, không phải nhãn của người

Đừng lẫn với mask tổn thương (`webapp/backend/volumes.py`): mask là vùng **người chú
giải khoanh** — ground truth. Bản đồ này là chỗ **mô hình nhạy** — có thể sai hoàn
toàn, và với ca mô hình đoán sai thì nó *nên* trông sai. Hai thứ dùng hai màu tách
biệt hẳn (`annotation` fuchsia so với `attention` hổ phách) chính vì lẫn chúng là
hiểu nhầm tệ nhất mà app này có thể gây ra.
"""

from __future__ import annotations

import functools
import io
import os
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

from webapp.backend.config import REPO_ROOT

GRADCAM_DIR: Path = Path(
    os.environ.get("LLDMMRI_GRADCAM_DIR", REPO_ROOT / "runs" / "E4_per_phase_results" / "gradcam")
)

# Ngưỡng dưới đó thì không tô gì: CAM gần 0 phủ khắp ảnh sẽ làm mờ toàn bộ nền xám và
# không thêm thông tin nào.
_FLOOR = 0.15

# `attention` trong `webapp/frontend/tailwind.config.js`. Giữ hai nơi khớp nhau bằng
# tay là nợ, nhưng backend không đọc được file cấu hình Tailwind.
_ATTENTION_RGB = np.array([245, 158, 11], dtype=np.float32)  # #F59E0B

_png_cache: OrderedDict[tuple[str, str, int], bytes] = OrderedDict()
_PNG_CACHE_SIZE = 256


@dataclass(frozen=True)
class GradCam:
    """Bản đồ chú ý của một ca, cùng mọi thứ cần để hiển thị trung thực."""

    patient_id: str
    cam_pred: np.ndarray
    cam_true: np.ndarray | None
    crop_ref: np.ndarray
    phase_importance: np.ndarray
    pred_index: int
    true_index: int | None
    fold: str
    layer: str
    native_shape: tuple[int, ...]

    @property
    def n_slices(self) -> int:
        return int(self.crop_ref.shape[2])

    def map_for(self, target: str) -> np.ndarray | None:
        """`pred` luôn có; `true` chỉ có khi mô hình đoán sai."""
        if target == "pred":
            return self.cam_pred
        if target == "true":
            return self.cam_true
        raise ValueError(f"target phải là 'pred' hoặc 'true', nhận {target!r}")


def _load_one(path: Path) -> GradCam:
    data = np.load(path, allow_pickle=False)
    cam_pred = np.asarray(data["cam_pred"], dtype=np.float32)
    crop_ref = np.asarray(data["crop_ref"], dtype=np.uint8)
    if cam_pred.shape != crop_ref.shape:
        raise ValueError(
            f"{path.name}: cam {cam_pred.shape} khác ảnh nền {crop_ref.shape} — "
            "phủ lệch nhau còn tệ hơn không phủ."
        )
    true_index = int(data["true_index"]) if "true_index" in data else None
    return GradCam(
        patient_id=path.stem,
        cam_pred=cam_pred,
        cam_true=np.asarray(data["cam_true"], dtype=np.float32) if "cam_true" in data else None,
        crop_ref=crop_ref,
        phase_importance=np.asarray(data["phase_importance"], dtype=np.float32),
        pred_index=int(data["pred_index"]),
        true_index=true_index,
        fold=str(data["fold"]),
        layer=str(data["layer"]),
        native_shape=tuple(int(v) for v in np.atleast_1d(data["cam_native_shape"])),
    )


@functools.lru_cache(maxsize=1)
def load_all(directory: str | None = None) -> dict[str, GradCam]:
    """Nạp mọi `.npz` trong thư mục, khoá theo tên file. Rỗng nếu chưa có gì."""
    root = Path(directory) if directory else GRADCAM_DIR
    if not root.is_dir():
        return {}
    return {path.stem: _load_one(path) for path in sorted(root.glob("*.npz"))}


def get(patient_id: str, directory: str | None = None) -> GradCam | None:
    return load_all(directory).get(patient_id)


def render_png(cam: GradCam, target: str, z: int) -> bytes:
    """Render một lát: ảnh nền xám + bản đồ chú ý phủ theo alpha.

    Dùng alpha thay vì đổi màu nền: cường độ mô bên dưới phải còn đọc được, nếu không
    thì bản đồ chú ý che mất chính thứ nó đang chỉ vào.
    """
    heat = cam.map_for(target)
    if heat is None:
        raise KeyError(f"{cam.patient_id}: không có bản đồ cho target {target!r}")
    if not 0 <= z < cam.n_slices:
        raise IndexError(f"lát {z} ngoài khoảng [0, {cam.n_slices - 1}]")

    key = (cam.patient_id, target, z)
    cached = _png_cache.get(key)
    if cached is not None:
        _png_cache.move_to_end(key)
        return cached

    # Cùng phép xoay như `volumes.render_slice_png` để hai ảnh cùng hướng — người xem
    # sẽ đối chiếu chúng với nhau, và lệch hướng là lỗi không ai phát hiện bằng mắt.
    gray = cam.crop_ref[:, :, z].T[::-1].astype(np.float32)
    weight = np.clip(heat[:, :, z].T[::-1].astype(np.float32), 0.0, 1.0)
    alpha = np.where(weight < _FLOOR, 0.0, (weight - _FLOOR) / (1.0 - _FLOOR)) * 0.72

    rgb = np.stack([gray, gray, gray], axis=-1)
    rgb = rgb * (1.0 - alpha[..., None]) + _ATTENTION_RGB * alpha[..., None]
    picture = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), mode="RGB")

    buffer = io.BytesIO()
    picture.save(buffer, format="PNG", optimize=True)
    payload = buffer.getvalue()

    _png_cache[key] = payload
    while len(_png_cache) > _PNG_CACHE_SIZE:
        _png_cache.popitem(last=False)
    return payload
