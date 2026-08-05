"""Trung bình trượt luỹ thừa của trọng số (EMA).

## Vì sao dự án này cần nó, cụ thể

Không phải vì "EMA thường tốt hơn". Vì một con số đã đo được: **thiên lệch do chọn
epoch là +0.079** (WORKLOG S-078). Checkpoint `best` được chọn theo macro-F1 trên đúng
tập val đang báo cáo, nên 0.6851 lệch lạc quan; `last` cho 0.6038 trên cùng dữ liệu.
Khoảng cách đó phần lớn là nhiễu giữa các epoch, không phải năng lực thật.

EMA tấn công đúng chỗ đó: trọng số EMA là trung bình trượt của **hàng nghìn** bước,
nên nó không nhảy theo từng epoch. Hai cái lợi tách bạch:

1. Model EMA thường tốt hơn model tức thời (lợi về hiệu năng).
2. Nó **bớt phụ thuộc vào việc chọn đúng epoch** (lợi về tính trung thực của con số) —
   và đây mới là lý do chính ở dự án lấy trustworthiness làm đóng góp.

## Cạm bẫy: buffer KHÔNG được trung bình như tham số

`state_dict()` của model trộn hai thứ khác hẳn nhau:

- **tham số** (`weight`, `bias`) — học bằng gradient, EMA đúng và có ý nghĩa;
- **buffer** (`running_mean`, `running_var`, `num_batches_tracked` của BatchNorm) —
  bản thân **đã là** thống kê trượt do BatchNorm tự duy trì. EMA chồng lên chúng là
  làm trơn hai lần, và `num_batches_tracked` là số nguyên đếm bước — trung bình nó
  ra một con số vô nghĩa.

Nên lớp này **chỉ EMA tham số**, và **sao chép** buffer từ model gốc. Đây là cách
`timm` và `torch.optim.swa_utils.AveragedModel` làm; ghi ra đây vì nếu ai đó "đơn giản
hoá" thành EMA cả `state_dict` thì nó vẫn chạy, vẫn ra số, và số đó sai.
"""

from __future__ import annotations

from typing import Any

__all__ = ["ModelEma"]


class ModelEma:
    """Giữ một bản sao trọng số được trung bình trượt.

    ``ema ← decay · ema + (1 − decay) · param`` sau **mỗi bước cập nhật optimizer**
    (không phải mỗi epoch — số lần cập nhật là thứ quyết định hằng số thời gian).

    `decay` gần 1 thì trơn hơn nhưng bám chậm hơn. Với fold này: 312 mẫu train,
    batch 2 ⇒ ~156 bước/epoch, 300 epoch ⇒ ~47k bước. `decay=0.999` cho hằng số thời
    gian ~1000 bước ≈ 6 epoch — đủ để lọc nhiễu giữa các epoch mà vẫn theo kịp xu
    hướng học. Đó là lý do chọn mặc định này, không phải vì nó phổ biến.

    ⚠️ **Warmup của EMA.** Những bước đầu, `ema` vẫn còn phần lớn là trọng số khởi
    tạo ngẫu nhiên. `use_num_updates=True` bù bằng cách dùng decay nhỏ hơn lúc đầu
    (công thức của TensorFlow), nếu không thì vài epoch đầu EMA tệ hơn hẳn model
    thường và biểu đồ trông như EMA hỏng.
    """

    def __init__(
        self,
        model: Any,
        decay: float = 0.999,
        use_num_updates: bool = True,
    ) -> None:
        import copy

        import torch

        if not 0.0 < decay < 1.0:
            raise ValueError(f"decay phải trong (0, 1), nhận {decay}")

        self.decay = float(decay)
        self.use_num_updates = bool(use_num_updates)
        self.num_updates = 0
        self._torch = torch
        # `deepcopy` rồi tắt gradient: bản EMA không bao giờ được train.
        self.module = copy.deepcopy(model).eval()
        for parameter in self.module.parameters():
            parameter.requires_grad_(False)

    def _current_decay(self) -> float:
        if not self.use_num_updates:
            return self.decay
        # Công thức warmup của TensorFlow: decay hiệu dụng nhỏ hơn khi mới bắt đầu.
        return min(self.decay, (1.0 + self.num_updates) / (10.0 + self.num_updates))

    @property
    def torch_module(self) -> Any:
        """Model EMA, dùng để đánh giá. Luôn ở chế độ eval."""
        return self.module

    def update(self, model: Any) -> None:
        """Một bước EMA. Gọi sau **mỗi** `optimizer.step()`."""
        self.num_updates += 1
        decay = self._current_decay()
        with self._torch.no_grad():
            ema_params = dict(self.module.named_parameters())
            for name, param in model.named_parameters():
                ema_params[name].mul_(decay).add_(param.detach(), alpha=1.0 - decay)

            # Buffer: SAO CHÉP, không trung bình. Xem docstring module.
            ema_buffers = dict(self.module.named_buffers())
            for name, buffer in model.named_buffers():
                ema_buffers[name].copy_(buffer)

    def state_dict(self) -> dict[str, Any]:
        return {"module": self.module.state_dict(), "num_updates": self.num_updates}

    def load_state_dict(self, state: dict[str, Any]) -> None:
        self.module.load_state_dict(state["module"])
        self.num_updates = int(state.get("num_updates", 0))
