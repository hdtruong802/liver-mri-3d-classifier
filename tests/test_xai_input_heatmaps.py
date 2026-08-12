"""Input × gradient maps keep an eight-phase global normalisation."""

import pytest

torch = pytest.importorskip("torch", reason="input sensitivity requires torch")

from src.xai.input_heatmap import input_x_gradient_heatmaps  # noqa: E402


class _TinyModel(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.weight = torch.nn.Parameter(
            torch.arange(1, 9, dtype=torch.float32).view(1, 8, 1, 1, 1)
        )

    def forward(self, value):
        score = (value * self.weight).sum(dim=(1, 2, 3, 4))
        reverse = (value * torch.flip(self.weight, dims=(1,))).sum(dim=(1, 2, 3, 4))
        return torch.stack([score, reverse], dim=1)


def test_input_gradient_has_input_shape_global_scale_and_restores_mode() -> None:
    model = _TinyModel()
    model.train()
    volume = torch.ones(1, 8, 4, 4, 2)
    result = input_x_gradient_heatmaps(model, volume, target_class=0)
    assert result.heatmaps.shape == (8, 4, 4, 2)
    assert float(result.heatmaps.min()) >= 0.0
    assert float(result.heatmaps.max()) == pytest.approx(1.0)
    assert float(result.heatmaps[0].max()) < 1.0, "phases must not be normalised independently"
    assert result.scale > 0.0
    assert model.training is True


def test_target_class_changes_sensitivity_direction() -> None:
    model = _TinyModel()
    volume = torch.ones(1, 8, 3, 3, 2)
    predicted = input_x_gradient_heatmaps(model, volume, target_class=0).heatmaps
    other = input_x_gradient_heatmaps(model, volume, target_class=1).heatmaps
    assert not torch.allclose(predicted, other)


def test_bad_input_or_target_fails_loudly() -> None:
    model = _TinyModel()
    with pytest.raises(ValueError, match="shape"):
        input_x_gradient_heatmaps(model, torch.ones(8, 3, 3, 2), target_class=0)
    with pytest.raises(ValueError, match="outside"):
        input_x_gradient_heatmaps(model, torch.ones(1, 8, 3, 3, 2), target_class=3)
