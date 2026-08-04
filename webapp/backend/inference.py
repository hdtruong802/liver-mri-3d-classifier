"""Lớp suy luận.

Hai nguồn số, phân biệt bằng `provenance.source` trong **mọi** phản hồi:

- **`oof`** — dự đoán out-of-fold THẬT, tra từ `.npz` đã lưu. 394 bệnh nhân trong
  trainval, mỗi ca được chấm bởi đúng model chưa từng thấy nó khi train. Đây là số
  đo được. Xem `webapp/backend/predictions.py`.
- **`simulated`** — sinh ra để dựng giao diện, dùng cho ca không có trong 394 ca đó.

Vì sao vẫn giữ nhánh mô phỏng thay vì trả 404: giao diện phải dựng và kiểm được với
dữ liệu có hình dạng thật. Cách phòng rủi ro không phải là giấu số đi, mà là **làm
cho không thể nhầm số giả với số thật**: `provenance.source` đi kèm mọi phản hồi, và
`webapp/DESIGN.md` buộc frontend đánh dấu bằng hai tín hiệu độc lập (chữ nghiêng và
nhãn chữ).

**Không có nhánh `live`** (forward pass từ checkpoint), và đó là chủ ý: backend bị
ràng buộc không kéo theo torch/monai (AGENTS.md §4), mà 394 ca out-of-fold đã đủ cho
bản demo. Ảnh mới tải lên không suy luận được — giới hạn thật, phải nói rõ với người
dùng chứ không che.
"""

from __future__ import annotations

import hashlib

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

_SIMULATED_NOTE = (
    "Số minh hoạ, chưa có model. Dùng để dựng và kiểm giao diện; "
    "không phải kết quả đo được của nghiên cứu."
)


def model_is_loaded() -> bool:
    """Đã có checkpoint thật hay chưa. W5 sẽ nạp; hiện luôn False."""
    return CHECKPOINT_PATH is not None and CHECKPOINT_PATH.exists()


def shannon_entropy(probs: np.ndarray) -> float:
    """Entropy của phân phối, đơn vị nat.

    Đây là chỉ số bất định mà pipeline này thực sự tính được, cùng với độ lệch chuẩn
    giữa các thành viên ensemble. Cố ý không phân rã epistemic/aleatoric: dự án không
    làm phép phân rã đó, nên báo nó ra là bịa một đại lượng chưa từng được đo.
    """
    safe = np.clip(probs, 1e-12, 1.0)
    return float(-np.sum(safe * np.log(safe)))


def build_probabilities(probs: np.ndarray) -> list[ClassProbability]:
    """Gói vector xác suất thành danh sách đủ 7 lớp theo taxonomy dự án."""
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
    """Tổng xác suất ba lớp ác: ICC, di căn, HCC (`taxonomy.MALIGNANT_INDICES`)."""
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
    """Dựng `PredictResult` từ một vector xác suất, bất kể nó từ đâu ra.

    Hàm thuần: cùng đầu vào cho cùng đầu ra, không đọc file, không đụng model. Nhờ
    vậy nó dùng lại được y nguyên khi chuyển từ `simulated` sang `oof`, và test được
    mà không cần torch.

    `defer_override` tồn tại vì quyết định từ chối **không phải lúc nào cũng suy ra
    được từ `confidence`**. Với dự đoán out-of-fold thật, defer dựa trên bất định
    epistemic — một đại lượng không nằm trong vector xác suất này (WORKLOG S-087:
    xếp hạng theo max-prob vô ích, P=0.88). Để `None` thì rơi về so `confidence` với
    ngưỡng, đúng như hành vi cũ của nhánh mô phỏng.
    """
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
        # Từ chối là kết quả hợp lệ, không phải lỗi (`PRODUCT.md` Product Principle 2).
        defer=(confidence < defer_threshold) if defer_override is None else defer_override,
        defer_basis=defer_basis,
        defer_score=confidence if defer_score is None else defer_score,
        defer_threshold=defer_threshold,
        confidence=confidence,
        inference_ms=inference_ms,
        provenance=provenance,
    )


