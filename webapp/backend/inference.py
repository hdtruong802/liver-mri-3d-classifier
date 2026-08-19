"""Dựng đối tượng kết quả dự đoán cho lớp serve.

Thuần biến đổi số: nhận một vector xác suất đã có rồi gói thành ``PredictResult``.
Không đọc file, không nạp model, không sinh số mô phỏng. Người gọi duy nhất là
``webapp/backend/live_inference.py`` — đường suy luận trực tiếp trên ZIP người dùng
tải lên.

⚠️ Đường "ca demo dựng sẵn" (``oof_result``, ``predict``) đã gỡ ở WORKLOG S-197 cùng
với ``demo_cases.py`` và ``predictions.py``: nó cần dữ liệu bệnh nhân trong ``data/``,
vốn bị .gitignore, nên người nhận repo không chạy được.
"""

from __future__ import annotations

import numpy as np
from src.data.taxonomy import CLASS_NAMES, MALIGNANT_INDICES, NUM_CLASSES, SHORT_NAMES

from webapp.backend.config import DEFAULT_DEFER_THRESHOLD
from webapp.backend.schemas import (
    ClassProbability,
    DeferBasis,
    PredictResult,
    Provenance,
    Uncertainty,
)


def shannon_entropy(probs: np.ndarray) -> float:
    safe = np.clip(probs, 1e-12, 1.0)
    return float(-np.sum(safe * np.log(safe)))


def build_probabilities(probs: np.ndarray) -> list[ClassProbability]:
    if probs.shape != (NUM_CLASSES,):
        raise ValueError(f"cần vector {NUM_CLASSES} chiều, nhận {probs.shape}")
    return [
        ClassProbability(
            class_index=i,
            class_name=CLASS_NAMES[i],
            label_vi=SHORT_NAMES[i],
            malignant=i in MALIGNANT_INDICES,
            probability=float(probs[i]),
        )
        for i in range(NUM_CLASSES)
    ]


def malignant_probability(probs: np.ndarray) -> float:
    return float(sum(probs[i] for i in sorted(MALIGNANT_INDICES)))


def assemble_result(
    case_id: str,
    probs: np.ndarray,
    provenance: Provenance,
    defer_threshold: float = DEFAULT_DEFER_THRESHOLD,
    ensemble_std: float | None = None,
    epistemic: float | None = None,
    inference_ms: int | None = None,
    defer_override: bool | None = None,
    defer_basis: DeferBasis = DeferBasis.CONFIDENCE,
    defer_score: float | None = None,
    defer_available: bool = True,
) -> PredictResult:
    """Dựng một ``PredictResult`` từ vector đã có; không đọc file hoặc chạy model."""
    total = float(probs.sum())
    if not np.isclose(total, 1.0, atol=1e-4):
        raise ValueError(f"xác suất phải tổng bằng 1, nhận {total:.6f}")

    confidence = float(probs.max())
    pred_index = int(probs.argmax())
    if defer_available:
        defer_value: bool | None = (
            (confidence < defer_threshold) if defer_override is None else defer_override
        )
        basis_value: DeferBasis | None = defer_basis
        score_value: float | None = confidence if defer_score is None else defer_score
        threshold_value: float | None = defer_threshold
    else:
        defer_value = None
        basis_value = None
        score_value = None
        threshold_value = None

    return PredictResult(
        case_id=case_id,
        pred_class_index=pred_index,
        pred_class_name=CLASS_NAMES[pred_index],
        probs=build_probabilities(probs),
        malignant_prob=malignant_probability(probs),
        uncertainty=Uncertainty(
            entropy=shannon_entropy(probs),
            epistemic=epistemic,
            ensemble_std=ensemble_std,
        ),
        defer=defer_value,
        defer_basis=basis_value,
        defer_score=score_value,
        defer_threshold=threshold_value,
        confidence=confidence,
        inference_ms=inference_ms,
        provenance=provenance,
    )
