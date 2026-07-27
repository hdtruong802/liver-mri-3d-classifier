"""Test resolve_data_root — dò data root theo ứng viên, có xác minh.

Kaggle đổi sơ đồ mount (`/kaggle/input/<slug>` vs `/kaggle/input/datasets/<owner>/<slug>`)
nên không được hardcode. Quan trọng hơn: phải **xác minh bằng annotation**, vì thư
mục rỗng tồn tại vẫn khiến mọi bước sau thất bại âm thầm (WORKLOG S-025).
"""

from pathlib import Path

import pytest
from src.utils.io import resolve_data_root

ANNOTATION_REL = "lld/LLD_MMRI_Annotation.json"


def _make_root(base: Path, name: str, *, with_annotation: bool) -> Path:
    root = base / name
    (root / "lld").mkdir(parents=True)
    if with_annotation:
        (root / ANNOTATION_REL).write_text("{}", encoding="utf-8")
    return root


def test_env_var_wins_over_everything(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("LLDMMRI_DATA_ROOT", str(tmp_path / "from_env"))
    config = {
        "data_root": str(tmp_path / "local"),
        "data_root_candidates": [str(tmp_path / "cand")],
        "annotation_rel": ANNOTATION_REL,
    }
    assert resolve_data_root(config) == tmp_path / "from_env"


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