def simulate_result(
    case_id: str, defer_threshold: float = DEFAULT_DEFER_THRESHOLD
) -> PredictResult:
    """Sinh một phân phối giả lập, **tất định theo `case_id`**.

    Tất định là có chủ ý: cùng một ca phải cho cùng một màn hình mỗi lần mở, nếu không
    người xem sẽ tưởng model không ổn định. Seed lấy từ băm của `case_id`.

    Hình dạng phân phối được chọn để giống bài toán thật chứ không phải ngẫu nhiên
    đều: một lớp dẫn đầu, một lớp bám sát trong cùng nhóm ác hoặc lành, phần còn lại
    thấp. Nhầm lẫn nội bộ nhóm ác chiếm 46% số ca sai của lần train E4, nên đó là hình
    dạng đáng dựng giao diện quanh nó.
    """
    seed = int.from_bytes(hashlib.sha256(case_id.encode()).digest()[:4], "big")
    rng = np.random.default_rng(seed)

    logits = rng.normal(0.0, 0.6, size=NUM_CLASSES)
    leader = int(rng.integers(0, NUM_CLASSES))
    logits[leader] += rng.uniform(1.2, 2.6)
    # Một lớp bám sát, ưu tiên cùng nhóm ác/lành với lớp dẫn đầu.
    same_group = [
        i
        for i in range(NUM_CLASSES)
        if i != leader and (i in MALIGNANT_INDICES) == (leader in MALIGNANT_INDICES)
    ]
    runner_up = int(rng.choice(same_group)) if same_group else (leader + 1) % NUM_CLASSES
    logits[runner_up] += rng.uniform(0.5, 1.4)

    exponentiated = np.exp(logits - logits.max())
    probs = exponentiated / exponentiated.sum()

    return assemble_result(
        case_id=case_id,
        probs=probs,
        provenance=Provenance(
            source=ProvenanceSource.SIMULATED,
            model_version=None,  # Không bịa chuỗi phiên bản. Bản bolt ghi "HepatoNet-3D v2.4.1".
            note=_SIMULATED_NOTE,
        ),
        defer_threshold=defer_threshold,
        ensemble_std=None,  # None chứ không phải 0: 0 nghĩa là ensemble đồng thuận tuyệt đối.
        inference_ms=None,
    )


def oof_result(case: CasePrediction, store: PredictionStore) -> PredictResult:
    """Dựng kết quả từ dự đoán out-of-fold thật.

    Ba đại lượng lấy từ ba nguồn khác nhau, theo đúng kết quả đo ở WORKLOG S-087 —
    lý do đầy đủ ở docstring `webapp/backend/predictions.py`:

    - lớp đoán ← model tất định;
    - xác suất hiển thị ← model tất định **đã temperature scaling**;
    - quyết định defer ← **epistemic**, không phải max-prob.

    `defer` vì thế **không** suy ra được từ `confidence` hiển thị. Đó là chủ ý, và
    frontend phải nói rõ lý do từ chối là bất định giữa các lượt dự đoán chứ không
    phải "xác suất thấp" — nếu không, một ca defer với xác suất 0,94 sẽ trông như lỗi.
    """
    probs = case.probs_calibrated
    defer = store.should_defer(case)

    note = (
        f"Dự đoán out-of-fold thật: ca này nằm ở tập validation của {case.fold}, "
        f"model chấm nó chưa từng thấy nó khi train. Xác suất đã hiệu chỉnh "
        f"(T={store.temperature:.3f}). Quyết định từ chối dựa trên bất định epistemic "
        f"(MC-dropout), không dựa trên xác suất — xem WORKLOG S-087."
    )
    if not store.has_epistemic:
        note += " CHƯA có epistemic cho ca này nên không đánh giá được từ chối hay không."

    return assemble_result(
        case_id=case.patient_id,
        probs=probs,
        provenance=Provenance(
            source=ProvenanceSource.OOF,
            model_version=None,  # Chưa có chuỗi phiên bản chính thức; không bịa.
            note=note,
        ),
        defer_threshold=store.defer_threshold,
        # Mutual information giữa 20 lượt MC-dropout — KHÔNG phải độ lệch chuẩn.
        epistemic=case.epistemic,
        inference_ms=None,  # Tra cứu, không suy luận: báo thời gian là gây hiểu nhầm.
        defer_override=defer,
        defer_basis=DeferBasis.EPISTEMIC,
        defer_score=case.epistemic if case.epistemic is not None else 0.0,
    )


def predict(case_id: str, defer_threshold: float = DEFAULT_DEFER_THRESHOLD) -> PredictResult:
    """Điểm vào duy nhất của suy luận.

    Thứ tự ưu tiên: dự đoán out-of-fold thật → mô phỏng. Nhánh `live` (forward pass
    từ checkpoint) chưa có và **cố ý chưa có**: backend không được kéo theo torch
    (AGENTS.md §4), mà 394 ca out-of-fold đã đủ cho bản demo.
    """
    store = load_store()
    if store is not None:
        case = store.get(case_id)
        if case is not None:
            return oof_result(case, store)
    return simulate_result(case_id, defer_threshold=defer_threshold)
