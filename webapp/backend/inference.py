"""Kết quả dự đoán dùng trong web demo.

Chỉ có một nguồn trong V1: dự đoán out-of-fold đã đo và lưu sẵn. Backend không tải
torch/MONAI, không sinh số mô phỏng, và cũng không chạy suy luận cho ZIP người dùng tải
lên. ZIP chỉ được kiểm tra cấu trúc ở ``/api/validate-upload``.
"""

from __future__ import annotations

import numpy as np
from src.data.taxonomy import CLASS_NAMES, MALIGNANT_INDICES, NUM_CLASSES, SHORT_NAMES

from webapp.backend.config import CHECKPOINT_PATH, DEFAULT_DEFER_THRESHOLD
from webapp.backend.predictions import CasePrediction, PredictionStore, load_store
from webapp.backend.schemas import (
    ClassProbability,
    DeferBasis,
    PredictResult,
    Provenance,
    ProvenanceSource,
    Uncertainty,
)


def model_is_loaded() -> bool:
    """Cho biết checkpoint local có mặt; web demo không nạp checkpoint vào FastAPI."""
    return CHECKPOINT_PATH is not None and CHECKPOINT_PATH.exists()


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
) -> PredictResult:
    """Dựng một ``PredictResult`` từ vector đã có; không đọc file hoặc chạy model."""
    total = float(probs.sum())
    if not np.isclose(total, 1.0, atol=1e-4):
        raise ValueError(f"xác suất phải tổng bằng 1, nhận {total:.6f}")

    confidence = float(probs.max())
    pred_index = int(probs.argmax())
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
        defer=(confidence < defer_threshold) if defer_override is None else defer_override,
        defer_basis=defer_basis,
        defer_score=confidence if defer_score is None else defer_score,
        defer_threshold=defer_threshold,
        confidence=confidence,
        inference_ms=inference_ms,
        provenance=provenance,
    )


def oof_result(case: CasePrediction, store: PredictionStore) -> PredictResult:
    """Trả dự đoán OOF thật của ca mà model fold tương ứng chưa từng thấy khi train."""
    defer = store.should_defer(case)
    note = (
        f"Dự đoán out-of-fold thật: ca này nằm ở tập validation của {case.fold}; "
        "model chấm ca chưa từng thấy nó khi train. Xác suất đã hiệu chỉnh; quyết định "
        "defer theo quy tắc bất định được khóa trước trên validation."
    )
    if not store.has_epistemic:
        note += " Chưa có chỉ số bất định cho ca này nên không thể áp dụng quy tắc defer."

    return assemble_result(
        case_id=case.patient_id,
        probs=case.probs_calibrated,
        provenance=Provenance(
            source=ProvenanceSource.OOF,
            model_version=None,
            note=note,
        ),
        defer_threshold=store.defer_threshold,
        epistemic=case.epistemic,
        inference_ms=None,
        defer_override=defer,
        defer_basis=DeferBasis.EPISTEMIC,
        defer_score=case.epistemic if case.epistemic is not None else 0.0,
    )


def predict(case_id: str) -> PredictResult:
    """Tra một dự đoán OOF thật, hoặc báo rõ khi dữ liệu đó không có."""
    store = load_store()
    if store is None:
        raise LookupError("Chưa có prediction out-of-fold trên máy này.")
    case = store.get(case_id)
    if case is None:
        raise LookupError(f"Không có prediction out-of-fold cho ca {case_id!r}.")
    return oof_result(case, store)
