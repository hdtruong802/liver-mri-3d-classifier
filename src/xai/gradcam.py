"""Grad-CAM 3D cho DenseNet121-3D, và độ nhạy theo từng thì MRI.

## Grad-CAM nói gì và KHÔNG nói gì

Grad-CAM lấy bản đồ đặc trưng của một tầng, nhân với gradient của logit lớp đích rồi
gộp lại: vùng nào vừa được kích hoạt mạnh vừa đẩy logit lên thì sáng. Nó cho biết
**mô hình nhạy với vùng nào**, không chứng minh mô hình "hiểu" vùng đó, và tuyệt đối
không phải một phép phân vùng tổn thương — dự án này không làm segmentation
(AGENTS.md §3.9).

## Cạm bẫy lớn nhất: độ phân giải theo trục Z

DenseNet121 hạ mẫu 5 lần. Với đầu vào 112×112×32 của dự án, tầng cuối (`norm5`) chỉ
còn cỡ 3×3×**1** — nghĩa là bản đồ **giống hệt nhau ở cả 32 lát**, và câu hỏi "tổn
thương nằm ở lát nào" không trả lời được. Bản đồ đó phóng lên 112×112×32 trông vẫn
mượt và vẫn thuyết phục, nên lỗi này không tự lộ ra.

Vì vậy `feature_layer_shapes` tồn tại: **đo hình dạng thật rồi mới chọn tầng**, không
suy luận. `grad_cam_3d` cũng từ chối chạy nếu tầng được chọn có chiều nào bằng 1.

Đánh đổi khi lùi về tầng nông hơn: bản đồ sắc nét hơn nhưng **ít mang tính lớp hơn**
(đặc trưng nông chung cho mọi lớp). Đây là đánh đổi thật, không có lựa chọn đúng
tuyệt đối; ghi lại tầng đã dùng cùng kết quả để người đọc tự đánh giá.
"""

from __future__ import annotations

from typing import Any

import numpy as np

__all__ = [
    "CANDIDATE_LAYERS",
    "feature_layer_shapes",
    "grad_cam_3d",
    "phase_importance",
    "resolve_layer",
]

# Các tầng đáng cân nhắc trong `model.features` của MONAI DenseNet, từ nông tới sâu.
# Danh sách này chỉ để *khảo sát*; tầng dùng thật phải chọn theo hình dạng đo được.
CANDIDATE_LAYERS: tuple[str, ...] = (
    "pool0",
    "transition1",
    "transition2",
    "denseblock3",
    "transition3",
    "denseblock4",
    "norm5",
)


def resolve_layer(model: Any, name: str) -> Any:
    """Lấy module con theo tên trong `model.features`, báo lỗi đọc được nếu sai tên."""
    features = getattr(model, "features", None)
    if features is None:
        raise AttributeError("model không có `.features` — đây có phải DenseNet của MONAI?")
    module = getattr(features, name, None)
    if module is None:
        available = [n for n, _ in features.named_children()]
        raise KeyError(f"không có tầng {name!r}. Các tầng hiện có: {available}")
    return module


def feature_layer_shapes(
    model: Any, input_shape: tuple[int, int, int, int, int]
) -> dict[str, tuple[int, ...]]:
    """Hình dạng đầu ra của từng tầng ứng viên, đo bằng một lượt forward giả.

    Gọi hàm này **trước** khi chạy cả mẻ. Nó là cách duy nhất biết chắc tầng nào còn
    đủ độ phân giải theo Z — số liệu ở docstring module là tính tay, và tính tay thì
    sai được.
    """
    import torch

    shapes: dict[str, tuple[int, ...]] = {}
    handles = []
    features = getattr(model, "features", None)
    if features is None:
        raise AttributeError("model không có `.features`")

    def make_hook(name: str):
        def hook(_module: Any, _inputs: Any, output: Any) -> None:
            shapes[name] = tuple(int(v) for v in output.shape)

        return hook

    for name, module in features.named_children():
        handles.append(module.register_forward_hook(make_hook(name)))

    was_training = model.training
    model.eval()
    try:
        with torch.no_grad():
            model(torch.zeros(input_shape))
    finally:
        for handle in handles:
            handle.remove()
        model.train(was_training)
    return shapes


