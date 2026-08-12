"""Input × gradient heatmaps for the model's predicted class.

This module is intentionally offline-only.  The web app only reads precomputed
artefacts; it never imports PyTorch or runs a backward pass.  A heatmap is a
local sensitivity visualisation, not a lesion segmentation or a diagnostic
output.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch


@dataclass(frozen=True)
class InputHeatmapResult:
    """Per-phase, globally normalised input × gradient attribution maps."""

    heatmaps: torch.Tensor
    scale: float


def input_x_gradient_heatmaps(
    model: torch.nn.Module,
    volume: torch.Tensor,
    target_class: int,
) -> InputHeatmapResult:
    """Return ``|input × gradient|`` for one predicted class.

    ``volume`` must be exactly the 5-D crop seen by the model:
    ``[batch=1, phases, x, y, z]``.  A single maximum from all eight phases
    normalises the result, so a weak phase cannot look artificially hot merely
    because its own map was scaled independently.
    """
    if volume.ndim != 5 or volume.shape[0] != 1:
        raise ValueError("volume must have shape [1, phases, x, y, z]")
    if target_class < 0:
        raise ValueError("target_class must be non-negative")

    was_training = model.training
    sample = volume.detach().clone().requires_grad_(True)
    try:
        model.eval()
        model.zero_grad(set_to_none=True)
        logits = model(sample)
        if logits.ndim != 2 or target_class >= logits.shape[1]:
            raise ValueError(
                f"target_class {target_class} outside model logits with shape {tuple(logits.shape)}"
            )
        logits[0, target_class].backward()
        if sample.grad is None:
            raise RuntimeError("input gradient was not populated")

        raw = (sample.grad * sample).abs()[0].detach()
        if not torch.isfinite(raw).all():
            raise ValueError("input × gradient contains non-finite values")
        scale = float(raw.max().item())
        heatmaps = torch.zeros_like(raw) if scale == 0.0 else raw / scale
        return InputHeatmapResult(heatmaps=heatmaps.cpu(), scale=scale)
    finally:
        model.zero_grad(set_to_none=True)
        model.train(was_training)
