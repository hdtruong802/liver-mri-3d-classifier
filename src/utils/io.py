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
    """Tìm thư mục gốc dữ liệu, ưu tiên env rồi tới các ứng viên trong config.

    Không hardcode `/kaggle/...` trong code — mọi path đi qua đây (AGENTS.md §7).

    Thứ tự:
    1. env ``LLDMMRI_DATA_ROOT`` **nếu nó thật sự chứa annotation**;
    2. các ứng viên trong ``config['data_root_candidates']`` (cũng phải chứa annotation)
       — Kaggle đổi sơ đồ mount tuỳ lúc: `/kaggle/input/<slug>` vs
       `/kaggle/input/datasets/<owner>/<slug>`;
    3. env dù không xác minh được (tôn trọng ý định người dùng, có cảnh báo);
    4. ``config['data_root']`` (mặc định máy local).

    **Xác minh bằng sự tồn tại của annotation, không phải `is_dir()`** — thư mục rỗng
    vẫn tồn tại và khiến mọi bước sau thất bại âm thầm (WORKLOG S-025).

    Env cũng bị xác minh vì một lý do rất thực tế (WORKLOG S-027): env đặt ở lần chạy
    trước **còn sót trong process Jupyter** sau khi `git pull`; nếu env được tin tuyệt
    đối thì giá trị cũ sẽ đè lên config mới và ta lại đi vào đúng cái bẫy vừa sửa.
    """
    annotation_rel = config.get("annotation_rel", "")

    def has_annotation(root: str | Path) -> bool:
        return bool(annotation_rel) and (Path(root) / annotation_rel).exists()

    env_root = os.environ.get("LLDMMRI_DATA_ROOT")
    if env_root and has_annotation(env_root):
        return Path(env_root)

    tried: list[str] = []
    for candidate in config.get("data_root_candidates") or []:
        tried.append(str(candidate))
        if has_annotation(candidate):
            return Path(candidate)

    if env_root:
        print(
            f"CẢNH BÁO: LLDMMRI_DATA_ROOT={env_root!r} không chứa {annotation_rel!r} "
            "và không ứng viên nào khớp. Nếu đang chạy trong Jupyter, đây có thể là "
            "env sót lại từ lần chạy trước — hãy Restart kernel."
        )
        return Path(env_root)

    root = config.get("data_root")
    if not root:
        raise ValueError(
            "không tìm được data_root. Đặt env LLDMMRI_DATA_ROOT, hoặc thêm đường dẫn "
            f"vào data_root_candidates trong config. Đã thử: {tried or '(không có ứng viên)'}"
        )
    return Path(root)
