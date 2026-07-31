"""Lớp suy luận.

**Chưa có model.** W5 mới nạp checkpoint (`docs/plan.md`); hiện tại dự án đang ở W3
và GPU đang chạy CV 5-fold. Module này định nghĩa giao diện, cộng một bản sinh số
giả lập được đánh dấu `simulated` ở mọi phản hồi.

Vì sao vẫn sinh số thay vì trả 501: giao diện phải dựng được và kiểm được với dữ liệu
có hình dạng thật (7 lớp, tổng bằng 1, entropy khớp phân phối, ngưỡng defer thật sự
được so). Cách phòng rủi ro không phải là giấu số đi, mà là **làm cho không thể nhầm
số giả với số thật**: `provenance.source` đi kèm mọi phản hồi, và
`webapp/DESIGN.md` buộc frontend đánh dấu bằng hai tín hiệu độc lập (chữ nghiêng và
nhãn chữ).

Khi có checkpoint: thay `simulate_result` bằng forward pass thật, đổi `source` sang
`live`, mọi thứ khác giữ nguyên.
"""

from __future__ import annotations

import hashlib

import numpy as np
from src.data.taxonomy import CLASS_NAMES, MALIGNANT_INDICES, NUM_CLASSES, SHORT_NAMES

from webapp.backend.config import CHECKPOINT_PATH, DEFAULT_DEFER_THRESHOLD
from webapp.backend.schemas import (
    ClassProbability,
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
    inference_ms: int | None = None,
) -> PredictResult:
    """Dựng `PredictResult` từ một vector xác suất, bất kể nó từ đâu ra.

    Hàm thuần: cùng đầu vào cho cùng đầu ra, không đọc file, không đụng model. Nhờ
    vậy nó dùng lại được y nguyên khi chuyển từ `simulated` sang `live`, và test được
    mà không cần torch.
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
        uncertainty=Uncertainty(entropy=shannon_entropy(probs), ensemble_std=ensemble_std),
        # Từ chối là kết quả hợp lệ, không phải lỗi (`PRODUCT.md` Product Principle 2).
        defer=confidence < defer_threshold,
        defer_threshold=defer_threshold,
        confidence=confidence,
        heatmap_slices=[],  # Grad-CAM thuộc W5; rỗng ⇒ frontend vẽ vùng "chưa khảo sát".
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


def predict(case_id: str, defer_threshold: float = DEFAULT_DEFER_THRESHOLD) -> PredictResult:
    """Điểm vào duy nhất của suy luận.

    W5 thay nhánh dưới bằng forward pass thật khi `model_is_loaded()`.
    """
    if model_is_loaded():
        raise NotImplementedError(
            "Đã thấy checkpoint nhưng nhánh suy luận thật thuộc W5 và chưa được viết. "
            "Bỏ biến LLDMMRI_CHECKPOINT để chạy ở chế độ minh hoạ."
        )
    return simulate_result(case_id, defer_threshold=defer_threshold)
