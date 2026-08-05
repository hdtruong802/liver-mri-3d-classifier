"""Test-time augmentation bằng phép lật. Suy luận thuần, không train lại.

## Vì sao lật là phép TTA HỢP LỆ ở bài toán này

TTA chỉ đúng khi model *đáng lẽ* bất biến với phép biến đổi được dùng. Ở đây điều đó
không phải giả định mà là **sự thật của quá trình train**: `configs/baseline_3dpatch.yaml`
bật `flip_prob: 0.5` trên cả ba trục, nên mọi model của dự án đã được dạy để bất biến
với lật. Trung bình hoá qua các phép lật vì thế lấy lại đúng thứ augmentation đã dạy.

**Xoay 90° thì KHÔNG hợp lệ** dù nó cũng là phép biến đổi rời rạc rẻ tiền: gan nằm bên
phải, lách bên trái, cột sống phía sau — xoay 90° tạo ra giải phẫu không tồn tại, và
model chưa từng được dạy bất biến với nó (`rot90_prob: 0`, có chủ ý). Đừng thêm vào.

## Vì sao trung bình XÁC SUẤT chứ không phải logit

Trung bình logit rồi mới softmax cho kết quả khác, và nó khuếch đại lượt nào tự tin
nhất. Trung bình xác suất là trung bình của các phân phối — đúng thứ ta muốn, và giữ
được tính chất "tổng bằng 1" mà mọi phần calibration phía sau dựa vào.

## Cái giá

`2^k` lượt forward cho `k` trục. Với 3 trục là 8 lượt — vẫn rẻ vì đây là inference
(vài phút cho 394 ca), nhưng không miễn phí. `FLIP_SETS` cho phép chọn tập con.
"""

from __future__ import annotations

import itertools
from collections.abc import Sequence
from typing import Any

import numpy as np

from src.data.transforms import resolve_axes

__all__ = ["FLIP_SETS", "flip_combinations", "tta_predict"]

# Các tập trục dùng được, từ rẻ tới đắt. Trục ở đây tính trên tensor `[C, X, Y, Z]`
# **sau khi đã bỏ chiều batch** — `tta_predict` tự cộng 1 để bù chiều batch.
FLIP_SETS: dict[str, tuple[int, ...]] = {
    "none": (),
    "inplane": resolve_axes(["x", "y"]),  # 4 lượt
    "all": resolve_axes(["x", "y", "z"]),  # 8 lượt
}


def flip_combinations(axes: Sequence[int]) -> list[tuple[int, ...]]:
    """Mọi tổ hợp con của `axes`, kể cả tổ hợp rỗng (ảnh gốc).

    Trả về `2^len(axes)` phần tử. Tổ hợp rỗng **luôn đứng đầu** để lượt đầu tiên là
    ảnh gốc — nhờ vậy `probs[0]` so được trực tiếp với kết quả không TTA.
    """
    axes = tuple(axes)
    out: list[tuple[int, ...]] = []
    for size in range(len(axes) + 1):
        out.extend(itertools.combinations(axes, size))
    return out


def tta_predict(
    model: Any,
    loader: Any,
    device: Any,
    axes: Sequence[int] = FLIP_SETS["all"],
    amp: bool = True,
) -> dict[str, Any]:
    """Suy luận có TTA. Trả về ``{"probs", "probs_per_view", "labels", "patient_ids"}``.

    `probs` là trung bình qua các lượt; `probs_per_view` có dạng ``(V, N, C)`` để so
    từng lượt — cần nó vì nếu TTA làm *tệ* đi thì phải biết lượt nào gây ra.

    ⚠️ **Gọi `model.eval()` trước.** Hàm này tự gọi, nhưng nếu người gọi tính lớp đích
    hay xác suất ở ngoài mà quên `eval()` thì con số đó sai — đã dính một lần với
    Grad-CAM (WORKLOG S-096).
    """
    import torch

    views = flip_combinations(axes)
    was_training = model.training
    model.eval()

    per_view: list[np.ndarray] = []
    labels_ref: np.ndarray | None = None
    ids_ref: list[str] | None = None

    try:
        for view in views:
            probs_chunks: list[np.ndarray] = []
            labels_chunks: list[np.ndarray] = []
            ids: list[str] = []
            with torch.no_grad():
                for batch in loader:
                    images = batch["image"].to(device, non_blocking=True)
                    if view:
                        # +1 vì tensor ở đây có thêm chiều batch ở đầu.
                        images = torch.flip(images, dims=tuple(a + 1 for a in view))
                    with torch.autocast(device_type=device.type, dtype=torch.float16, enabled=amp):
                        logits = model(images)
                    probs_chunks.append(torch.softmax(logits.float(), dim=1).cpu().numpy())
                    labels_chunks.append(batch["label"].cpu().numpy())
                    ids.extend(batch["patient_id"])

            labels = np.concatenate(labels_chunks)
            if labels_ref is None:
                labels_ref, ids_ref = labels, ids
            elif ids != ids_ref:
                raise RuntimeError(
                    f"lượt {view} xếp ca khác thứ tự lượt đầu — loader phải shuffle=False"
                )
            per_view.append(np.concatenate(probs_chunks))
    finally:
        model.train(was_training)

    assert labels_ref is not None and ids_ref is not None
    stacked = np.stack(per_view)
    return {
        "probs": stacked.mean(axis=0),
        "probs_per_view": stacked,
        "labels": labels_ref,
        "patient_ids": ids_ref,
        "views": [list(v) for v in views],
    }
