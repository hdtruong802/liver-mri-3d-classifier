"""IO tiện ích: đọc YAML/JSON, resolve đường dẫn data root qua config/env."""

from __future__ import annotations

import json
import os
from collections.abc import Sequence
from pathlib import Path, PurePosixPath
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


CACHE_META_NAME = "cache_meta.json"


def resolve_cache_dir(config: dict[str, Any]) -> Path:
    """Thư mục cache đã tiền xử lý: env ``LLDMMRI_CACHE_DIR`` thắng, sau đó config."""
    return Path(os.environ.get("LLDMMRI_CACHE_DIR") or config["cache_dir"])


def find_cache_dir(
    search_roots: Sequence[str | Path],
    max_depth: int = 4,
    min_npz: int = 1,
) -> Path | None:
    """Lùng thư mục cache dưới các gốc cho trước; ``None`` nếu không thấy.

    Cùng triết lý với `discover_data_root`: **không đoán sơ đồ mount của Kaggle**,
    cứ tìm bằng nội dung thật. Hai lượt:

    1. thư mục nào chứa ``cache_meta.json`` — bằng chứng chắc chắn nhất;
    2. thư mục nào chứa ít nhất ``min_npz`` file ``.npz`` — cứu được trường hợp
       cache được đóng gói lại mà rơi mất file metadata.

    Ưu tiên theo **độ sâu tăng dần**: mount nông thường là bản chính, các thư mục
    lồng sâu hơn dễ là bản sao/giải nén tạm.
    """
    roots = [Path(root) for root in search_roots if Path(root).is_dir()]

    for depth in range(max_depth + 1):
        prefix = ["*"] * depth
        for base in roots:
            for hit in sorted(base.glob("/".join([*prefix, CACHE_META_NAME]))):
                if hit.is_file():
                    return hit.parent

    for depth in range(max_depth + 1):
        prefix = ["*"] * depth
        for base in roots:
            for hit in sorted(base.glob("/".join([*prefix, "*.npz"]))):
                if len(list(hit.parent.glob("*.npz"))) >= min_npz:
                    return hit.parent
    return None


def describe_tree(root: str | Path, max_depth: int = 2, max_entries: int = 30) -> list[str]:
    """Liệt kê nông nội dung một thư mục — để thông báo lỗi nói được *đang thấy gì*.

    Một dòng "không thấy cache" mà không kèm thực tế đang mount cái gì thì bắt người
    dùng phải tự mò; đây là phần bù cho điều đó. Thư mục hiện kèm số file bên trong.
    """
    base = Path(root)
    if not base.is_dir():
        return [f"{base} — không tồn tại"]

    lines: list[str] = []
    for depth in range(max_depth + 1):
        for entry in sorted(base.glob("/".join(["*"] * (depth + 1)))):
            if entry.is_dir():
                children = list(entry.iterdir())
                suffix_counts: dict[str, int] = {}
                for child in children:
                    suffix_counts[child.suffix or "<dir>"] = (
                        suffix_counts.get(child.suffix or "<dir>", 0) + 1
                    )
                detail = ", ".join(f"{n}{s}" for s, n in sorted(suffix_counts.items()))
                lines.append(f"{entry}/  ({len(children)} mục: {detail or 'rỗng'})")
            else:
                lines.append(f"{entry}  ({entry.stat().st_size / 1e6:.1f} MB)")
            if len(lines) >= max_entries:
                lines.append("... (còn nữa)")
                return lines
    return lines or [f"{base} — rỗng"]


def resolve_output_dir(config: dict[str, Any]) -> Path:
    """Thư mục ghi của một run: env ``LLDMMRI_OUTPUT_DIR`` thắng, sau đó config.

    Trên Kaggle, ổ ghi được duy nhất là output dir (AGENTS.md §7) — nên đường dẫn
    ghi phải đi qua đây, không hardcode ``/kaggle/working`` rải rác trong code.
    """
    return Path(os.environ.get("LLDMMRI_OUTPUT_DIR") or config["output_dir"])


def discover_data_root(
    config: dict[str, Any],
    search_roots: Sequence[str | Path] | None = None,
    max_depth: int = 4,
) -> Path | None:
    """Lùng file annotation dưới các thư mục tìm kiếm -> suy ra data root.

    Đây là cách **bền nhất**: không phụ thuộc vào việc đoán đúng sơ đồ mount của
    Kaggle. Đã đoán sai hai lần (`/kaggle/input/<slug>` vs
    `/kaggle/input/datasets/<owner>/<slug>`) nên thôi đoán — cứ tìm file thật.

    Dùng glob giới hạn độ sâu thay vì `**` để không phải duyệt toàn bộ cây 83.7GB.
    Trả về ``None`` nếu không tìm thấy.
    """
    annotation_rel = config.get("annotation_rel", "")
    if not annotation_rel:
        return None

    rel = PurePosixPath(str(annotation_rel).replace("\\", "/"))
    depth_of_rel = len(rel.parts)
    roots = search_roots if search_roots is not None else (config.get("data_root_search") or [])

    for base in roots:
        base_path = Path(base)
        if not base_path.is_dir():
            continue
        for depth in range(max_depth + 1):
            pattern = "/".join(["*"] * depth + [str(rel)])
            for hit in sorted(base_path.glob(pattern)):
                if hit.is_file():
                    return hit.parents[depth_of_rel - 1]
    return None


def resolve_data_root(config: dict[str, Any]) -> Path:
    """Tìm thư mục gốc dữ liệu; xác minh bằng annotation ở mọi bước.

    Không hardcode `/kaggle/...` trong code — mọi path đi qua đây (AGENTS.md §7).

    Thứ tự:
    1. env ``LLDMMRI_DATA_ROOT`` **nếu nó thật sự chứa annotation**;
    2. các ứng viên trong ``config['data_root_candidates']`` (cũng phải chứa annotation);
    3. **tự lùng** annotation dưới ``config['data_root_search']`` (vd `/kaggle/input`)
       — không cần biết trước sơ đồ mount;
    4. env dù không xác minh được (tôn trọng ý định người dùng, có cảnh báo);
    5. ``config['data_root']`` (mặc định máy local).

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

    discovered = discover_data_root(config)
    if discovered is not None:
        return discovered

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