def grad_cam_3d(
    model: Any,
    volume: Any,
    target_class: int,
    layer: str = "denseblock3",
    output_shape: tuple[int, int, int] | None = None,
) -> tuple[np.ndarray, tuple[int, ...]]:
    """Bản đồ Grad-CAM cho một mẫu. Trả về ``(cam, hình_dạng_gốc_của_cam)``.

    `volume` là tensor ``[1, C, X, Y, Z]``. `cam` được chuẩn hoá về [0, 1] và nội suy
    lên `output_shape` (mặc định: đúng kích thước không gian của `volume`).

    **Trả về cả hình dạng gốc** vì đó là thông tin phải hiển thị cho người dùng: một
    bản đồ 7×7×2 phóng lên 112×112×32 trông mịn tới từng voxel nhưng không hề mịn, và
    giấu con số đó đi là để người xem tự tin hơn mức dữ liệu cho phép.

    ReLU sau tổ hợp là đúng bản gốc (Selvaraju và cs. 2017): chỉ giữ phần đẩy logit
    **lên**. Bỏ ReLU sẽ trộn bằng chứng ủng hộ với bằng chứng phản đối vào một thang.
    """
    import torch.nn.functional as F

    target = resolve_layer(model, layer)
    store: dict[str, Any] = {}

    def forward_hook(_module: Any, _inputs: Any, output: Any) -> None:
        store["activations"] = output
        output.retain_grad()

    handle = target.register_forward_hook(forward_hook)
    was_training = model.training
    model.eval()
    try:
        model.zero_grad(set_to_none=True)
        logits = model(volume)
        logits[0, int(target_class)].backward()

        activations = store["activations"]
        gradients = activations.grad
        if gradients is None:
            raise RuntimeError(
                f"không có gradient ở tầng {layer!r}. Tầng này nằm ngoài đường lan "
                "truyền, hoặc model đang ở chế độ no_grad."
            )

        native = tuple(int(v) for v in activations.shape[2:])
        if any(v < 2 for v in native):
            raise ValueError(
                f"tầng {layer!r} cho bản đồ {native} — có chiều bằng 1, nghĩa là bản đồ "
                "hằng số theo chiều đó và không giải thích được gì. Chọn tầng nông hơn "
                "(xem `feature_layer_shapes`)."
            )

        # Trọng số kênh = gradient trung bình theo không gian (bản gốc Grad-CAM).
        weights = gradients.mean(dim=(2, 3, 4), keepdim=True)
        cam = F.relu((weights * activations).sum(dim=1, keepdim=True))

        size = output_shape or tuple(int(v) for v in volume.shape[2:])
        cam = F.interpolate(cam, size=size, mode="trilinear", align_corners=False)
        cam = cam[0, 0].detach().cpu().numpy().astype(np.float32)
    finally:
        handle.remove()
        model.train(was_training)

    peak = float(cam.max())
    # CAM toàn 0 xảy ra thật khi gradient của lớp đích âm ở mọi kênh. Trả về mảng 0
    # thay vì chia cho 0 — và người gọi thấy `max == 0` thì biết là không có gì để vẽ.
    return (cam / peak if peak > 0 else cam), native


def phase_importance(model: Any, volume: Any, target_class: int) -> np.ndarray:
    """Độ nhạy của logit lớp đích với từng thì MRI. Vector 8 phần tử, tổng bằng 1.

    Tính bằng ``|gradient × đầu vào|`` gộp theo không gian cho từng kênh — cùng họ với
    "input × gradient" trong văn liệu saliency.

    ⚠️ **Đây là độ nhạy cục bộ, KHÔNG phải phép ablation.** Nó trả lời "đổi nhẹ thì
    này thì logit đổi bao nhiêu", không trả lời "bỏ hẳn thì này thì mất bao nhiêu điểm
    macro-F1". Hai câu đó khác nhau, và câu thứ hai mới là thứ dùng để loại bớt thì
    khỏi pipeline. Muốn trả lời câu thứ hai thì phải train lại khi thiếu thì đó.

    ⚠️ Chuẩn hoá về tổng 1 khiến kết quả là **thứ hạng tương đối**, không phải độ lớn
    tuyệt đối: mọi ca đều cho tổng 1 kể cả khi mô hình gần như không nhạy với gì cả.
    """

    was_training = model.training
    model.eval()
    try:
        sample = volume.clone().requires_grad_(True)
        model.zero_grad(set_to_none=True)
        logits = model(sample)
        logits[0, int(target_class)].backward()
        if sample.grad is None:
            raise RuntimeError("không có gradient trên đầu vào")
        contribution = (sample.grad * sample).abs().sum(dim=(2, 3, 4))[0]
        values = contribution.detach().cpu().numpy().astype(np.float64)
    finally:
        model.train(was_training)

    total = float(values.sum())
    if total <= 0:
        return np.full(values.shape, 1.0 / values.size, dtype=np.float32)
    return (values / total).astype(np.float32)
