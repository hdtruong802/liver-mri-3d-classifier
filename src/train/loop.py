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
    mixup_alpha: float = 0.0,
) -> dict[str, Any]:
    """Chạy một lượt qua loader. Có `optimizer` = train, không có = eval.

    `on_step` được gọi sau **mỗi** lần `optimizer.step()` thật sự chạy (tức là sau khi
    đã gom đủ `accum_steps`), không phải sau mỗi batch. Dùng cho EMA: hằng số thời gian
    của EMA tính theo số lần cập nhật trọng số, nên gọi nhầm nhịp sẽ làm nó trơn sai
    mức mà không có gì báo.

    ## `mixup_alpha` — trộn ảnh và trộn nhãn (Zhang và cs. 2018)

    ``0`` = tắt, và khi tắt thì đường code **y hệt** bản chưa có mixup (xem
    `tests/test_mixup.py`). ``> 0`` thì mỗi batch lấy λ ~ Beta(α, α), trộn batch với chính
    nó đã hoán vị, rồi tính ``λ·L(out, y) + (1−λ)·L(out, y[perm])``.

    **Chỉ áp khi train** (`optimizer is not None`). Trộn ở eval sẽ làm mọi con số báo cáo
    trở thành vô nghĩa, nên chốt ở đây thay vì tin người gọi.

    Vì sao mixup là can thiệp khớp với chẩn đoán ở `src/eval/weak_classes.py`: lỗi của model
    **cực kỳ tự tin** (biên trung vị 0.86–0.99, và 1/117 lỗi có biên < 0.10) và **trùng 74%
    giữa hai cấu hình khác augmentation**, tức là học thuộc chứ không phải nhiễu. Mixup tạo
    mẫu nội suy **giữa các lớp dễ lẫn** — đúng biên HCC/ICC/di căn — và trừng phạt việc tự
    tin tuyệt đối.

    ⚠️ ``train_loss`` trả về từ đây là loss **trên nhãn đã trộn**, nên **không so trực tiếp
    được** với `train_loss` của run không mixup. `val_loss` thì vẫn so được (eval không trộn).

    ⚠️ Khi mixup bật, ``probs``/``labels`` của **lượt train** ứng với ảnh đã trộn nên không
    dùng để tính metric được. Không sao trong đường chạy hiện tại: `src/train/run.py` chỉ
    đọc ``train_out["loss"]``, còn mọi metric và mọi `val_probs_*.npz` đều từ lượt **val**.

    ⚠️ **Không có thanh tiến độ ở đây, và đó là chủ ý** (WORKLOG S-122). Bản tqdm đã dựng
    rồi bỏ: ở Kaggle batch run (`Save & Run All`) nó vô dụng theo cả hai nhánh — bản
    widget không có frontend nào nhận cập nhật, còn bản text thì log lưu lại không gộp
    `\\r` nên thành hàng nghìn dòng lặp. Tiến độ theo epoch đã có ở `src/train/run.py`
    qua `logger.info`, và đó là thứ đọc được ở cả hai chế độ.

    Trả về ``{"loss", "labels", "probs", "patient_ids"}``. Xác suất được trả ra
    (không chỉ nhãn đoán) để W5 dùng lại đúng file này cho calibration và selective
    prediction mà không phải chạy lại model.
    """
    import torch

    training = optimizer is not None
    model.train(training)
    # Trộn CHỈ khi train. Trộn ở eval làm mọi con số báo cáo thành vô nghĩa, nên chốt ở đây
    # thay vì tin người gọi truyền đúng.
    mixup = float(mixup_alpha) if training else 0.0

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

            # Trộn ảnh TRƯỚC forward; nhãn trộn được xử lý ở phần loss bên dưới.
            perm, lam = None, 1.0
            if mixup > 0:
                # Dùng RNG của torch, KHÔNG dùng `np.random.default_rng()`: mọi tính ngẫu
                # nhiên của dự án đi qua `src/utils/seed.py::set_seed` (AGENTS.md §8), và
                # một RNG mới mỗi batch thì seed không còn nghĩa gì.
                lam = float(torch.distributions.Beta(mixup, mixup).sample())
                # Beta đối xứng nên λ và 1−λ tương đương; ép về nửa trên để λ luôn là
                # trọng số của mẫu GỐC, đọc log dễ hơn và không đổi phân bố phép trộn.
                lam = max(lam, 1.0 - lam)
                perm = torch.randperm(images.shape[0], device=images.device)
                images = lam * images + (1.0 - lam) * images[perm]

            with torch.autocast(device_type=device.type, dtype=torch.float16, enabled=amp):
                output = model(images)
                # Model có deep supervision (CGHNet) trả về dict `{"main", "aux"}` ở chế
                # độ train và tensor ở chế độ eval. Criterion nhận cả hai dạng (xem
                # `src.train.losses.deep_supervision`), nhưng metric và xác suất lưu ra
                # thì LUÔN chỉ tính trên đầu ra chính — nếu không thì `val_probs_*.npz`
                # trộn ba nguồn số vào cùng một file và về sau không ai phát hiện được.
                #
                # Với mixup phải gọi criterion HAI LẦN thay vì trộn nhãn thành one-hot:
                # criterion ở đây có thể là `deep_supervision(...)` nhận dict nhiều đầu ra,
                # và nó chỉ nhận nhãn dạng chỉ số lớp.
                if perm is None:
                    loss = criterion(output, labels)
                else:
                    loss = lam * criterion(output, labels) + (1.0 - lam) * criterion(
                        output, labels[perm]
                    )
            logits = output["main"] if isinstance(output, dict) else output

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
