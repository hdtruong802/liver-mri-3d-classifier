"""Test pipeline tiền xử lý: lưới đích, resample, chuẩn hoá, build_cache, dataset.

Dựng NIfTI tổng hợp có một khối sáng đóng vai tổn thương, ở vị trí đã biết. Sau khi
chạy pipeline, khối đó phải nằm **giữa** patch — đó là bằng chứng lưới đích và phép
lấy mẫu đúng.
"""

import json
from pathlib import Path

import numpy as np
import pytest
from src.preprocess.grid import make_reference_image, target_origin
from src.preprocess.normalize import clip_and_zscore

from tests.conftest import CATEGORY_INFO, make_boxes, make_phase_entry

sitk = pytest.importorskip("SimpleITK", reason="cần SimpleITK cho resample")

PHASES = [{"name": "C+V", "file": "C+V"}, {"name": "DWI", "file": "DWI"}]
SPACING = (1.5, 1.5, 3.0)
SIZE = (16, 16, 8)


# --- lưới đích ---------------------------------------------------------------


def test_target_origin_places_center_correctly():
    """Tâm lưới phải rơi đúng vào điểm yêu cầu."""
    center = np.array([10.0, 20.0, 30.0])
    direction = np.eye(3)
    origin = target_origin(center, direction, SPACING, SIZE)
    half = np.array(SPACING) * (np.array(SIZE) - 1) / 2
    assert np.allclose(origin + half, center)


def test_make_reference_image_geometry():
    ref = make_reference_image(np.array([0.0, 0.0, 0.0]), np.eye(3), SPACING, SIZE)
    assert tuple(ref.GetSize()) == SIZE
    assert np.allclose(ref.GetSpacing(), SPACING)


# --- chuẩn hoá ---------------------------------------------------------------


def test_clip_and_zscore_standardises():
    rng = np.random.default_rng(0)
    vol = rng.normal(100, 15, size=(10, 10, 10))
    out = clip_and_zscore(vol)
    assert out.dtype == np.float32
    assert abs(float(out.mean())) < 0.1
    assert abs(float(out.std()) - 1.0) < 0.1


def test_clip_and_zscore_uses_external_stats():
    """stats_source giữ tương phản: patch sáng hơn nền thì mean phải > 0."""
    volume = np.zeros((20, 20, 20))
    volume[5:15, 5:15, 5:15] = 50.0
    patch = volume[6:10, 6:10, 6:10]  # nằm trong vùng sáng
    out = clip_and_zscore(patch, stats_source=volume)
    assert float(out.mean()) > 0.5


def test_clip_and_zscore_handles_flat_volume():
    """Volume phẳng -> trả 0, KHÔNG sinh NaN (chia cho std=0)."""
    out = clip_and_zscore(np.zeros((4, 4, 4)))
    assert np.isfinite(out).all()
    assert not out.any()


# --- pipeline end-to-end -----------------------------------------------------


def _write_phase(path: Path, shape, spacing, origin, lesion_center_vox, radius=4):
    """NIfTI có một khối cầu sáng làm 'tổn thương' tại vị trí cho trước.

    Nền phải **có nhiễu**, không được hằng số: với nền phẳng thì p0.5 == p99.5 và
    `clip_and_zscore` (đúng đắn) trả về toàn 0 để tránh chia cho std=0 — khi đó test
    không đo được gì. Dữ liệu MRI thật luôn có nhiễu nên đây mới là mô phỏng đúng.
    """
    import nibabel as nib

    rng = np.random.default_rng(0)
    data = rng.normal(100.0, 20.0, size=shape).astype(np.float32)  # nền mô mềm + nhiễu
    gx, gy, gz = np.ogrid[: shape[0], : shape[1], : shape[2]]
    cx, cy, cz = lesion_center_vox
    mask = ((gx - cx) ** 2 + (gy - cy) ** 2 + (gz - cz) ** 2) <= radius**2
    data[mask] = 1000.0
    affine = np.diag([*spacing, 1.0])
    affine[:3, 3] = origin
    nib.save(nib.Nifti1Image(data, affine), str(path))


