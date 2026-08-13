"""Direct UniFormer inference for a newly uploaded, lesion-annotated MRI set.

The available fold checkpoints may only be ensembled for a new external case.  They
must never be used to regenerate an out-of-fold prediction because four of the
five models have trained on any given validation patient.
"""

from __future__ import annotations

import functools
import json
import time
from collections.abc import Mapping
from dataclasses import dataclass
from importlib.util import find_spec
from pathlib import Path
from typing import Any

import numpy as np
from src.preprocess.build_cache import process_uploaded_with_masks
from src.utils.io import load_yaml

from webapp.backend.config import (
    LIVE_DEVICE,
    LIVE_PREPROCESS_CONFIG,
    LIVE_WEIGHTS_DIR,
    REPO_ROOT,
)
from webapp.backend.inference import assemble_result
from webapp.backend.schemas import PredictResult, Provenance, ProvenanceSource

_EXPECTED_MODEL = {
    "name": "uniformer3d",
    "variant": "small",
    "in_channels": 8,
    "num_classes": 7,
    "patch_embed1_stride": [1, 2, 2],
    "drop_rate": 0.0,
    "drop_path_rate": 0.1,
    "head_dropout": 0.0,
    "require_pretrained": True,
    "pretrained_path": None,
}


@dataclass(frozen=True)
class UploadInference:
    """Prediction plus the exact cropped arrays used for the forward pass."""

    prediction: PredictResult
    crop_volume: np.ndarray
    annotation_masks: np.ndarray
    spacing_mm: np.ndarray


def weight_paths() -> tuple[Path, ...]:
    """Return completed UniFormer folds; a finished fold 4 is picked up on restart."""
    return tuple(sorted(LIVE_WEIGHTS_DIR.glob("fold_*/uniformer3D_best_*.pt")))


def dependencies_available() -> bool:
    return all(find_spec(package) is not None for package in ("torch", "yaml", "SimpleITK"))


def is_available() -> bool:
    """Whether the machine has both the local artifacts and runtime packages."""
    return (
        LIVE_PREPROCESS_CONFIG.is_file()
        and len(weight_paths()) >= 4
        and dependencies_available()
    )


def _select_device(torch) -> str:
    if LIVE_DEVICE in {"", "auto"}:
        return "cuda" if torch.cuda.is_available() else "cpu"
    if LIVE_DEVICE not in {"cpu", "cuda"}:
        raise RuntimeError("LLDMMRI_LIVE_DEVICE chỉ nhận auto, cpu hoặc cuda")
    if LIVE_DEVICE == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("LLDMMRI_LIVE_DEVICE=cuda nhưng PyTorch không thấy GPU")
    return LIVE_DEVICE


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise RuntimeError(f"config cạnh weights không hợp lệ: {path}")
    return data


def _load_runtime_config() -> tuple[list[dict[str, str]], dict[str, Any], dict[str, Any]]:
    data_config = load_yaml(REPO_ROOT / "configs" / "data.yaml")
    preprocess_config = load_yaml(LIVE_PREPROCESS_CONFIG)
    phases = data_config.get("phases")
    if not isinstance(phases, list) or len(phases) != 8:
        raise RuntimeError("configs/data.yaml phải khai báo đủ 8 phase")
    if (
        preprocess_config.get("crop_mode") != "lesion_tight"
        or (preprocess_config.get("lesion_tight") or {}).get("source") != "mask"
        or preprocess_config.get("align_phases") != "per_phase"
        or tuple(preprocess_config.get("target_size") or ()) != (112, 112, 14)
        or tuple(preprocess_config.get("crop_margin_voxels") or ()) != (8, 8, 1)
    ):
        raise RuntimeError("preprocess dùng cho upload không khớp crop ROI UniFormer")
    return phases, preprocess_config, data_config


