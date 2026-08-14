"""Selective policy for direct UniFormer uploads is OOF-locked and test-free."""

from pathlib import Path

import numpy as np
import pytest
from webapp.backend.live_inference import load_live_selective_policy


def _write_oof_fold(directory: Path, patient_ids: list[str], confidences: list[float]) -> None:
    directory.mkdir(parents=True)
    probs = np.zeros((len(confidences), 7), dtype=np.float64)
    for index, confidence in enumerate(confidences):
        probs[index, 0] = confidence
        probs[index, 1:] = (1.0 - confidence) / 6.0
    np.savez_compressed(
        directory / "val_probs_best.npz",
        probs=probs,
        labels=np.zeros(len(confidences), dtype=np.int64),
        patient_ids=np.asarray(patient_ids),
    )


def test_live_policy_locks_raw_max_prob_quantile_from_oof(tmp_path: Path) -> None:
    _write_oof_fold(tmp_path / "fold_1", ["MR1", "MR2"], [0.40, 0.70])
    _write_oof_fold(tmp_path / "fold_2", ["MR3", "MR4", "MR5"], [0.80, 0.90, 0.95])

    policy = load_live_selective_policy(tmp_path, target_coverage=0.80)

    assert policy.n_oof_cases == 5
    assert policy.target_coverage == 0.80
    assert policy.confidence_threshold == pytest.approx(0.64)


def test_live_policy_rejects_duplicate_oof_patient(tmp_path: Path) -> None:
    _write_oof_fold(tmp_path / "fold_1", ["MR-1"], [0.70])
    _write_oof_fold(tmp_path / "fold_2", ["MR1"], [0.90])

    with pytest.raises(RuntimeError, match="trùng bệnh nhân"):
        load_live_selective_policy(tmp_path)


def test_live_policy_never_reads_test_artifact(tmp_path: Path) -> None:
    _write_oof_fold(tmp_path / "fold_1", ["MR1"], [0.70])
    (tmp_path / "test").mkdir()
    np.savez_compressed(tmp_path / "test" / "test_probs.npz", forbidden=np.array([1]))

    policy = load_live_selective_policy(tmp_path)

    assert policy.n_oof_cases == 1