@pytest.fixture
def tiny_dataset(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Một bệnh nhân, 2 pha khác spacing/origin, tổn thương ở CÙNG điểm mm (60,60,30)."""
    root = tmp_path / "data"
    images = root / "lld" / "images"
    images.mkdir(parents=True)

    # C+V: spacing 1mm, origin 0    -> tổn thương ở voxel (60,60,10) = world (60,60,30)
    _write_phase(
        images / "MR-1_1_C+V_0000.nii", (120, 120, 20), (1.0, 1.0, 3.0), (0, 0, 0), (60, 60, 10)
    )
    # DWI: spacing 2mm, origin -20  -> voxel (40,40,10) = world (60,60,30)
    _write_phase(
        images / "MR-1_1_DWI_0000.nii", (60, 60, 20), (2.0, 2.0, 3.0), (-20, -20, 0), (40, 40, 10)
    )

    annotation = {
        "Category_info": CATEGORY_INFO,
        "Annotation_info": {
            "MR-1": [
                make_phase_entry("C+V", 6, make_boxes([9, 10, 11], 56.0, 56.0, 64.0, 64.0)),
                make_phase_entry(
                    "DWI", 6, make_boxes([9, 10, 11], 38.0, 38.0, 42.0, 42.0), (2.0, 2.0), 3.0, 3.0
                ),
            ]
        },
    }
    (root / "lld" / "LLD_MMRI_Annotation.json").write_text(json.dumps(annotation), encoding="utf-8")

    data_cfg = {
        "data_root": str(root),
        "annotation_rel": "lld/LLD_MMRI_Annotation.json",
        "images_rel": "lld/images",
        "image_suffixes": ["_0000.nii.gz", "_0000.nii"],
        "phases": PHASES,
        "seed": 42,
    }
    pre_cfg = {
        "axis_order": "xy",
        "reference_phase": "C+V",
        "target_spacing": list(SPACING),
        "target_size": list(SIZE),
        "interpolator": "linear",
        "normalize": {"clip_percentile": [0.5, 99.5], "scope": "volume"},
        "n4": False,
        "output_dtype": "float16",
        "cache_dir": str(tmp_path / "cache"),
    }
    monkeypatch.delenv("LLDMMRI_DATA_ROOT", raising=False)
    monkeypatch.delenv("LLDMMRI_CACHE_DIR", raising=False)
    return data_cfg, pre_cfg


def test_process_patient_centres_lesion(tiny_dataset):
    """Tổn thương phải nằm GIỮA patch — bằng chứng lưới đích + lấy mẫu đúng."""
    from src.data.annotation import Annotation
    from src.data.images import scan_image_index
    from src.preprocess.build_cache import process_patient

    data_cfg, pre_cfg = tiny_dataset
    root = Path(data_cfg["data_root"])
    ann = Annotation(root / data_cfg["annotation_rel"])
    index = scan_image_index(root / data_cfg["images_rel"], data_cfg["image_suffixes"])

    volume = process_patient("MR-1", ann, index, PHASES, pre_cfg)
    assert volume.shape == (2, *SIZE)
    assert np.isfinite(volume).all()

    # Tâm patch phải nằm trong tổn thương (sáng), góc patch phải là nền (tối).
    # Không dùng argmax: sau khi cắt ngưỡng, mọi voxel tổn thương bằng nhau nên
    # argmax chỉ trả về voxel có chỉ số nhỏ nhất, không nói lên vị trí.
    cx, cy, cz = (s // 2 for s in SIZE)
    for channel in range(volume.shape[0]):
        centre_value = float(volume[channel, cx, cy, cz])
        corner_value = float(volume[channel, 0, 0, 0])
        assert centre_value > corner_value + 1.0, (
            f"pha {channel}: tâm={centre_value:.2f} không sáng hơn góc={corner_value:.2f} "
            "⇒ tổn thương KHÔNG nằm giữa patch"
        )


def test_build_cache_writes_npz_and_is_resumable(tiny_dataset, tmp_path, monkeypatch):
    from src.preprocess.build_cache import build_cache

    data_cfg, pre_cfg = tiny_dataset
    cfg_dir = tmp_path / "configs"
    cfg_dir.mkdir()
    import yaml

    (cfg_dir / "data.yaml").write_text(yaml.safe_dump(data_cfg), encoding="utf-8")
    pre_path = cfg_dir / "preprocess.yaml"
    pre_path.write_text(yaml.safe_dump(pre_cfg), encoding="utf-8")

    # build_cache đọc configs/data.yaml theo gốc repo -> chặn load_yaml để trỏ vào
    # config của test, và trỏ data root sang thư mục tạm.
    monkeypatch.setenv("LLDMMRI_DATA_ROOT", data_cfg["data_root"])
    monkeypatch.setattr(
        "src.preprocess.build_cache.load_yaml",
        lambda p: pre_cfg if str(p).endswith("preprocess.yaml") else data_cfg,
    )

    cache_dir = build_cache(pre_path)
    out = cache_dir / "MR-1.npz"
    assert out.exists()
    assert (cache_dir / "cache_meta.json").exists()
    assert (cache_dir / "build_log.csv").exists()

    with np.load(out) as d:
        assert d["image"].shape == (2, *SIZE)
        assert d["image"].dtype == np.float16
        assert int(d["label"]) == 6

    # chạy lại: phải BỎ QUA, không ghi đè (tính resume)
    mtime = out.stat().st_mtime_ns
    build_cache(pre_path)
    assert out.stat().st_mtime_ns == mtime


def test_build_cache_refuses_without_axis_order(tiny_dataset, tmp_path, monkeypatch):
    """axis_order để trống -> DỪNG, không đoán."""
    from src.preprocess.build_cache import build_cache

    data_cfg, pre_cfg = tiny_dataset
    bad = dict(pre_cfg, axis_order=None)
    monkeypatch.setattr(
        "src.preprocess.build_cache.load_yaml",
        lambda p: bad if str(p).endswith("preprocess.yaml") else data_cfg,
    )
    with pytest.raises(SystemExit, match="axis_order"):
        build_cache(tmp_path / "preprocess.yaml")


# --- cắt bám sát tổn thương (crop_mode = lesion_tight) -----------------------


def test_bbox_extent_counts_both_endpoints():
    """Bbox từ voxel 56 đến 64 phủ 9 voxel, không phải 8."""
    from src.data.annotation import BBox3D
    from src.preprocess.crop import bbox_extent_voxel

    box = BBox3D(x_min=56.0, x_max=64.0, y_min=50.0, y_max=60.0, z_min=9.0, z_max=11.0)
    assert np.allclose(bbox_extent_voxel(box, "xy"), [9.0, 11.0, 3.0])
    # 'yx' hoán hai trục đầu, trục slice giữ nguyên.
    assert np.allclose(bbox_extent_voxel(box, "yx"), [11.0, 9.0, 3.0])


def test_mask_extent_matches_written_blob():
    from src.preprocess.crop import mask_center_extent_voxel

    mask = np.zeros((20, 20, 20), dtype=np.uint8)
    mask[4:9, 10:14, 2:5] = 1  # 5 x 4 x 3 voxel
    center, extent = mask_center_extent_voxel(mask)
    assert np.allclose(extent, [5.0, 4.0, 3.0])
    assert np.allclose(center, [6.0, 11.5, 3.0])


def test_empty_mask_raises_instead_of_guessing():
    """Mask rỗng = phân vùng hỏng. Im lặng rơi về tâm ảnh sẽ tạo dữ liệu sai."""
    from src.preprocess.crop import mask_center_extent_voxel

    with pytest.raises(ValueError, match="rỗng"):
        mask_center_extent_voxel(np.zeros((5, 5, 5)))


def test_adaptive_spacing_scales_with_lesion():
    from src.preprocess.crop import adaptive_spacing

    spacing, fov = adaptive_spacing(
        np.array([10.0, 10.0, 10.0]),
        size=(20, 20, 10),
        margin_factor=2.0,
        min_fov_mm=(1.0, 1.0, 1.0),
        max_fov_mm=(500.0, 500.0, 500.0),
    )
    assert np.allclose(fov, [20.0, 20.0, 20.0])  # 10mm x 2.0
    assert np.allclose(spacing, [1.0, 1.0, 2.0])  # fov / size


def test_adaptive_spacing_respects_floor_and_ceiling():
    from src.preprocess.crop import adaptive_spacing

    _, tiny = adaptive_spacing(
        np.array([2.0, 2.0, 2.0]), (10, 10, 10), 1.6, (40.0, 40.0, 40.0), (200.0, 200.0, 200.0)
    )
    assert np.allclose(tiny, [40.0, 40.0, 40.0]), "tổn thương nhỏ phải bị chặn bởi sàn"

    _, huge = adaptive_spacing(
        np.array([300.0, 300.0, 300.0]),
        (10, 10, 10),
        1.6,
        (40.0, 40.0, 40.0),
        (200.0, 200.0, 200.0),
    )
    assert np.allclose(huge, [200.0, 200.0, 200.0]), "tổn thương lớn phải bị chặn bởi trần"


def test_adaptive_spacing_rejects_bad_bounds():
    from src.preprocess.crop import adaptive_spacing

    with pytest.raises(ValueError, match="max_fov_mm"):
        adaptive_spacing(np.ones(3), (8, 8, 8), 1.0, (100.0,) * 3, (50.0,) * 3)
    with pytest.raises(ValueError, match="margin_factor"):
        adaptive_spacing(np.ones(3), (8, 8, 8), 0.0, (1.0,) * 3, (50.0,) * 3)


def test_lesion_tight_gives_smaller_fov_and_still_centres(tiny_dataset):
    """Cửa sổ phải hẹp hơn fixed_mm mà tổn thương vẫn nằm giữa patch."""
    from src.data.annotation import Annotation
    from src.data.images import scan_image_index
    from src.preprocess.build_cache import process_patient_with_meta

    data_cfg, pre_cfg = tiny_dataset
    root = Path(data_cfg["data_root"])
    ann = Annotation(root / data_cfg["annotation_rel"])
    index = scan_image_index(root / data_cfg["images_rel"], data_cfg["image_suffixes"])

    tight_cfg = {
        **pre_cfg,
        "crop_mode": "lesion_tight",
        "lesion_tight": {
            "source": "bbox",
            "margin_factor": 1.6,
            "min_fov_mm": [5.0, 5.0, 5.0],
            "max_fov_mm": [500.0, 500.0, 500.0],
        },
    }
    volume, meta = process_patient_with_meta("MR-1", ann, index, PHASES, tight_cfg)

    assert volume.shape == (2, *SIZE), "số voxel đầu ra phải không đổi"
    assert meta["crop_source"] == "bbox"

    fixed_fov = np.array(SPACING) * np.array(SIZE)
    assert np.all(meta["fov_mm"] < fixed_fov), (
        f"fov {meta['fov_mm']} phải hẹp hơn cửa sổ cố định {fixed_fov}"
    )
    # bbox 9x9x3 voxel @ spacing (1,1,3)mm = 9x9x9mm, nhân 1.6 = 14.4mm mỗi trục.
    assert np.allclose(meta["lesion_extent_mm"], [9.0, 9.0, 9.0])
    assert np.allclose(meta["fov_mm"], [14.4, 14.4, 14.4], atol=1e-4)

    cx, cy, cz = (s // 2 for s in SIZE)
    for channel in range(volume.shape[0]):
        assert float(volume[channel, cx, cy, cz]) > float(volume[channel, 0, 0, 0]) + 1.0


def test_lesion_tight_falls_back_to_bbox_when_mask_missing(tiny_dataset):
    """Thiếu mask thì vẫn chạy, nhưng phải ghi rõ nguồn là bbox."""
    from src.data.annotation import Annotation
    from src.data.images import scan_image_index
    from src.preprocess.build_cache import process_patient_with_meta

    data_cfg, pre_cfg = tiny_dataset
    root = Path(data_cfg["data_root"])
    ann = Annotation(root / data_cfg["annotation_rel"])
    index = scan_image_index(root / data_cfg["images_rel"], data_cfg["image_suffixes"])

    cfg = {
        **pre_cfg,
        "crop_mode": "lesion_tight",
        "lesion_tight": {
            "source": "mask",
            "margin_factor": 1.6,
            "min_fov_mm": [5.0, 5.0, 5.0],
            "max_fov_mm": [500.0, 500.0, 500.0],
        },
    }
    _, meta = process_patient_with_meta("MR-1", ann, index, PHASES, cfg, mask_index={})
    assert meta["crop_source"] == "bbox"


def test_fixed_mm_mode_is_unchanged(tiny_dataset):
    """Chế độ cũ phải cho đúng kết quả cũ — không được đổi dữ liệu đã build."""
    from src.data.annotation import Annotation
    from src.data.images import scan_image_index
    from src.preprocess.build_cache import process_patient, process_patient_with_meta

    data_cfg, pre_cfg = tiny_dataset
    root = Path(data_cfg["data_root"])
    ann = Annotation(root / data_cfg["annotation_rel"])
    index = scan_image_index(root / data_cfg["images_rel"], data_cfg["image_suffixes"])

    legacy = process_patient("MR-1", ann, index, PHASES, pre_cfg)
    volume, meta = process_patient_with_meta("MR-1", ann, index, PHASES, pre_cfg)

    assert np.allclose(legacy, volume)
    assert meta["crop_mode"] == "fixed_mm"
    assert np.allclose(meta["fov_mm"], np.array(SPACING) * np.array(SIZE))


def test_build_cache_lesion_tight_writes_geometry_meta(tiny_dataset, tmp_path, monkeypatch):
    """Đường chạy thật trên Kaggle: cache mới phải kèm hình học cửa sổ cắt.

    `lesion_extent_mm` là thứ chế độ lesion_tight cắt bỏ khỏi ảnh; không ghi lại
    thì kích thước tuyệt đối của tổn thương mất hẳn, và đó là thông tin chẩn đoán.
    """
    import yaml
    from src.preprocess.build_cache import build_cache

    data_cfg, pre_cfg = tiny_dataset
    tight_cfg = {
        **pre_cfg,
        "crop_mode": "lesion_tight",
        "lesion_tight": {
            "source": "bbox",
            "margin_factor": 1.6,
            "min_fov_mm": [5.0, 5.0, 5.0],
            "max_fov_mm": [500.0, 500.0, 500.0],
        },
        "cache_dir": str(tmp_path / "cache_tight"),
    }
    cfg_dir = tmp_path / "configs"
    cfg_dir.mkdir()
    (cfg_dir / "data.yaml").write_text(yaml.safe_dump(data_cfg), encoding="utf-8")
    pre_path = cfg_dir / "preprocess.yaml"
    pre_path.write_text(yaml.safe_dump(tight_cfg), encoding="utf-8")

    monkeypatch.setenv("LLDMMRI_DATA_ROOT", data_cfg["data_root"])
    monkeypatch.delenv("LLDMMRI_CACHE_DIR", raising=False)
    monkeypatch.setattr(
        "src.preprocess.build_cache.load_yaml",
        lambda p: tight_cfg if str(p).endswith("preprocess.yaml") else data_cfg,
    )

    cache_dir = build_cache(pre_path)
    with np.load(cache_dir / "MR-1.npz") as d:
        assert d["image"].shape == (2, *SIZE)
        assert np.allclose(d["lesion_extent_mm"], [9.0, 9.0, 9.0])
        assert np.allclose(d["fov_mm"], [14.4, 14.4, 14.4], atol=1e-4)
        assert str(d["crop_source"]) == "bbox"

    meta = json.loads((cache_dir / "cache_meta.json").read_text(encoding="utf-8"))
    assert meta["crop_mode"] == "lesion_tight"
    assert meta["lesion_tight"]["margin_factor"] == 1.6


def test_build_cache_mask_source_needs_labels_rel(tiny_dataset, tmp_path, monkeypatch):
    """source='mask' mà data.yaml thiếu labels_rel thì phải dừng có thông báo rõ."""
    import yaml
    from src.preprocess.build_cache import build_cache

    data_cfg, pre_cfg = tiny_dataset
    tight_cfg = {**pre_cfg, "crop_mode": "lesion_tight", "lesion_tight": {"source": "mask"}}
    cfg_dir = tmp_path / "configs"
    cfg_dir.mkdir()
    pre_path = cfg_dir / "preprocess.yaml"
    pre_path.write_text(yaml.safe_dump(tight_cfg), encoding="utf-8")

    monkeypatch.setenv("LLDMMRI_DATA_ROOT", data_cfg["data_root"])
    monkeypatch.setattr(
        "src.preprocess.build_cache.load_yaml",
        lambda p: tight_cfg if str(p).endswith("preprocess.yaml") else data_cfg,
    )
    with pytest.raises(SystemExit, match="labels_rel"):
        build_cache(pre_path)
