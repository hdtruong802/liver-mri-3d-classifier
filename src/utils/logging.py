"""Logger console + CSV ghi liên tục.

Kaggle session có thể bị ngắt bất cứ lúc nào (AGENTS.md §7) → CSV phải flush mỗi
dòng, không buffer đến cuối. `CsvLogger` mở file ở chế độ append và flush ngay.
"""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Any


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Trả về logger console đã cấu hình (idempotent)."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s | %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(level)
        logger.propagate = False
    return logger


class CsvLogger:
    """Ghi từng dòng metric ra CSV, flush ngay (an toàn khi Kaggle ngắt session).

    **Tôn trọng header đã có.** Nếu file tồn tại và đã có header thì `fieldnames` truyền
    vào bị bỏ qua, dùng đúng header trong file. Đây là chuyện của `resume`: một run bắt
    đầu trước khi schema đổi mà chạy tiếp sau khi schema đổi sẽ có những dòng nhiều cột
    hơn header, và file đó không đọc lại được bằng `csv.DictReader` nữa. Cột mới bị bỏ
    im lặng (`extrasaction="ignore"`) — mất một cột ở một run cũ thì chấp nhận được, còn
    làm hỏng cả file log thì không.
    """

    def __init__(self, path: str | Path, fieldnames: list[str]) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        existing = self._read_header()
        self.fieldnames = existing or list(fieldnames)
        # File cố ý giữ mở xuyên suốt vòng train (đóng ở close()/__exit__), không
        # dùng `with` cục bộ ở đây.
        self._fh = open(self.path, "a", newline="", encoding="utf-8")  # noqa: SIM115
        self._writer = csv.DictWriter(
            self._fh, fieldnames=self.fieldnames, extrasaction="ignore", restval=""
        )
        if existing is None:
            self._writer.writeheader()
            self._fh.flush()

    def _read_header(self) -> list[str] | None:
        """Header của file đã có, hoặc ``None`` nếu file chưa có / rỗng."""
        if not self.path.exists() or self.path.stat().st_size == 0:
            return None
        with open(self.path, newline="", encoding="utf-8") as f:
            row = next(csv.reader(f), None)
        return row or None

    def log(self, row: dict[str, Any]) -> None:
        """Ghi một dòng và flush ngay."""
        self._writer.writerow(row)
        self._fh.flush()

    def close(self) -> None:
        self._fh.close()

    def __enter__(self) -> CsvLogger:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