@functools.lru_cache(maxsize=1)
def _load_models() -> tuple[tuple[Any, ...], str]:
    """Load completed UniFormer folds once, strictly validating their architecture."""
    if not dependencies_available():
        raise RuntimeError(
            "Thiếu runtime suy luận. Cài dependencies trong "
            "webapp/backend/requirements.txt rồi khởi động lại backend."
        )
    checkpoints = weight_paths()
    if len(checkpoints) < 4:
        raise RuntimeError("Cần tối thiểu 4 checkpoint UniFormer hoàn tất để suy luận.")
    missing = [str(path) for path in checkpoints if not path.is_file()]
    if missing:
        raise RuntimeError("Thiếu checkpoint UniFormer: " + ", ".join(missing))

    import torch
    from src.models import build_model

    config_path = LIVE_WEIGHTS_DIR / "fold_1" / "config_used.json"
    if not config_path.is_file():
        raise RuntimeError(f"Thiếu config đã dùng để train cạnh weights: {config_path}")
    training_config = _load_json(config_path)
    model_config = training_config.get("model")
    if model_config != _EXPECTED_MODEL:
        raise RuntimeError("weights không khớp kiến trúc UniFormer-S đã được kiểm tra")

    device = _select_device(torch)
    models: list[Any] = []
    for path in checkpoints:
        expected_fold = int(path.stem.rsplit("_", 1)[-1])
        try:
            payload = torch.load(path, map_location=device, weights_only=True)
        except TypeError:  # PyTorch cũ hơn không có weights_only.
            payload = torch.load(path, map_location=device)
        if not isinstance(payload, dict) or not isinstance(payload.get("model"), dict):
            raise RuntimeError(f"checkpoint {path.name} không có state_dict 'model'")
        if payload.get("fold") not in {None, expected_fold}:
            raise RuntimeError(f"checkpoint {path.name} khai báo fold không khớp")
        # The checkpoint already includes Kinetics-initialised weights.
        model = build_model({**model_config, "require_pretrained": False})
        model.load_state_dict(payload["model"], strict=True)
        model.to(device)
        model.eval()
        models.append(model)
    return tuple(models), device


def predict_uploaded(
    archive_name: str,
    image_paths: Mapping[str, Path],
    mask_paths: Mapping[str, Path],
) -> UploadInference:
    """Run raw UniFormer ensemble probabilities for one newly uploaded case.

    No temperature or defer rule is applied: those serving rules were validated
    for the stored OOF population, not for this unlabelled upload.
    """
    started = time.perf_counter()
    phases, preprocess_config, _ = _load_runtime_config()
    volume, crop_meta = process_uploaded_with_masks(
        image_paths, mask_paths, phases, preprocess_config
    )
    annotation_masks = np.asarray(crop_meta["annotation_masks"], dtype=np.uint8)
    if volume.shape != (8, 128, 128, 16) or annotation_masks.shape != volume.shape:
        raise RuntimeError(
            "crop ROI UniFormer cho shape bất ngờ: "
            f"MRI {volume.shape}, mask {annotation_masks.shape}"
        )
    # Validation/inference uses the deterministic centre crop 128×128×16 -> 112×112×14.
    model_volume = volume[:, 8:120, 8:120, 1:15]
    model_masks = annotation_masks[:, 8:120, 8:120, 1:15]
    if model_volume.shape != (8, 112, 112, 14) or model_masks.shape != model_volume.shape:
        raise RuntimeError(
            "center crop UniFormer cho shape bất ngờ: "
            f"MRI {model_volume.shape}, mask {model_masks.shape}"
        )

    models, device = _load_models()
    import torch

    tensor = torch.from_numpy(np.ascontiguousarray(model_volume, dtype=np.float32))
    tensor = tensor.unsqueeze(0).to(device)
    member_probs: list[np.ndarray] = []
    with torch.inference_mode():
        for model in models:
            logits = model(tensor)
            probs = torch.softmax(logits, dim=1).detach().cpu().numpy()[0]
            member_probs.append(np.asarray(probs, dtype=np.float64))
    stacked = np.stack(member_probs, axis=0)
    probs = stacked.mean(axis=0)
    probs /= probs.sum()
    elapsed_ms = int((time.perf_counter() - started) * 1000)

    prediction = assemble_result(
        case_id=Path(archive_name).stem,
        probs=probs,
        provenance=Provenance(
            source=ProvenanceSource.LIVE,
            model_version=f"UniFormer-S · ensemble {len(models)} fold",
            note=(
                f"Suy luận trực tiếp từ {len(models)} weights UniFormer-S trên bộ MRI "
                "và mask người dùng tải lên. "
                "Xác suất là trung bình softmax thô, chưa được hiệu chỉnh cho nguồn dữ liệu này. "
                "Không áp dụng cơ chế từ chối ca. Research Use Only, không dùng để chẩn đoán."
            ),
        ),
        ensemble_std=float(stacked.std(axis=0).mean()),
        inference_ms=elapsed_ms,
        defer_available=False,
    )
    return UploadInference(
        prediction=prediction,
        crop_volume=model_volume,
        annotation_masks=model_masks,
        spacing_mm=np.asarray(crop_meta["spacing"], dtype=np.float32),
    )
