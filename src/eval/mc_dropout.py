"""MC-dropout: bất định epistemic từ MỘT checkpoint, không phải train thêm model.

## Vì sao module này tồn tại

Deep ensemble là cách chuẩn để đo bất định *epistemic* (mức bất đồng giữa các model).
Nhưng 5 checkpoint của CV **không** dùng làm ensemble để báo out-of-fold được: mỗi ca
ở val của fold `f` nằm trong tập train của **cả 4 model kia** (kiểm trực tiếp trên
`splits/`, WORKLOG S-080). Gộp chúng lại rồi chấm trên 394 ca là để 4/5 thành viên
chấm bài họ đã học thuộc — leakage, không phải ensemble.

MC-dropout né đúng chỗ đó: `K` lượt forward ngẫu nhiên **trên chính model của fold
đó**, nên mọi thành viên đều mù với val của nó. Đổi lại, nó là một xấp xỉ nghèo hơn
deep ensemble thật — các thành viên cùng cực tiểu, cùng bộ trọng số, nên đa dạng ít
hơn hẳn. Đây là bước đo trước khi quyết có đáng đốt 4 session Kaggle cho ensemble
nhiều seed hay không.

## Cạm bẫy: BatchNorm

`enable_dropout` chỉ bật lại **các lớp Dropout**, và cố ý để BatchNorm nguyên ở eval.
Gọi `model.train()` cho gọn sẽ kéo BatchNorm sang chế độ dùng thống kê của batch hiện
tại thay vì thống kê chạy — khi đó **dự đoán của một ca phụ thuộc vào những ca tình
cờ nằm cùng batch với nó**. Với `batch_size: 2` thì thống kê tính trên 2 mẫu, và kết
quả đổi theo thứ tự loader. Đó không còn là bất định của model nữa, mà là nhiễu do
cách chia batch — và nó sẽ trông y hệt một tín hiệu epistemic đẹp.

Config baseline dùng ``norm: batch`` nên bẫy này là thật, không phải giả định.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

__all__ = [
    "count_dropout_modules",
    "enable_dropout",
    "mc_dropout_predict",
    "save_member_probs",
]


def count_dropout_modules(model: Any) -> int:
    """Số lớp Dropout trong model.

    Gọi trước khi chạy: nếu bằng 0 thì MC-dropout **không làm gì cả** — `K` lượt
    forward sẽ cho ra `K` kết quả giống hệt nhau và epistemic bằng 0 trên mọi ca.
    Đó là một chế độ hỏng thầm lặng, phải chặn bằng assert chứ không để nó chạy.
    """
    import torch.nn as nn

    return sum(1 for m in model.modules() if isinstance(m, nn.modules.dropout._DropoutNd))


def enable_dropout(model: Any) -> int:
    """Đưa model về eval rồi bật lại **riêng** các lớp Dropout. Trả về số lớp đã bật.

    Xem ghi chú BatchNorm ở đầu module: đây là lý do hàm này tồn tại thay vì một lời
    gọi `model.train()`.
    """
    import torch.nn as nn

    model.eval()
    count = 0
    for module in model.modules():
        if isinstance(module, nn.modules.dropout._DropoutNd):
            module.train()
            count += 1
    return count


def mc_dropout_predict(
    model: Any,
    loader: Any,
    device: Any,
    n_passes: int = 20,
    amp: bool = True,
    seed: int = 1337,
) -> dict[str, Any]:
    """`n_passes` lượt forward có dropout; trả về xác suất từng thành viên.

    Trả về ``{"member_probs": (K, N, C), "labels": (N,), "patient_ids": [N], "n_passes"}``
    — đúng dạng mà `src.eval.selective.uncertainty_decomposition` nhận vào.

    `loader` phải **không xáo trộn** (`shuffle=False`) để `N` lượt xếp cùng thứ tự
    giữa các pass; hàm kiểm điều đó qua `patient_ids` và nổ nếu lệch, vì một lỗi kiểu
    này không tự lộ ra ở đâu khác ngoài các con số bất định trông hơi lạ.
    """
    import torch

    n_dropout = enable_dropout(model)
    if n_dropout == 0:
        raise RuntimeError(
            "model không có lớp Dropout nào — MC-dropout sẽ cho K kết quả giống hệt "
            "nhau và epistemic = 0 khắp nơi. Kiểm lại `model.dropout_prob` trong config."
        )

    members: list[np.ndarray] = []
    labels_ref: np.ndarray | None = None
    ids_ref: list[str] | None = None

    for pass_index in range(n_passes):
        # Seed lại mỗi pass để chạy lại cho ra đúng cùng bộ số (AGENTS.md §8).
        torch.manual_seed(seed + pass_index)
        probs_chunks: list[np.ndarray] = []
        labels_chunks: list[np.ndarray] = []
        ids: list[str] = []

        with torch.no_grad():
            for batch in loader:
                images = batch["image"].to(device, non_blocking=True)
                with torch.autocast(device_type=device.type, dtype=torch.float16, enabled=amp):
                    logits = model(images)
                probs_chunks.append(torch.softmax(logits.float(), dim=1).cpu().numpy())
                labels_chunks.append(batch["label"].cpu().numpy())
                ids.extend(batch["patient_id"])

        probs = np.concatenate(probs_chunks)
        labels = np.concatenate(labels_chunks)

        if labels_ref is None:
            labels_ref, ids_ref = labels, ids
        elif ids != ids_ref:
            raise RuntimeError(
                f"pass {pass_index} xếp ca khác thứ tự pass 0 — loader phải shuffle=False"
            )
        members.append(probs)

    assert labels_ref is not None and ids_ref is not None
    return {
        "member_probs": np.stack(members),
        "labels": labels_ref,
        "patient_ids": ids_ref,
        "n_passes": n_passes,
    }


def save_member_probs(path: str | Path, result: dict[str, Any]) -> Path:
    """Ghi kết quả ra `.npz` để máy local đọc lại mà không cần GPU."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        out,
        member_probs=result["member_probs"],
        labels=np.asarray(result["labels"], dtype=np.int64),
        patient_ids=np.asarray(result["patient_ids"]),
        n_passes=result["n_passes"],
    )
    return out
