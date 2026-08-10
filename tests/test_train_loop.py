"""Test các mảnh của vòng train.

`class_weights_from_labels` là numpy thuần nên luôn chạy; phần checkpoint và
`run_epoch` cần torch nên sẽ skip trên máy chưa cài deep-learning stack.
"""

from pathlib import Path

import numpy as np
import pytest
from src.train.loop import class_weights_from_labels, load_checkpoint, run_epoch, save_checkpoint


def test_class_weights_are_inverse_frequency():
    labels = [6] * 40 + [2] * 10  # HCC nhiều gấp 4 lần áp-xe
    weights = class_weights_from_labels(labels)

    assert weights[2] == pytest.approx(4.0 * weights[6])
    assert np.isfinite(weights).all()


def test_class_weights_absent_class_is_one_not_inf():
    """Lớp vắng mặt trong fold không được sinh trọng số vô hạn."""
    weights = class_weights_from_labels([0, 0, 1])
    assert np.isfinite(weights).all()
    assert weights[5] == pytest.approx(1.0)


def test_class_weights_balanced_labels_give_ones():
    weights = class_weights_from_labels(list(range(7)))
    assert weights == pytest.approx(np.ones(7))


def test_checkpoint_roundtrip_and_missing_file(tmp_path: Path):
    pytest.importorskip("torch", reason="checkpoint cần torch")

    assert load_checkpoint(tmp_path / "chưa-có.pt") is None

    path = tmp_path / "last.pt"
    save_checkpoint(path, {"epoch": 3, "best_score": 0.42})
    state = load_checkpoint(path)

    assert state["epoch"] == 3
    assert state["best_score"] == pytest.approx(0.42)
    # Ghi nguyên tử: không được để lại file tạm sau khi xong.
    assert not list(tmp_path.glob("*.tmp.pt"))


def test_run_epoch_eval_returns_probs_per_patient():
    torch = pytest.importorskip("torch", reason="run_epoch cần torch")

    class TinyModel(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.fc = torch.nn.Linear(4, 7)

        def forward(self, x):
            return self.fc(x.flatten(1)[:, :4])

    batch = {
        "image": torch.randn(3, 8, 2, 2, 2),
        "label": torch.tensor([0, 3, 6]),
        "patient_id": ["MR-1", "MR-2", "MR-3"],
    }
    out = run_epoch(
        TinyModel(), [batch], torch.device("cpu"), torch.nn.CrossEntropyLoss(), amp=False
    )

    assert out["probs"].shape == (3, 7)
    assert out["probs"].sum(axis=1) == pytest.approx(np.ones(3), abs=1e-5)
    assert out["labels"].tolist() == [0, 3, 6]
    assert out["patient_ids"] == ["MR-1", "MR-2", "MR-3"]
    assert np.isfinite(out["loss"])


def test_run_epoch_train_updates_weights_with_partial_accumulation():
    """Batch cuối chưa đủ accum_steps vẫn phải được cập nhật, không bị vứt."""
    torch = pytest.importorskip("torch", reason="run_epoch cần torch")

    model = torch.nn.Linear(64, 7)

    class Wrapper(torch.nn.Module):
        def __init__(self, inner):
            super().__init__()
            self.inner = inner

        def forward(self, x):
            return self.inner(x.flatten(1))

    wrapped = Wrapper(model)
    before = model.weight.detach().clone()
    batch = {
        "image": torch.randn(2, 8, 2, 2, 2),
        "label": torch.tensor([1, 4]),
        "patient_id": ["MR-1", "MR-2"],
    }
    optimizer = torch.optim.SGD(wrapped.parameters(), lr=0.1)
    run_epoch(
        wrapped,
        [batch],  # 1 batch nhưng accum_steps=8
        torch.device("cpu"),
        torch.nn.CrossEntropyLoss(),
        optimizer=optimizer,
        scaler=None,
        accum_steps=8,
        amp=False,
    )

    assert not torch.allclose(before, model.weight), "gradient của batch đuôi bị bỏ qua"


# --- F1 từng lớp theo epoch ---------------------------------------------------


def test_csv_fields_co_cot_f1_tung_lop():
    """Hai lớp yếu (ICC, di căn) chặn mục tiêu về số học, nên phải theo dõi được quỹ đạo
    của chúng theo epoch, không chỉ macro-F1 gộp."""
    from src.data.taxonomy import SHORT_NAMES
    from src.train.run import CSV_FIELDS

    for index, name in SHORT_NAMES.items():
        assert f"f1_{name}" in CSV_FIELDS, (index, name)
    assert CSV_FIELDS[:9] == [
        "epoch",
        "train_loss",
        "val_loss",
        "val_macro_f1",
        "val_balanced_accuracy",
        "val_accuracy",
        "val_cohen_kappa",
        "lr",
        "seconds",
    ], "chín cột đầu phải giữ nguyên thứ tự — có log cũ đọc theo vị trí"
