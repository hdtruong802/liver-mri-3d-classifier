"""Test lùng thư mục cache + mô tả cây thư mục.

Cùng bài học với `resolve_data_root` (WORKLOG S-025/S-027): **không đoán sơ đồ mount
của Kaggle**, tìm bằng nội dung thật. Và khi không tìm thấy thì phải nói được *đang
thấy gì* — một câu "không thấy cache" trơ trọi bắt người dùng tự mò.
"""

from pathlib import Path

from src.utils.io import describe_tree, find_cache_dir


def _make_cache(base: Path, n_npz: int = 3, with_meta: bool = True) -> Path:
    base.mkdir(parents=True, exist_ok=True)
    for i in range(n_npz):
        (base / f"MR-{i}.npz").write_bytes(b"x")
    if with_meta:
        (base / "cache_meta.json").write_text("{}", encoding="utf-8")
    return base


def test_finds_cache_at_any_mount_depth(tmp_path: Path):
    """Cache nằm sâu bao nhiêu cũng phải thấy — Kaggle từng đổi sơ đồ mount."""
    for depth in range(4):
        root = tmp_path / f"root{depth}"
        nested = root.joinpath(*[f"lvl{i}" for i in range(depth)]) / "cache"
        _make_cache(nested)
        assert find_cache_dir([root]) == nested


def test_prefers_shallower_mount(tmp_path: Path):
    """Mount nông là bản chính; thư mục lồng sâu dễ là bản sao/giải nén tạm."""
    shallow = _make_cache(tmp_path / "cache")
    _make_cache(tmp_path / "a" / "b" / "cache")
    assert find_cache_dir([tmp_path]) == shallow


def test_falls_back_to_npz_when_metadata_missing(tmp_path: Path):
    """Cache đóng gói lại làm mất cache_meta.json vẫn dùng được (có cảnh báo ở notebook)."""
    cache = _make_cache(tmp_path / "ds" / "cache", n_npz=5, with_meta=False)
    assert find_cache_dir([tmp_path]) == cache


def test_metadata_wins_over_bare_npz_folder(tmp_path: Path):
    _make_cache(tmp_path / "a" / "npz_only", n_npz=9, with_meta=False)
    real = _make_cache(tmp_path / "b" / "real", n_npz=1, with_meta=True)
    assert find_cache_dir([tmp_path]) == real


def test_min_npz_rejects_a_too_small_folder(tmp_path: Path):
    _make_cache(tmp_path / "ds", n_npz=2, with_meta=False)
    assert find_cache_dir([tmp_path], min_npz=400) is None


def test_returns_none_when_nothing_mounted(tmp_path: Path):
    assert find_cache_dir([tmp_path]) is None
    assert find_cache_dir([tmp_path / "không-tồn-tại"]) is None
    assert find_cache_dir([]) is None


def test_describe_tree_lists_dirs_with_file_counts(tmp_path: Path):
    _make_cache(tmp_path / "lld-mmri-3" / "cache", n_npz=3)
    lines = "\n".join(describe_tree(tmp_path))

    assert "lld-mmri-3" in lines
    assert "3.npz" in lines  # đếm theo đuôi file -> nhìn là biết có phải cache không


def test_describe_tree_handles_missing_and_empty(tmp_path: Path):
    assert "không tồn tại" in describe_tree(tmp_path / "vắng")[0]
    assert "rỗng" in describe_tree(tmp_path)[0]


def test_describe_tree_is_bounded(tmp_path: Path):
    """Không được đổ hàng nghìn dòng ra output khi mount cả dataset lớn."""
    for i in range(80):
        (tmp_path / f"f{i}.txt").write_text("x", encoding="utf-8")
    lines = describe_tree(tmp_path, max_entries=10)

    assert len(lines) == 11  # 10 mục + dòng "còn nữa"
    assert "còn nữa" in lines[-1]
