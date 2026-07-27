"""Test resolve_data_root — dò data root theo ứng viên, có xác minh.

Kaggle đổi sơ đồ mount (`/kaggle/input/<slug>` vs `/kaggle/input/datasets/<owner>/<slug>`)
nên không được hardcode. Quan trọng hơn: phải **xác minh bằng annotation**, vì thư
mục rỗng tồn tại vẫn khiến mọi bước sau thất bại âm thầm (WORKLOG S-025).
"""

from pathlib import Path

import pytest
from src.utils.io import discover_data_root, resolve_data_root

ANNOTATION_REL = "lld/LLD_MMRI_Annotation.json"


def _make_root(base: Path, name: str, *, with_annotation: bool) -> Path:
    root = base / name
    (root / "lld").mkdir(parents=True)
    if with_annotation:
        (root / ANNOTATION_REL).write_text("{}", encoding="utf-8")
    return root


def test_valid_env_var_wins_over_candidates(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Env trỏ tới data thật -> thắng, kể cả khi ứng viên cũng hợp lệ."""
    env_root = _make_root(tmp_path, "from_env", with_annotation=True)
    cand = _make_root(tmp_path, "cand", with_annotation=True)
    monkeypatch.setenv("LLDMMRI_DATA_ROOT", str(env_root))
    config = {
        "data_root": str(tmp_path / "local"),
        "data_root_candidates": [str(cand)],
        "annotation_rel": ANNOTATION_REL,
    }
    assert resolve_data_root(config) == env_root


def test_stale_env_var_loses_to_valid_candidate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Bẫy có thật (S-027): env sót lại từ lần chạy trước trỏ vào chỗ không có data.

    Trong Jupyter, env đặt ở lần chạy trước vẫn nằm trong process sau `git pull`.
    Nếu tin env tuyệt đối thì giá trị cũ đè lên config mới. Phải ưu tiên ứng viên
    thật sự chứa annotation.
    """
    monkeypatch.setenv("LLDMMRI_DATA_ROOT", str(tmp_path / "stale_nonexistent"))
    real = _make_root(tmp_path, "real", with_annotation=True)
    config = {
        "data_root_candidates": [str(real)],
        "annotation_rel": ANNOTATION_REL,
    }
    assert resolve_data_root(config) == real


def test_env_used_as_last_resort_with_warning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
):
    """Env không xác minh được VÀ không ứng viên nào khớp -> vẫn dùng env, có cảnh báo."""
    monkeypatch.setenv("LLDMMRI_DATA_ROOT", str(tmp_path / "only_option"))
    config = {
        "data_root_candidates": [str(tmp_path / "nope")],
        "annotation_rel": ANNOTATION_REL,
    }
    assert resolve_data_root(config) == tmp_path / "only_option"
    assert "CẢNH BÁO" in capsys.readouterr().out


def test_picks_candidate_that_has_annotation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("LLDMMRI_DATA_ROOT", raising=False)
    empty = _make_root(tmp_path, "empty", with_annotation=False)
    real = _make_root(tmp_path, "real", with_annotation=True)

    config = {
        "data_root": str(tmp_path / "local"),
        "data_root_candidates": [str(empty), str(real)],
        "annotation_rel": ANNOTATION_REL,
    }
    # Ứng viên đầu tồn tại nhưng KHÔNG có annotation -> phải bỏ qua, chọn cái thứ hai.
    assert resolve_data_root(config) == real


def test_candidate_order_respected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("LLDMMRI_DATA_ROOT", raising=False)
    first = _make_root(tmp_path, "first", with_annotation=True)
    second = _make_root(tmp_path, "second", with_annotation=True)

    config = {
        "data_root_candidates": [str(first), str(second)],
        "annotation_rel": ANNOTATION_REL,
    }
    assert resolve_data_root(config) == first


def test_falls_back_to_data_root_when_no_candidate_matches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.delenv("LLDMMRI_DATA_ROOT", raising=False)
    config = {
        "data_root": "data/lldmmridataset",
        "data_root_candidates": [str(tmp_path / "nope")],
        "annotation_rel": ANNOTATION_REL,
    }
    assert resolve_data_root(config) == Path("data/lldmmridataset")


def test_raises_with_tried_paths_when_nothing_found(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.delenv("LLDMMRI_DATA_ROOT", raising=False)
    config = {
        "data_root_candidates": [str(tmp_path / "nope")],
        "annotation_rel": ANNOTATION_REL,
    }
    with pytest.raises(ValueError, match="nope"):  # báo rõ đã thử đường nào
        resolve_data_root(config)


def test_works_without_candidates_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Config cũ (không có data_root_candidates) vẫn chạy."""
    monkeypatch.delenv("LLDMMRI_DATA_ROOT", raising=False)
    assert resolve_data_root({"data_root": "x/y"}) == Path("x/y")


# --- Tự lùng annotation: không cần đoán đúng sơ đồ mount (S-028) ---


def test_discover_finds_root_at_depth_one(tmp_path: Path):
    """Sơ đồ /kaggle/input/<slug>/lld/annotation.json"""
    root = _make_root(tmp_path / "input", "lldmmridataset", with_annotation=True)
    config = {"annotation_rel": ANNOTATION_REL, "data_root_search": [str(tmp_path / "input")]}
    assert discover_data_root(config) == root


def test_discover_finds_root_at_depth_three(tmp_path: Path):
    """Sơ đồ thật của Kaggle: /kaggle/input/datasets/<owner>/<slug>/lld/annotation.json"""
    base = tmp_path / "input"
    root = _make_root(base / "datasets" / "marcohoang", "lldmmridataset", with_annotation=True)
    config = {"annotation_rel": ANNOTATION_REL, "data_root_search": [str(base)]}
    assert discover_data_root(config) == root


def test_discover_returns_none_when_absent(tmp_path: Path):
    (tmp_path / "input").mkdir()
    config = {"annotation_rel": ANNOTATION_REL, "data_root_search": [str(tmp_path / "input")]}
    assert discover_data_root(config) is None


def test_discover_ignores_missing_search_root(tmp_path: Path):
    config = {"annotation_rel": ANNOTATION_REL, "data_root_search": [str(tmp_path / "nope")]}
    assert discover_data_root(config) is None


def test_resolve_falls_back_to_discovery(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Ứng viên trong config đều sai, nhưng vẫn tìm ra data nhờ lùng — đúng tình
    huống thật: sơ đồ mount không nằm trong danh sách đã đoán."""
    monkeypatch.delenv("LLDMMRI_DATA_ROOT", raising=False)
    base = tmp_path / "input"
    root = _make_root(base / "datasets" / "someone", "ds", with_annotation=True)
    config = {
        "data_root": "local/fallback",
        "data_root_candidates": [str(tmp_path / "wrong1"), str(tmp_path / "wrong2")],
        "data_root_search": [str(base)],
        "annotation_rel": ANNOTATION_REL,
    }
    assert resolve_data_root(config) == root
