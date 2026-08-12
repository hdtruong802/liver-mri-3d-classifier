"""Read and render offline multi-phase model-sensitivity artefacts.

The files are produced on Kaggle from the exact E4 crop grid. This backend only
validates and composites them; it never fabricates overlays or runs a model.
Heatmaps are local sensitivity for the predicted class, not lesion masks.
"""

from __future__ import annotations

import io
from collections import OrderedDict
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image

from webapp.backend.config import MODEL_HEATMAP_DIR, SLICE_CACHE_SIZE
from webapp.backend.phases import PHASES

_EXPECTED_PHASES = tuple(phase.file_token for phase in PHASES)
_ANNOTATION_COLOUR = np.array([232, 121, 249], dtype=np.float32)  # #E879F9
_HEATMAP_COLOUR = np.array([245, 158, 11], dtype=np.float32)  # #F59E0B
_render_cache: OrderedDict[tuple[str, str, int, bool, bool], bytes] = OrderedDict()


class InvalidModelHeatmap(ValueError):
    """The on-disk artefact cannot safely be rendered."""


@dataclass(frozen=True)
class ModelHeatmap:
    patient_id: str
    phase_tokens: tuple[str, ...]
    crop_refs: np.ndarray
    heatmaps_pred: np.ndarray
    annotation_masks: np.ndarray
    pred_index: int
    heatmap_scale: float

    @property
    def n_slices(self) -> int:
        return int(self.crop_refs.shape[3])

    @property
    def lesion_slices(self) -> dict[str, list[int]]:
        return {
            token: [
                int(z)
                for z, present in enumerate(self.annotation_masks[i].any(axis=(0, 1)))
                if present
            ]
            for i, token in enumerate(self.phase_tokens)
        }


def _require_shape(name: str, array: np.ndarray, shape: tuple[int, ...]) -> None:
    if tuple(array.shape) != shape:
        raise InvalidModelHeatmap(f"{name} has shape {tuple(array.shape)}, expected {shape}")


def _read_artifact(path: Path) -> ModelHeatmap:
    try:
        with np.load(path, allow_pickle=False) as payload:
            required = {
                "phase_tokens",
                "crop_refs",
                "heatmaps_pred",
                "annotation_masks",
                "pred_index",
                "heatmap_scale",
            }
            missing = required.difference(payload.files)
            if missing:
                raise InvalidModelHeatmap(f"missing keys: {', '.join(sorted(missing))}")
            phase_tokens = tuple(str(token) for token in payload["phase_tokens"].tolist())
            crop_refs = np.asarray(payload["crop_refs"])
            heatmaps = np.asarray(payload["heatmaps_pred"], dtype=np.float32)
            masks = np.asarray(payload["annotation_masks"])
            pred_index = int(np.asarray(payload["pred_index"]).item())
            heatmap_scale = float(np.asarray(payload["heatmap_scale"]).item())
    except (OSError, ValueError, TypeError) as exc:
        if isinstance(exc, InvalidModelHeatmap):
            raise
        raise InvalidModelHeatmap(f"cannot read {path.name}: {exc}") from exc

    if phase_tokens != _EXPECTED_PHASES:
        raise InvalidModelHeatmap(
            f"phase_tokens {phase_tokens!r} do not match expected E4 order {_EXPECTED_PHASES!r}"
        )
    if crop_refs.dtype != np.uint8 or crop_refs.ndim != 4 or crop_refs.shape[0] != len(PHASES):
        raise InvalidModelHeatmap("crop_refs must be uint8 with shape [8, x, y, z]")
    shape = tuple(int(v) for v in crop_refs.shape)
    if any(v <= 0 for v in shape[1:]):
        raise InvalidModelHeatmap("crop_refs has an empty spatial dimension")
    _require_shape("heatmaps_pred", heatmaps, shape)
    _require_shape("annotation_masks", masks, shape)
    is_valid_range = heatmaps.min(initial=0.0) >= 0.0 and heatmaps.max(initial=0.0) <= 1.0
    if not np.isfinite(heatmaps).all() or not is_valid_range:
        raise InvalidModelHeatmap("heatmaps_pred must be finite and globally normalised to [0, 1]")
    if not np.isfinite(heatmap_scale) or heatmap_scale < 0.0:
        raise InvalidModelHeatmap("heatmap_scale must be a finite non-negative value")
    if not 0 <= pred_index <= 6:
        raise InvalidModelHeatmap("pred_index must be a valid seven-class index")

    return ModelHeatmap(
        patient_id=path.stem,
        phase_tokens=phase_tokens,
        crop_refs=crop_refs,
        heatmaps_pred=heatmaps,
        annotation_masks=(masks > 0).astype(np.uint8),
        pred_index=pred_index,
        heatmap_scale=heatmap_scale,
    )


