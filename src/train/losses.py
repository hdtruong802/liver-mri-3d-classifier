"""Hàm mất mát: cross-entropy · focal · class-balanced.

## Vì sao thêm focal loss vào lúc này

Hai lý do độc lập, cả hai đều là bằng chứng chứ không phải phỏng đoán.

**1. Độ chính xác.** Ablation của CGHNet (Bảng 4, `doi:10.1016/j.compmedimag.2026.102780`)
chạy trên **đúng dataset LLD-MMRI và đúng protocol 14×112×112** mà ta đang dùng:
Focal 81.8 so với CE 79.9 — cao hơn 1.9 điểm. Đây là đòn bẩy recipe-huấn-luyện có
bằng chứng mạnh nhất còn lại; augmentation thì ta đã có (bỏ random-crop mất 8.8 điểm,
ta không bỏ), lr 1e-4 đã đúng.

**2. Hiệu chỉnh xác suất — và đây mới là lý do hợp với đóng góp headline của dự án.**
Đo trên out-of-fold E4 (WORKLOG S-079): độ tự tin trung bình **0.889** trong khi
accuracy 0.703, trung vị 0.987, phân vị 75 là **1.000**. Model tự tin quá mức đến mức
bệnh lý. Đó là hệ quả đã biết của 300 epoch cross-entropy trần: CE luôn thưởng cho
việc đẩy xác suất lớp đúng về 1 và không bao giờ dừng. Mukhoti và cs. 2020
(*Calibrating Deep Neural Networks using Focal Loss*) cho thấy focal loss sinh ra model
hiệu chỉnh tốt hơn hẳn, vì hệ số ``(1-p)^γ`` **ngừng thưởng** cho những ca đã đúng chắc.

Ta đang phải chữa hậu kỳ bằng temperature scaling, mà một scalar chỉ hạ được ECE
0.203 → 0.153 (S-079). Focal loss tấn công nguyên nhân thay vì triệu chứng.

## Cảnh báo khi đọc kết quả

Focal loss **đổi thang xác suất**, nên ECE của một model focal không so trực tiếp được
với ECE của model CE *chưa* hiệu chỉnh — phải so sau khi cả hai đã temperature-scale,
hoặc so cả hai trước. Ghi rõ trong báo cáo mình đang so cái nào.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np

from src.data.taxonomy import NUM_CLASSES

__all__ = ["build_criterion", "effective_number_weights", "focal_loss"]


def effective_number_weights(
    labels: Sequence[int], beta: float = 0.9999, num_classes: int = NUM_CLASSES
) -> np.ndarray:
    """Trọng số class-balanced theo *số mẫu hiệu dụng* (Cui và cs. 2019).

    Nghịch tần suất trần (``class_weights_from_labels`` trong `src/train/loop.py`) giả
    định mỗi mẫu thêm vào đóng góp một lượng thông tin như nhau. Với lớp nhiều dữ liệu
    thì không đúng — mẫu thứ 150 của HCC chồng lấn nhiều với 149 mẫu trước. Số mẫu
    hiệu dụng ``(1 - β^n) / (1 - β)`` mô hình hoá chỗ chồng lấn đó, nên trọng số tăng
    chậm hơn nghịch tần suất và ít làm nổ gradient của lớp hiếm.

    ``β → 0`` cho trọng số đều; ``β → 1`` tiệm cận nghịch tần suất. 0.9999 là giá trị
    bài gốc dùng cho tập cỡ vài trăm–vài nghìn.

    ⚠️ **Chỉ truyền nhãn của tập train.** Đếm cả val là leakage (AGENTS.md §3.3).

    Trả về mảng ``[num_classes]`` chuẩn hoá về trung bình 1, để đổi loss weighting
    không kéo theo đổi độ lớn learning rate hiệu dụng. Lớp vắng mặt nhận trọng số 1.
    """
    if not 0.0 <= beta < 1.0:
        raise ValueError(f"beta phải trong [0, 1), nhận {beta}")
    counts = np.bincount(np.asarray(labels, dtype=int), minlength=num_classes).astype(float)
    weights = np.ones(num_classes, dtype=np.float64)
    present = counts > 0
    effective = (1.0 - np.power(beta, counts[present])) / (1.0 - beta)
    raw = 1.0 / effective
    weights[present] = raw / raw.mean()
    return weights


def focal_loss(
    logits: Any,
    targets: Any,
    gamma: float = 2.0,
    weight: Any | None = None,
    label_smoothing: float = 0.0,
) -> Any:
    """Focal loss đa lớp: ``-(1-p_đúng)^γ · log p_đúng``, trung bình trên batch.

    ``γ = 0`` cho lại đúng cross-entropy — dùng làm phép kiểm tính đúng đắn, và có
    test đối chiếu trực tiếp với `torch.nn.CrossEntropyLoss`.

    `weight` là trọng số lớp (vai trò ``α``), nhân vào **sau** hệ số điều biến. Chuẩn
    hoá theo tổng trọng số của các mẫu trong batch chứ không chia cho batch size, khớp
    quy ước ``reduction='mean'`` của PyTorch khi có `weight`; nếu chia cho batch size
    thì độ lớn loss sẽ trôi theo thành phần lớp của từng batch.
    """
    import torch
    import torch.nn.functional as F

    if gamma < 0:
        raise ValueError(f"gamma phải ≥ 0, nhận {gamma}")

    log_probs = F.log_softmax(logits, dim=1)
    # `label_smoothing` xử lý riêng: F.cross_entropy trộn sẵn smoothing vào kết quả
    # nên không lấy ra được log p_đúng để nhân hệ số điều biến.
    log_pt = log_probs.gather(1, targets.unsqueeze(1)).squeeze(1)
    modulating = (1.0 - log_pt.exp()).pow(gamma)

    if label_smoothing > 0.0:
        n = log_probs.shape[1]
        smooth = -log_probs.mean(dim=1)
        per_sample = (1.0 - label_smoothing) * (-log_pt) + label_smoothing * n / (n - 1) * smooth
        per_sample = modulating * per_sample
    else:
        per_sample = -modulating * log_pt

    if weight is None:
        return per_sample.mean()
    sample_weight = weight.gather(0, targets)
    return (per_sample * sample_weight).sum() / sample_weight.sum().clamp_min(
        torch.finfo(sample_weight.dtype).eps
    )


def deep_supervision(base: Any, aux_weight: float = 1.0) -> Any:
    """Bọc một criterion để nó nhận **dict nhiều đầu ra** thay vì một tensor logits.

    Dùng cho CGHNet, nơi bài báo định nghĩa (Eq. 12)::

        L = FL(ŷ, y) + Σ_{m ∈ {2D, 3D}} FL(ŷ_m, y)

    Hàm trả về vẫn nhận được **cả** tensor thường (khi đó nó chỉ gọi `base`), nên cùng
    một criterion dùng được cho cả model một đầu ra và model nhiều đầu ra. Nhờ vậy
    `run_epoch` không phải biết mình đang train kiến trúc nào.

    `aux_weight` mặc định 1.0 vì bài cộng **không có trọng số**. Để lại tham số để ablate
    được, nhưng đổi nó là lệch khỏi công thức của bài.

    ⚠️ Vì sao deep supervision là bắt buộc chứ không phải tuỳ chọn ở CGHNet: hai đầu phụ
    chính là hai nhánh đơn lẻ, và mốc công bố cho chúng (0.724 cho 3D, 0.742 cho 2D) là
    **thang bậc chẩn đoán** của cả phép tái lập. Bỏ chúng đi thì một kết quả thấp không
    còn phân biệt được "sai protocol" với "sai fusion". Bài cũng nói thêm rằng multi-head
    supervision *"prevents modality co-adaptation"*.
    """

    def criterion(output: Any, targets: Any) -> Any:
        if not isinstance(output, dict):
            return base(output, targets)
        total = base(output["main"], targets)
        for logits in (output.get("aux") or {}).values():
            total = total + aux_weight * base(logits, targets)
        return total

    return criterion


def build_criterion(config: dict[str, Any], train_labels: Sequence[int], device: Any) -> Any:
    """Dựng hàm mất mát từ khối ``loss:`` của config.

    Khoá config::

        loss:
          name: cross_entropy | focal
          class_weights: none | balanced | effective_number
          label_smoothing: 0.0
          gamma: 2.0             # chỉ dùng khi name = focal
          beta: 0.9999           # chỉ dùng khi class_weights = effective_number
          deep_supervision: false # bọc bằng `deep_supervision()` cho model nhiều đầu ra
          aux_weight: 1.0        # trọng số các đầu phụ; bài CGHNet dùng 1.0

    ⚠️ Trọng số lớp **luôn** tính từ `train_labels` và chỉ từ đó. Người gọi phải
    truyền đúng nhãn train của fold đang chạy, không phải toàn bộ trainval.
    """
    import torch

    from src.train.loop import class_weights_from_labels

    loss_config = config.get("loss") or {}
    name = str(loss_config.get("name", "cross_entropy"))
    label_smoothing = float(loss_config.get("label_smoothing", 0.0))

    mode = str(loss_config.get("class_weights", "none"))
    if mode == "none":
        weight = None
    elif mode == "balanced":
        weight = class_weights_from_labels(train_labels)
    elif mode == "effective_number":
        weight = effective_number_weights(train_labels, float(loss_config.get("beta", 0.9999)))
    else:
        raise ValueError(
            f"loss.class_weights phải thuộc {{none, balanced, effective_number}}, nhận {mode!r}"
        )
    if weight is not None:
        weight = torch.tensor(weight, dtype=torch.float32, device=device)

    if name == "cross_entropy":
        base = torch.nn.CrossEntropyLoss(weight=weight, label_smoothing=label_smoothing)
    elif name == "focal":
        gamma = float(loss_config.get("gamma", 2.0))

        def base(logits: Any, targets: Any) -> Any:  # type: ignore[misc]
            return focal_loss(logits, targets, gamma, weight, label_smoothing)
    else:
        raise ValueError(f"loss.name phải thuộc {{cross_entropy, focal}}, nhận {name!r}")

    if bool(loss_config.get("deep_supervision", False)):
        return deep_supervision(base, float(loss_config.get("aux_weight", 1.0)))
    return base
