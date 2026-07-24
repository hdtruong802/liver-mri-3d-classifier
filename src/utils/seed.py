"""Randomness đi qua MỘT chỗ duy nhất (AGENTS.md §8).

Gọi `set_seed()` ở đầu mọi entrypoint. Không rải `random.seed()` / `np.random.seed()`
rải rác nơi khác — làm vậy khiến thí nghiệm không tái lập được.
"""

from __future__ import annotations

import os
import random


def set_seed(seed: int, *, deterministic: bool = True) -> None:
    """Đặt seed cho random / numpy / torch (nếu có mặt) + cờ deterministic.

    numpy và torch được import lười (lazy) để module này dùng được cả khi chưa cài
    deep-learning stack (vd lúc chỉ chạy tiền xử lý / build manifest).

    Args:
        seed: seed cố định, lấy từ config YAML, không hardcode nơi khác.
        deterministic: bật cờ cudnn deterministic (chậm hơn nhưng tái lập).
    """
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)

    try:
        import numpy as np

        np.random.seed(seed)
    except ImportError:
        pass

    try:
        import torch

        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        if deterministic:
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    except ImportError:
        pass