@lru_cache(maxsize=4)
def load_all(directory: str | None = None) -> dict[str, ModelHeatmap]:
    """Load valid artefacts once; invalid files are omitted rather than faked."""
    root = Path(directory) if directory else MODEL_HEATMAP_DIR
    if not root.is_dir():
        return {}
    loaded: dict[str, ModelHeatmap] = {}
    for path in sorted(root.glob("*.npz")):
        try:
            artifact = _read_artifact(path)
        except InvalidModelHeatmap:
            continue
        loaded[artifact.patient_id] = artifact
    return loaded


def get(patient_id: str) -> ModelHeatmap | None:
    return load_all().get(patient_id)


def _oriented_slab(volume: np.ndarray, z: int) -> np.ndarray:
    return volume[:, :, z].T[::-1]


def _overlay_heatmap(rgb: np.ndarray, heatmap: np.ndarray) -> np.ndarray:
    """Amber sensitivity layer. Values below 0.15 stay transparent."""
    weight = np.clip(heatmap.astype(np.float32), 0.0, 1.0)
    alpha = np.clip((weight - 0.15) / 0.85, 0.0, 1.0) * 0.72
    result = rgb.astype(np.float32)
    result = result * (1.0 - alpha[..., None]) + _HEATMAP_COLOUR * alpha[..., None]
    return np.clip(result, 0, 255).astype(np.uint8)


def _overlay_annotation(rgb: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Fuchsia human annotation rendered above the optional heatmap."""
    binary = mask > 0
    if not binary.any():
        return rgb
    padded = np.pad(binary, 1, mode="constant", constant_values=False)
    interior = padded[:-2, 1:-1] & padded[2:, 1:-1] & padded[1:-1, :-2] & padded[1:-1, 2:] & binary
    edge = binary & ~interior
    result = rgb.astype(np.float32)
    result[binary] = result[binary] * 0.75 + _ANNOTATION_COLOUR * 0.25
    result[edge] = _ANNOTATION_COLOUR
    return np.clip(result, 0, 255).astype(np.uint8)


def render_png(
    artifact: ModelHeatmap,
    phase_token: str,
    z: int,
    *,
    annotation: bool,
    heatmap: bool,
) -> bytes:
    """Render MRI → heatmap → human annotation in the E4 crop space."""
    if phase_token not in artifact.phase_tokens:
        raise ValueError(f"unknown phase {phase_token!r}")
    if not 0 <= z < artifact.n_slices:
        raise IndexError(f"slice {z} outside [0, {artifact.n_slices - 1}]")
    key = (artifact.patient_id, phase_token, z, annotation, heatmap)
    cached = _render_cache.get(key)
    if cached is not None:
        _render_cache.move_to_end(key)
        return cached

    phase_index = artifact.phase_tokens.index(phase_token)
    gray = _oriented_slab(artifact.crop_refs[phase_index], z)
    rgb = np.stack([gray, gray, gray], axis=-1)
    if heatmap:
        rgb = _overlay_heatmap(rgb, _oriented_slab(artifact.heatmaps_pred[phase_index], z))
    if annotation:
        rgb = _overlay_annotation(rgb, _oriented_slab(artifact.annotation_masks[phase_index], z))

    buffer = io.BytesIO()
    Image.fromarray(rgb, mode="RGB").save(buffer, format="PNG", optimize=True)
    payload = buffer.getvalue()
    _render_cache[key] = payload
    while len(_render_cache) > SLICE_CACHE_SIZE:
        _render_cache.popitem(last=False)
    return payload
