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

## Cạm bẫy thứ hai: Grad-CAM gốc giả định đặc trưng KHÔNG ÂM

Grad-CAM (Selvaraju và cs. 2017) gộp kênh bằng **một trọng số cho cả bản đồ**:
``w_k = mean(∂y/∂A_k)``, rồi ``relu(Σ_k w_k · A_k)``. Phép đó chỉ hợp lý khi `A_k ≥ 0`
— đúng với VGG/ResNet, nơi tầng được hook nằm ngay sau ReLU.

**DenseNet không thoả.** Mỗi `_DenseLayer` của MONAI là norm→relu→conv, nên đầu ra của
một dense block là **concat các đầu ra conv** và có cả giá trị âm. Khi đó tổ hợp
``Σ_k w_k · A_k`` có thể âm ở *mọi* voxel, ReLU quét sạch, và bản đồ **toàn 0** — đúng
lỗi gặp ở ca `MR207769` (WORKLOG S-095). Nó không phải bug: nó là giả định bị vi phạm.

Vì vậy mặc định của module này là **HiResCAM** (Draelos & Carin 2020):
``relu(Σ_k (∂y/∂A_k) ⊙ A_k)`` — nhân theo từng phần tử thay vì gộp gradient trước.
Tổng chưa ReLU của nó **chính là** khai triển Taylor bậc nhất của logit theo vị trí
không gian, nên nó đúng cho cả đặc trưng có dấu. Grad-CAM gốc vẫn gọi được bằng
``mode="gradcam"`` để đối chiếu.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

__all__ = [
    "CANDIDATE_LAYERS",
    "CamResult",
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


@dataclass(frozen=True)
class CamResult:
    """Bản đồ cùng số liệu chẩn đoán. `degenerate=True` là KẾT QUẢ, không phải lỗi.

    Bản đồ suy biến (tổ hợp ≤ 0 ở mọi voxel) có nghĩa khác nhau tuỳ câu hỏi:

    - Với **lớp model đã đoán**: đáng ngờ. Model chọn lớp đó thì phải có chỗ nào đó
      ủng hộ nó; không có chỗ nào là dấu hiệu sai tầng hoặc sai chế độ eval.
    - Với **lớp thật mà model đoán trượt**: hoàn toàn hợp lý, và là một phát hiện —
      "mô hình không tìm thấy bằng chứng nào cho lớp đúng, ở bất kỳ đâu".

    Hai cách đọc ngược nhau, nên hàm này **không** tự quyết định cái nào là lỗi. Nó
    trả số liệu; người gọi đặt chính sách.
    """

    cam: np.ndarray
    native_shape: tuple[int, ...]
    degenerate: bool
    combined_min: float
    combined_max: float
    negative_fraction: float

    def explain(self) -> str:
        """Câu chẩn đoán đọc được, dùng cho thông báo lỗi và cho UI."""
        return (
            f"tổ hợp trong [{self.combined_min:.3e}, {self.combined_max:.3e}], "
            f"{self.negative_fraction:.0%} đặc trưng âm, bản đồ gốc {self.native_shape}"
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
    mode: str = "hires",
) -> CamResult:
    """Bản đồ Grad-CAM cho một mẫu.

    `volume` là tensor ``[1, C, X, Y, Z]``. `cam` được chuẩn hoá về [0, 1] và nội suy
    lên `output_shape` (mặc định: đúng kích thước không gian của `volume`).

    **Trả về cả hình dạng gốc** vì đó là thông tin phải hiển thị cho người dùng: một
    bản đồ 7×7×2 phóng lên 112×112×32 trông mịn tới từng voxel nhưng không hề mịn, và
    giấu con số đó đi là để người xem tự tin hơn mức dữ liệu cho phép.

    `mode`:

    - ``"hires"`` (mặc định) — HiResCAM: ``relu(Σ_k grad_k ⊙ A_k)``, nhân theo từng
      phần tử. Đúng cho đặc trưng **có dấu**, tức là đúng cho DenseNet. Xem docstring
      module.
    - ``"gradcam"`` — bản gốc: ``relu(Σ_k mean(grad_k) · A_k)``. Giữ lại để đối chiếu;
      trên kiến trúc này nó **có thể cho bản đồ toàn 0** ở một số ca.

    ReLU sau tổ hợp giữ ở cả hai chế độ, đúng tinh thần bản gốc: chỉ giữ phần đẩy logit
    **lên**. Bỏ ReLU sẽ trộn bằng chứng ủng hộ với bằng chứng phản đối vào một thang.

    **Không nổ khi bản đồ suy biến** (tổ hợp ≤ 0 ở mọi voxel). Nó đánh dấu
    `degenerate=True` và trả số liệu chẩn đoán, vì cùng một hiện tượng mang hai nghĩa
    ngược nhau tuỳ lớp đích đang hỏi — xem docstring `CamResult`. Người gọi đặt chính
    sách; thư viện chỉ đo.
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

        if mode == "hires":
            combined = (gradients * activations).sum(dim=1, keepdim=True)
        elif mode == "gradcam":
            weights = gradients.mean(dim=(2, 3, 4), keepdim=True)
            combined = (weights * activations).sum(dim=1, keepdim=True)
        else:
            raise ValueError(f"mode phải là 'hires' hoặc 'gradcam', nhận {mode!r}")

        cam_raw = F.relu(combined)
        peak = float(cam_raw.max().detach())
        stats = (
            float(combined.min().detach()),
            float(combined.max().detach()),
            float((activations < 0).float().mean().detach()),
        )

        size = output_shape or tuple(int(v) for v in volume.shape[2:])
        cam_t = F.interpolate(cam_raw, size=size, mode="trilinear", align_corners=False)
        cam = cam_t[0, 0].detach().cpu().numpy().astype(np.float32)
    finally:
        handle.remove()
        model.train(was_training)

    # Chia cho đỉnh CHỈ khi có đỉnh. Bản đồ suy biến giữ nguyên toàn 0 và được đánh
    # dấu — người gọi quyết định đó là lỗi hay là kết quả (xem docstring `CamResult`).
    if peak > 0:
        cam = cam / float(cam.max())
    return CamResult(
        cam=cam,
        native_shape=native,
        degenerate=peak <= 0,
        combined_min=stats[0],
        combined_max=stats[1],
        negative_fraction=stats[2],
    )


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
