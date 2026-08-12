"""Đường dẫn và ngưỡng của lớp serve.

Mọi đường dẫn đi qua biến môi trường (`AGENTS.md` §7: không hardcode đường dẫn rải
rác trong code). Không có giá trị nào ở đây là hyperparam khoa học — ngưỡng `defer`
thật sẽ được khoá trên validation và nạp cùng prediction store; con số dưới đây chỉ
là default cho utility thuần, không được dùng để dựng prediction upload.
"""

from __future__ import annotations

import os
from pathlib import Path

# Gốc repo: webapp/backend/config.py -> webapp/backend -> webapp -> repo
REPO_ROOT = Path(__file__).resolve().parents[2]


def _env_path(name: str, default: Path) -> Path:
    raw = os.environ.get(name)
    return Path(raw).expanduser() if raw else default


# Dữ liệu bệnh nhân thật. `data/` bị .gitignore toàn bộ, và phải giữ nguyên như vậy:
# đây là volume MRI của người thật (`AGENTS.md` §3.10). App đọc lúc chạy, không copy
# vào webapp/, không commit, không đi kèm khi đem demo lên host công khai.
SAMPLE_DIR: Path = _env_path("LLDMMRI_SAMPLE_DIR", REPO_ROOT / "data" / "sample")

# Checkpoint. Chưa có — W5 mới nạp model thật.
CHECKPOINT_PATH: Path | None = (
    Path(os.environ["LLDMMRI_CHECKPOINT"]) if os.environ.get("LLDMMRI_CHECKPOINT") else None
)

# Ngưỡng mặc định cho utility thuần. Quy tắc defer của prediction OOF được nạp cùng store,
# đã khóa trên validation; UI không dùng giá trị này để dựng kết quả tải lên.
DEFAULT_DEFER_THRESHOLD: float = float(os.environ.get("LLDMMRI_DEFER_THRESHOLD", "0.55"))

RUO_NOTICE: str = "Research Use Only: chưa kiểm định lâm sàng"

# Số lát tối đa render trong một phiên trước khi cache bị cắt bớt. Volume 8 thì của
# một ca cỡ 20-160 lát mỗi thì; giữ trần để phiên dài không phình bộ nhớ.
SLICE_CACHE_SIZE: int = int(os.environ.get("LLDMMRI_SLICE_CACHE", "512"))
