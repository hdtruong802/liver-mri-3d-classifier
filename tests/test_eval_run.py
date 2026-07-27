"""Test CLI đánh giá thuần — chạy trên file .npz giả, không cần torch/GPU."""

from pathlib import Path

import numpy as np
import pytest
from src.eval.run import (
    evaluate,
    find_fold_predictions,
    format_per_class,
    format_table,
    load_predictions,
    pool_out_of_fold,
    report,
)

N_RESAMPLES = 2000


def _write_predictions(
    directory: Path, patient_ids: list[str], labels: list[int], filename: str = "val_probs_best.npz"
) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(len(patient_ids))
    probs = rng.random((len(labels), 7))
    probs /= probs.sum(axis=1, keepdims=True)
    # Cho model "đoán đúng" phần lớn để metric không suy biến.
    for row, label in enumerate(labels):
        probs[row, label] += 1.0
    path = directory / filename
    np.savez_compressed(
        path,
        probs=probs,
        labels=np.array(labels, dtype=np.int64),
        patient_ids=np.array(patient_ids),
        epoch=11,
    )
    return path


def test_load_predictions_roundtrip(tmp_path: Path):
    _write_predictions(tmp_path, ["MR-1", "MR-2"], [0, 6])
    loaded = load_predictions(tmp_path / "val_probs_best.npz")

    assert loaded["patient_ids"] == ["MR-1", "MR-2"]
    assert loaded["labels"].tolist() == [0, 6]
    assert loaded["probs"].shape == (2, 7)
    assert loaded["epoch"] == 11


def test_find_fold_predictions_matches_hashed_dir_names(tmp_path: Path):
    """Thư mục run hiện mang hash kiến trúc (`fold1_4c2cf705`), bản cũ thì không."""
    _write_predictions(tmp_path / "fold1_4c2cf705", ["MR-1"], [0])
    _write_predictions(tmp_path / "fold2", ["MR-2"], [1])

    found = find_fold_predictions(tmp_path)
    assert set(found) == {"fold1_4c2cf705", "fold2"}


def test_pool_out_of_fold_concatenates_all_folds():
    predictions = {
        "fold1": {
            "labels": np.array([0, 1]),
            "probs": np.zeros((2, 7)),
            "patient_ids": ["MR-1", "MR-2"],
        },
        "fold2": {
            "labels": np.array([6]),
            "probs": np.zeros((1, 7)),
            "patient_ids": ["MR-3"],
        },
    }
    pooled = pool_out_of_fold(predictions)

    assert pooled["labels"].tolist() == [0, 1, 6]
    assert pooled["patient_ids"] == ["MR-1", "MR-2", "MR-3"]
    assert pooled["n_folds"] == 2


def test_pool_rejects_a_patient_appearing_in_two_folds():
    """Gộp mà đếm một người hai lần vẫn ra số trông hợp lý — phải nổ, đừng báo số sai."""
    predictions = {
        "fold1": {
            "labels": np.array([0]),
            "probs": np.zeros((1, 7)),
            "patient_ids": ["MR-1"],
        },
        "fold2": {
            "labels": np.array([0]),
            "probs": np.zeros((1, 7)),
            "patient_ids": ["MR-1"],
        },
    }
    with pytest.raises(ValueError, match="LEAK"):
        pool_out_of_fold(predictions)


def test_pool_detects_leak_across_hyphen_forms():
    """'MR207602' và 'MR-207602' là cùng một người."""
    predictions = {
        "fold1": {"labels": np.array([0]), "probs": np.zeros((1, 7)), "patient_ids": ["MR-207602"]},
        "fold2": {"labels": np.array([0]), "probs": np.zeros((1, 7)), "patient_ids": ["MR207602"]},
    }
    with pytest.raises(ValueError, match="LEAK"):
        pool_out_of_fold(predictions)


def test_evaluate_returns_ci_for_each_metric():
    rng = np.random.default_rng(0)
    labels = np.tile(np.arange(7), 12)
    probs = rng.random((labels.size, 7))
    probs[np.arange(labels.size), labels] += 1.5

    result = evaluate(labels, probs, n_resamples=N_RESAMPLES)

    assert set(result) == {"macro_f1", "cohen_kappa", "balanced_accuracy", "accuracy"}
    for value in result.values():
        assert value["ci_low"] <= value["point"] <= value["ci_high"]


def test_report_produces_folds_and_pooled(tmp_path: Path):
    """Đường đi end-to-end: 2 fold trên đĩa -> bảng từng fold + bảng gộp."""
    _write_predictions(
        tmp_path / "fold1_abc", [f"MR-{i}" for i in range(20)], list(range(7)) * 2 + [0] * 6
    )
    _write_predictions(
        tmp_path / "fold2_abc", [f"MR-{i}" for i in range(20, 40)], list(range(7)) * 2 + [1] * 6
    )

    result = report(tmp_path, n_resamples=N_RESAMPLES)

    assert set(result["folds"]) == {"fold1_abc", "fold2_abc"}
    assert result["pooled"]["best"]["n_patients"] == 40
    assert result["pooled"]["best"]["n_folds"] == 2
    assert "macro_f1" in result["pooled"]["best"]["metrics"]


def test_report_reads_best_and_last_separately(tmp_path: Path):
    """Hai cột best/last là thước đo thiên lệch chọn epoch — phải tách được."""
    ids = [f"MR-{i}" for i in range(14)]
    labels = list(range(7)) * 2
    _write_predictions(tmp_path / "fold1_abc", ids, labels, "val_probs_best.npz")
    _write_predictions(tmp_path / "fold1_abc", ids, labels, "val_probs_last.npz")

    result = report(tmp_path, n_resamples=N_RESAMPLES)

    assert set(result["folds"]["fold1_abc"]) == {"best", "last"}
    assert set(result["pooled"]) == {"best", "last"}


def test_report_on_empty_dir_is_not_an_error(tmp_path: Path):
    result = report(tmp_path, n_resamples=N_RESAMPLES)
    assert result["folds"] == {}
    assert result["pooled"] == {}


def test_format_table_lists_every_metric():
    rows = {"fold1 · best": {"macro_f1": {"point": 0.26, "ci_low": 0.18, "ci_high": 0.35}}}
    text = format_table(rows)

    assert "macro_f1" in text
    assert "0.2600" in text
    assert "fold1 · best" in text


def test_format_per_class_shows_support_and_matrix():
    labels = np.array([0, 0, 6, 6])
    probs = np.zeros((4, 7))
    probs[:, 0] = 1.0
    text = format_per_class(labels, probs)

    assert "u máu" in text
    assert "n=2" in text
    assert "Ma trận nhầm lẫn" in text
