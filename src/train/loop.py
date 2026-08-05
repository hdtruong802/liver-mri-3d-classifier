"""Các mảnh của vòng train, tách khỏi entrypoint để test được từng phần.

Ba thứ ở đây đáng đọc kỹ vì chúng là ràng buộc Kaggle chứ không phải sở thích:

- `save_checkpoint` ghi **nguyên tử** (file tạm rồi `replace`). Kaggle có thể cắt
  session giữa lúc ghi; nếu ghi thẳng vào `last.pt` thì lần resume sau sẽ gặp một
  checkpoint cụt và mất toàn bộ tiến trình.
- `class_weights_from_labels` chỉ nhận nhãn **train** — không bao giờ tính trên val
  (AGENTS.md §3.3).
- `make_amp_scaler` bọc qua hai API khác nhau của torch, vì phiên bản torch trên
  Kaggle không phải lúc nào cũng khớp `requirements.txt`.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

import numpy as np

from src.data.taxonomy import NUM_CLASSES


def class_weights_from_labels(labels: Sequence[int], num_classes: int = NUM_CLASSES) -> np.ndarray:
    """Trọng số lớp nghịch tần suất, chuẩn hoá về trung bình 1.

    Áp-xe và FNH chỉ vài chục ca trong 394 (EDA W2); nếu để cross-entropy trần thì
    model tối ưu được loss bằng cách bỏ hẳn hai lớp đó, mà đúng chúng lại là lớp
    macro-F1 phạt nặng nhất. Lớp vắng mặt nhận trọng số 1 (không chia cho 0).

    **Chỉ truyền nhãn của tập train.** Đếm cả val là leakage.
    """
    counts = np.bincount(np.asarray(labels, dtype=int), minlength=num_classes).astype(float)
    weights = np.ones(num_classes, dtype=np.float64)
    present = counts > 0
    weights[present] = counts[present].sum() / (present.sum() * counts[present])
    return weights


def make_amp_scaler(enabled: bool) -> Any:
    """GradScaler cho AMP, tương thích cả API cũ (`torch.cuda.amp`) lẫn mới (`torch.amp`)."""
    import torch

    try:
        return torch.amp.GradScaler("cuda", enabled=enabled)
    except (AttributeError, TypeError):  # torch < 2.4
        return torch.cuda.amp.GradScaler(enabled=enabled)


def save_checkpoint(path: str | Path, payload: dict[str, Any]) -> None:
    """Ghi checkpoint nguyên tử: `.tmp` trước, `replace` sau."""
    import torch

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.stem}.tmp{path.suffix}")
    torch.save(payload, tmp_path)
    tmp_path.replace(path)


def load_checkpoint(path: str | Path) -> dict[str, Any] | None:
    """Đọc checkpoint nếu có; trả ``None`` nếu chưa tồn tại (lần chạy đầu)."""
    import torch

    path = Path(path)
    if not path.exists():
        return None
    return torch.load(path, map_location="cpu", weights_only=False)


def run_epoch(
    model: Any,
    loader: Any,
    device: Any,
    criterion: Any,
    optimizer: Any | None = None,
    scaler: Any | None = None,
    accum_steps: int = 1,
    amp: bool = True,
    on_step: Callable[[], None] | None = None,
) -> dict[str, Any]:
    """Chạy một lượt qua loader. Có `optimizer` = train, không có = eval.

    `on_step` được gọi sau **mỗi** lần `optimizer.step()` thật sự chạy (tức là sau khi
    đã gom đủ `accum_steps`), không phải sau mỗi batch. Dùng cho EMA: hằng số thời gian
    của EMA tính theo số lần cập nhật trọng số, nên gọi nhầm nhịp sẽ làm nó trơn sai
    mức mà không có gì báo.

    Trả về ``{"loss", "labels", "probs", "patient_ids"}``. Xác suất được trả ra
    (không chỉ nhãn đoán) để W5 dùng lại đúng file này cho calibration và selective
    prediction mà không phải chạy lại model.
    """
    import torch

    training = optimizer is not None
    model.train(training)

    total_loss = 0.0
    total_count = 0
    all_labels: list[np.ndarray] = []
    all_probs: list[np.ndarray] = []
    all_ids: list[str] = []

    if training:
        optimizer.zero_grad(set_to_none=True)

    step = -1
    with torch.set_grad_enabled(training):
        for step, batch in enumerate(loader):
            images = batch["image"].to(device, non_blocking=True)
            labels = batch["label"].to(device, non_blocking=True)

            with torch.autocast(device_type=device.type, dtype=torch.float16, enabled=amp):
                logits = model(images)
                loss = criterion(logits, labels)

            if training:
                # Chia cho accum_steps để loss tích luỹ tương đương batch lớn.
                scaled = loss / accum_steps
                if scaler is not None and scaler.is_enabled():
                    scaler.scale(scaled).backward()
                else:
                    scaled.backward()

                if (step + 1) % accum_steps == 0:
                    if scaler is not None and scaler.is_enabled():
                        scaler.step(optimizer)
                        scaler.update()
                    else:
                        optimizer.step()
                    optimizer.zero_grad(set_to_none=True)
                    if on_step is not None:
                        on_step()

            batch_size = labels.shape[0]
            total_loss += float(loss.detach()) * batch_size
            total_count += batch_size
            all_labels.append(labels.detach().cpu().numpy())
            all_probs.append(torch.softmax(logits.detach().float(), dim=1).cpu().numpy())
            all_ids.extend(batch["patient_id"])

    # Batch cuối có thể chưa đủ accum_steps — vẫn phải cập nhật, không thì gradient
    # của phần đuôi bị vứt đi âm thầm.
    if training and (step + 1) % accum_steps != 0:
        if scaler is not None and scaler.is_enabled():
            scaler.step(optimizer)
            scaler.update()
        else:
            optimizer.step()
        optimizer.zero_grad(set_to_none=True)
        if on_step is not None:
            on_step()

    return {
        "loss": total_loss / max(total_count, 1),
        "labels": np.concatenate(all_labels) if all_labels else np.zeros(0, dtype=int),
        "probs": np.concatenate(all_probs) if all_probs else np.zeros((0, NUM_CLASSES)),
        "patient_ids": all_ids,
    }
