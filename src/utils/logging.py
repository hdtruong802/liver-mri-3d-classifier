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
    """Ghi từng dòng metric ra CSV, flush ngay (an toàn khi Kaggle ngắt session)."""

    def __init__(self, path: str | Path, fieldnames: list[str]) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.fieldnames = fieldnames
        write_header = not self.path.exists() or self.path.stat().st_size == 0
        # File cố ý giữ mở xuyên suốt vòng train (đóng ở close()/__exit__), không
        # dùng `with` cục bộ ở đây.
        self._fh = open(self.path, "a", newline="", encoding="utf-8")  # noqa: SIM115
        self._writer = csv.DictWriter(self._fh, fieldnames=fieldnames)
        if write_header:
            self._writer.writeheader()
            self._fh.flush()

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
