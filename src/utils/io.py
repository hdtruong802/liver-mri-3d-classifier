"""IO tiện ích: đọc YAML/JSON, resolve đường dẫn data root qua config/env."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def load_yaml(path: str | Path) -> dict[str, Any]:
    """Đọc file YAML thành dict."""
    import yaml

    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_json(path: str | Path) -> Any:
    """Đọc file JSON."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def read_id_class_file(path: str | Path) -> list[tuple[str, int]]:
    """Đọc file split dạng LLD-MMRI: mỗi dòng ``<patient_id> <class_idx>``."""
    rows: list[tuple[str, int]] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            pid, cls = line.split()
            rows.append((pid, int(cls)))
    return rows


def resolve_data_root(config: dict[str, Any]) -> Path:
    """Lấy data_root: ưu tiên env LLDMMRI_DATA_ROOT, sau đó config['data_root'].

    Không hardcode `/kaggle/...` trong code — mọi path ghi qua đây (AGENTS.md §7).

    Thứ tự ưu tiên:
    1. env ``LLDMMRI_DATA_ROOT`` (dùng nguyên, không kiểm tra — người dùng chủ động);
    2. các ứng viên trong ``config['data_root_candidates']``, **chỉ nhận cái thật sự
       chứa file annotation** — vì Kaggle đổi sơ đồ mount tuỳ lúc
       (`/kaggle/input/<slug>` vs `/kaggle/input/datasets/<owner>/<slug>`);
    3. ``config['data_root']`` (mặc định cho máy local).

    Bước 2 xác minh bằng sự tồn tại của annotation chứ không chỉ `is_dir()` — một
    thư mục rỗng tồn tại vẫn khiến mọi bước sau **thất bại âm thầm** (WORKLOG S-025).
    """
    env_root = os.environ.get("LLDMMRI_DATA_ROOT")
    if env_root:
        return Path(env_root)

    annotation_rel = config.get("annotation_rel", "")
    tried: list[str] = []
    for candidate in config.get("data_root_candidates") or []:
        tried.append(str(candidate))
        if annotation_rel and (Path(candidate) / annotation_rel).exists():
            return Path(candidate)

    root = config.get("data_root")
    if not root:
        raise ValueError(
            "không tìm được data_root. Đặt env LLDMMRI_DATA_ROOT, hoặc thêm đường dẫn "
            f"vào data_root_candidates trong config. Đã thử: {tried or '(không có ứng viên)'}"
        )
    return Path(root)
