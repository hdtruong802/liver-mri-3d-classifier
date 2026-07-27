"""Kiểm tra tỉnh táo: model có **học nổi vài mẫu** không, trước khi train thật.

Đây là phép thử chuẩn để phân biệt hai chuyện rất khác nhau mà nhìn log train thì
giống nhau:

- *bài toán khó* — model học được nhưng chậm, cần thêm epoch/dữ liệu;
- *pipeline hỏng* — model **không thể** học, dù chỉ 8 mẫu lặp đi lặp lại.

Một model lành mạnh phải nhồi được 8 mẫu tới gần như thuộc lòng (loss → ~0,
accuracy → 1.0) trong vài chục bước. Không làm nổi việc đó thì lỗi nằm ở kiến trúc
hoặc đường dữ liệu, và train 60 epoch chỉ tốn thêm thời gian để khẳng định lại.

Bài học dẫn tới file này (WORKLOG S-039): đổi `norm` sang InstanceNorm làm model sập
về đoán một lớp duy nhất, và phải mất một run 20 phút mới thấy. Phép thử ở đây tốn
~30 giây mỗi phương án.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from src.data.taxonomy import NUM_CLASSES
from src.utils.logging import get_logger

logger = get_logger(__name__)


def pick_diverse_subset(labels: Sequence[int], n_samples: int) -> list[int]:
    """Chọn chỉ số mẫu sao cho **trải qua nhiều lớp nhất có thể**.

    Lấy `n_samples` mẫu đầu danh sách là cách hỏng: fold có thể xếp liền nhau nhiều
    ca cùng lớp, và một tập con chỉ có một lớp thì loss về 0 mà chẳng chứng minh gì.
    Ở đây quay vòng qua các lớp, mỗi vòng lấy một mẫu của mỗi lớp.
    """
    by_class: dict[int, list[int]] = {}
    for index, label in enumerate(labels):
        by_class.setdefault(int(label), []).append(index)

    picked: list[int] = []
    round_index = 0
    while len(picked) < n_samples:
        added = False
        for label in sorted(by_class):
            if round_index < len(by_class[label]):
                picked.append(by_class[label][round_index])
                added = True
                if len(picked) == n_samples:
                    break
        if not added:  # đã lấy hết mẫu có sẵn
            break
        round_index += 1
    return picked


def overfit_check(
    dataset: Any,
    model: Any,
    device: Any,
    n_samples: int = 8,
    passes: int = 40,
    batch_size: int = 2,
    lr: float = 1e-3,
) -> dict[str, float]:
    """Nhồi `n_samples` mẫu vào model và xem nó có thuộc bài không.

    Cố ý **không** dùng augmentation, class weight hay scheduler: mục tiêu là hỏi
    "kiến trúc này có khả năng khớp dữ liệu không", không phải "cấu hình train này
    tốt không". Càng ít biến càng dễ đọc kết quả.

    Trả về ``{"loss_start", "loss_end", "accuracy_end", "n_classes"}``.
    """
    import torch
    from torch.utils.data import DataLoader, Subset

    labels = [label for _, label, _ in dataset.samples]
    indices = pick_diverse_subset(labels, n_samples)
    subset = Subset(dataset, indices)
    n_classes = len({labels[i] for i in indices})

    loader = DataLoader(subset, batch_size=batch_size, shuffle=False)
    criterion = torch.nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr)

    model.to(device)
    model.train()

    loss_start = float("nan")
    loss_end = float("nan")
    correct = 0

    for pass_index in range(passes):
        total_loss = 0.0
        correct = 0
        for batch in loader:
            images = batch["image"].to(device)
            targets = batch["label"].to(device)

            logits = model(images)
            loss = criterion(logits, targets)

            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()

            total_loss += float(loss.detach()) * targets.shape[0]
            correct += int((logits.detach().argmax(dim=1) == targets).sum())

        loss_end = total_loss / len(indices)
        if pass_index == 0:
            loss_start = loss_end

    return {
        "loss_start": loss_start,
        "loss_end": loss_end,
        "accuracy_end": correct / len(indices),
        "n_classes": float(n_classes),
    }


def verdict(result: dict[str, float], num_classes: int = NUM_CLASSES) -> str:
    """Đọc kết quả `overfit_check` thành một chữ: HỌC ĐƯỢC / CHẬM / SẬP.

    Mốc so sánh là loss của phép đoán ngẫu nhiên, ``ln(num_classes)`` ≈ 1.946 với 7
    lớp — con số đã thấy y nguyên trong log của bản InstanceNorm.
    """
    import math

    chance = math.log(num_classes)
    if result["accuracy_end"] >= 0.99 or result["loss_end"] < 0.1:
        return "HỌC ĐƯỢC"
    if result["loss_end"] < chance * 0.75:
        return "CHẬM"
    return "SẬP"
