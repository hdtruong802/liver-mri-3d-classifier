"""Schema JSON của API.

Bám contract đã chốt ở `docs/liver_mri_3d_classification_plan.md` §8.1, mở rộng hai
trường: `defer_threshold` (frontend phải vẽ được ngưỡng, không chỉ kết quả so ngưỡng)
và `provenance`.

`provenance` là cơ chế trung thực của cả ứng dụng, không phải metadata phụ.
`PRODUCT.md` mục *Evidence on Hand* ghi: "Số placeholder trông giống số thật là rủi
ro nghiêm trọng nhất của dự án này — người review sẽ tưởng đó là kết quả." Đặt sự
thật đó ở **backend** nghĩa là frontend không thể vô tình trình bày số giả như số
thật; nó bắt buộc phải đọc `source` để biết mình đang vẽ gì.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class ProvenanceSource(StrEnum):
    """Con số trong phản hồi này từ đâu ra.

    - `oof`: prediction out-of-fold thật trên validation. Là số thật, đo được.
    - `live`: forward pass thật từ checkpoint đã nạp.
    """

    OOF = "oof"
    LIVE = "live"


class Provenance(BaseModel):
    source: ProvenanceSource
    model_version: str | None = Field(
        default=None,
        description="Phiên bản checkpoint. None khi chưa có model — không bịa chuỗi phiên bản.",
    )
    note: str = Field(
        description="Câu tiếng Việt giải thích nguồn số, hiển thị thẳng cho người dùng."
    )


class Uncertainty(BaseModel):
    """Các đại lượng bất định mà pipeline này **thực sự tính được**.

    Trường nào không đo được thì để `None`, không điền 0 — 0 là một khẳng định mạnh
    ("hoàn toàn không có bất định"), còn `None` là "chưa đo".

    `entropy` và `epistemic` **không thay thế được cho nhau**. Entropy là bất định
    *toàn phần* của một phân phối duy nhất: nó cao cả khi bài toán vốn mập mờ
    (aleatoric) lẫn khi model không biết (epistemic). `epistemic` tách riêng phần thứ
    hai bằng cách đo mức bất đồng **giữa** các lượt dự đoán. Endpoint khai báo rõ
    đại lượng dùng cho từng quyết định từ chối; so sánh các cách xếp hạng thuộc report.
    """

    entropy: float = Field(
        ge=0.0, description="Shannon entropy của phân phối đã hiệu chỉnh, đơn vị nat."
    )
    epistemic: float | None = Field(
        default=None,
        ge=0.0,
        description=(
            "Bất định epistemic = mutual information giữa các lượt dự đoán MC-dropout, "
            "đơn vị nat. `None` khi chỉ có một lượt (không đo được mức bất đồng)."
        ),
    )
    ensemble_std: float | None = Field(
        default=None,
        ge=0.0,
        description=(
            "Độ lệch chuẩn giữa các thành viên ensemble. `None` khi K=1. KHÁC "
            "`epistemic` cả về định nghĩa lẫn đơn vị — đừng dùng lẫn."
        ),
    )


class DeferBasis(StrEnum):
    """Quyết định từ chối dựa trên đại lượng nào.

    Hai đại lượng có chiều so sánh khác nhau:

    - `confidence` — max-prob của phân phối.
    - `epistemic` — mức bất đồng giữa các lượt dự đoán (MC-dropout). Từ chối theo nó
      là một dạng tín hiệu bất định riêng.

    Chiều so sánh **ngược nhau**: confidence thấp thì từ chối, epistemic cao thì từ
    chối. Frontend phải đọc trường này chứ không được giả định một chiều.
    """

    CONFIDENCE = "confidence"
    EPISTEMIC = "epistemic"


class ClassProbability(BaseModel):
    class_index: int = Field(ge=0, le=6)
    class_name: str = Field(description="Tên lớp trong `src/data/taxonomy.py`.")
    label_vi: str
    malignant: bool
    probability: float = Field(ge=0.0, le=1.0)


class PredictResult(BaseModel):
    """Kết quả suy luận cho một ca."""

    case_id: str
    pred_class_index: int = Field(ge=0, le=6)
    pred_class_name: str
    probs: list[ClassProbability] = Field(min_length=7, max_length=7)
    malignant_prob: float = Field(
        ge=0.0, le=1.0, description="Tổng xác suất của ba lớp ác: ICC, di căn, HCC."
    )
    uncertainty: Uncertainty
    # Live uploads use the max-prob policy locked on UniFormer OOF predictions.
    # `None` remains reserved for an incomplete result without a validated policy;
    # it must never be represented as a reassuring false value.
    defer: bool | None
    defer_basis: DeferBasis | None = Field(
        default=DeferBasis.CONFIDENCE,
        description="Đại lượng nào được so với ngưỡng để ra quyết định từ chối.",
    )
    defer_score: float | None = Field(
        default=None,
        ge=0.0,
        description=(
            "Giá trị của chính đại lượng nêu ở `defer_basis`, cho ca này. So nó với "
            "`defer_threshold`. KHÔNG phải lúc nào cũng bằng `confidence`."
        ),
    )
    defer_threshold: float | None = Field(
        default=None,
        ge=0.0,
        description=(
            "Ngưỡng khoá trên validation, cùng đơn vị với `defer_score`. Chiều so sánh "
            "phụ thuộc `defer_basis`: `confidence` thì DƯỚI ngưỡng là defer, "
            "`epistemic` thì TRÊN ngưỡng là defer."
        ),
    )
    confidence: float = Field(ge=0.0, le=1.0, description="max-prob của phân phối đã hiệu chỉnh.")
    # `heatmap_slices` (base64 PNG) đã bị bỏ ở S-093: nó luôn rỗng, frontend chưa từng
    # đọc, và giữ lại sẽ thành cơ chế thứ hai cạnh tranh với `CaseDetail.model_heatmap` +
    # endpoint ảnh. Hai đường cho cùng một việc là nợ, không phải linh hoạt.
    inference_ms: int | None = None
    provenance: Provenance


class PhaseInfo(BaseModel):
    index: int
    name: str
    file_token: str
    label_vi: str
    description_vi: str


class UploadPhaseState(StrEnum):
    """Trạng thái một thì bắt buộc sau khi đọc manifest ZIP."""

    READY = "ready"
    MISSING = "missing"
    DUPLICATE = "duplicate"


class UploadPhaseValidation(BaseModel):
    index: int
    file_token: str
    label_vi: str
    filename: str | None = None
    state: UploadPhaseState
    mask_filename: str | None = None
    mask_state: UploadPhaseState


class UploadValidationResult(BaseModel):
    """Kết quả kiểm tra cấu trúc ZIP trước khi suy luận trực tiếp."""

    archive_name: str
    valid: bool
    inference_ready: bool
    message: str
    errors: list[str] = Field(default_factory=list)
    phases: list[UploadPhaseValidation] = Field(min_length=8, max_length=8)


class UploadPredictionResult(UploadValidationResult):
    """Manifest cùng kết quả chỉ khi bộ MRI đủ contract ROI có mask."""

    prediction: PredictResult | None = None
    upload_view: UploadViewInfo | None = None


class ClassInfo(BaseModel):
    index: int
    name: str
    label_vi: str
    malignant: bool


class MetaResponse(BaseModel):
    """Nguồn sự thật cho frontend: taxonomy và danh sách thì.

    Frontend **không khai báo lại** hai danh sách này ở TypeScript. Bản bolt tự khai
    một taxonomy riêng và nó sai: thiếu ICC và áp-xe, thừa một lớp "gan khoẻ mạnh"
    không tồn tại trong bài toán.
    """

    classes: list[ClassInfo] = Field(min_length=7, max_length=7)
    phases: list[PhaseInfo] = Field(min_length=8, max_length=8)
    ruo_notice: str
    default_defer_threshold: float


class CaseVolumeInfo(BaseModel):
    """Hình học thật của volume, đọc từ file NIfTI."""

    phase_name: str
    file_token: str
    shape: list[int] = Field(min_length=3, max_length=3)
    spacing_mm: list[float] = Field(min_length=3, max_length=3)
    n_slices: int
    has_mask: bool = Field(
        default=False,
        description=(
            "Có nhãn segmentation OFFICIAL của LLD-MMRI cho thì này không. Đây là nhãn "
            "do người chú giải, KHÔNG phải đầu ra của model — dự án không làm "
            "segmentation (AGENTS.md §3.9)."
        ),
    )
    mask_slices: list[int] = Field(
        default_factory=list,
        description=(
            "Chỉ số lát (0-based) có ít nhất một voxel tổn thương, để đánh dấu trên "
            "thanh trượt. Cùng nguồn với `has_mask`: nhãn của người chú giải, KHÔNG "
            "phải vùng model tìm ra. Rỗng khi thì này không có mask."
        ),
    )


class UploadViewInfo(BaseModel):
    """A short-lived, in-memory UniFormer crop made available after upload."""

    upload_id: str
    volumes: list[CaseVolumeInfo] = Field(min_length=8, max_length=8)
    expires_in_seconds: int = Field(gt=0)
    note: str


class ModelHeatmapInfo(BaseModel):
    """Metadata for validated, precomputed model-sensitivity overlays."""

    available: bool
    phase_tokens: list[str] = Field(default_factory=list, max_length=8)
    n_slices: int = Field(ge=0)
    pred_class_index: int | None = Field(default=None, ge=0, le=6)
    lesion_slices: dict[str, list[int]] = Field(default_factory=dict)
    note: str = ""


class CaseSummary(BaseModel):
    case_id: str
    label_vi: str
    source_note: str
    available: bool = Field(description="False khi thư mục dữ liệu không có trên máy này.")


class CaseDetail(BaseModel):
    case_id: str
    label_vi: str
    source_note: str
    volumes: list[CaseVolumeInfo]
    reference_phase: str
    provenance: Provenance
    model_heatmap: ModelHeatmapInfo | None = None


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    sample_dir_present: bool
