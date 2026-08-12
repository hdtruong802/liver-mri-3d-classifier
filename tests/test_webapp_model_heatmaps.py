"""Tests for validated, multi-phase sensitivity artefacts served by the web app."""

import io
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("PIL", reason="serve layer needs Pillow")

from PIL import Image  # noqa: E402
from webapp.backend import model_heatmaps  # noqa: E402
from webapp.backend.phases import PHASES  # noqa: E402

SHAPE = (8, 12, 12, 6)
TOKENS = np.asarray([phase.file_token for phase in PHASES])


def _write(directory: Path, pid: str, **overrides: object) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    crop = np.full(SHAPE, 64, dtype=np.uint8)
    heatmaps = np.zeros(SHAPE, dtype=np.float32)
    heatmaps[:, 2:10, 2:10, :] = 1.0
    annotations = np.zeros(SHAPE, dtype=np.uint8)
    annotations[:, 4:8, 4:8, 2:4] = 1
    payload: dict[str, object] = {
        "phase_tokens": TOKENS,
        "crop_refs": crop,
        "heatmaps_pred": heatmaps,
        "annotation_masks": annotations,
        "pred_index": np.int64(3),
        "heatmap_scale": np.float32(0.42),
    }
    payload.update(overrides)
    path = directory / f"{pid}.npz"
    np.savez_compressed(path, **payload)
    return path


@pytest.fixture(autouse=True)
def _clear_caches():
    model_heatmaps.load_all.cache_clear()
    model_heatmaps._render_cache.clear()
    yield
    model_heatmaps.load_all.cache_clear()
    model_heatmaps._render_cache.clear()


def test_missing_directory_is_a_safe_empty_state(tmp_path: Path) -> None:
    assert model_heatmaps.load_all(str(tmp_path / "not-created")) == {}
    assert model_heatmaps.get("MR001") is None


def test_loads_eight_phase_artifact_and_preserves_common_scale(tmp_path: Path) -> None:
    _write(tmp_path, "MR001")
    artifact = model_heatmaps.load_all(str(tmp_path))["MR001"]
    assert artifact.phase_tokens == tuple(TOKENS.tolist())
    assert artifact.n_slices == SHAPE[3]
    assert artifact.pred_index == 3
    assert artifact.heatmap_scale == pytest.approx(0.42)
    assert artifact.lesion_slices["C-pre"] == [2, 3]


@pytest.mark.parametrize(
    ("key", "value", "message"),
    [
        ("phase_tokens", np.asarray(list(reversed(TOKENS.tolist()))), "phase_tokens"),
        ("heatmaps_pred", np.zeros((8, 8, 8, 6), dtype=np.float32), "heatmaps_pred"),
        ("crop_refs", np.zeros(SHAPE, dtype=np.float32), "crop_refs"),
        ("heatmaps_pred", np.full(SHAPE, 1.1, dtype=np.float32), "normalised"),
    ],
)
def test_rejects_invalid_geometry_or_phase_order(
    tmp_path: Path, key: str, value: object, message: str
) -> None:
    path = _write(tmp_path, "MR001", **{key: value})
    with pytest.raises(model_heatmaps.InvalidModelHeatmap, match=message):
        model_heatmaps._read_artifact(path)


def test_renders_all_phases_and_all_overlay_states(tmp_path: Path) -> None:
    _write(tmp_path, "MR001")
    artifact = model_heatmaps.load_all(str(tmp_path))["MR001"]
    rendered = {
        (phase.file_token, annotation, heatmap): model_heatmaps.render_png(
            artifact, phase.file_token, 0, annotation=annotation, heatmap=heatmap
        )
        for phase in PHASES
        for annotation in (False, True)
        for heatmap in (False, True)
    }
    assert all(payload.startswith(b"\x89PNG") for payload in rendered.values())
    assert rendered[("C-pre", False, False)] != rendered[("C-pre", False, True)]
    assert rendered[("C-pre", False, False)] == rendered[("C+A", False, False)]


def test_annotation_is_drawn_above_heatmap(tmp_path: Path) -> None:
    _write(tmp_path, "MR001")
    artifact = model_heatmaps.load_all(str(tmp_path))["MR001"]
    image = Image.open(
        io.BytesIO(model_heatmaps.render_png(artifact, "C-pre", 2, annotation=True, heatmap=True))
    )
    pixels = np.asarray(image)
    assert np.any(np.all(pixels == np.asarray([232, 121, 249]), axis=-1)), (
        "fuchsia edge must remain visible"
    )


def test_rejects_unknown_phase_and_out_of_range_slice(tmp_path: Path) -> None:
    _write(tmp_path, "MR001")
    artifact = model_heatmaps.load_all(str(tmp_path))["MR001"]
    with pytest.raises(ValueError, match="unknown phase"):
        model_heatmaps.render_png(artifact, "not-a-phase", 0, annotation=False, heatmap=False)
    with pytest.raises(IndexError):
        model_heatmaps.render_png(artifact, "C-pre", SHAPE[3], annotation=False, heatmap=False)


def test_model_view_route_exists_and_legacy_route_is_absent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from webapp.backend import main

    _write(tmp_path, "MR113627")
    monkeypatch.setattr(model_heatmaps, "MODEL_HEATMAP_DIR", tmp_path)
    model_heatmaps.load_all.cache_clear()
    response = main.case_model_view("MR113627", phase="C-pre", z=2, annotation=True, heatmap=True)
    assert response.media_type == "image/png" and response.body.startswith(b"\x89PNG")
