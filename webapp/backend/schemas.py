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

    - `simulated`: sinh ra để dựng giao diện. **Chưa có model.** Frontend bắt buộc
      đánh dấu bằng cả chữ nghiêng lẫn nhãn chữ (`webapp/DESIGN.md`).
    - `oof`: prediction out-of-fold thật trên validation. Là số thật, đo được.
    - `live`: forward pass thật từ checkpoint đã nạp.
    """

    SIMULATED = "simulated"
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
    """Hai đại lượng bất định mà pipeline này thực sự tính được.

    Cố ý **không** có epistemic/aleatoric tách đôi: dự án không phân rã như vậy, và
    báo một chỉ số không tính được là bịa. `ensemble_std` là None khi chạy một model
    đơn lẻ, không phải 0 — 0 nghĩa là các thành viên ensemble đồng thuận tuyệt đối.
    """

    entropy: float = Field(
        ge=0.0, description="Shannon entropy của phân phối đã hiệu chỉnh, đơn vị nat."
    )
    ensemble_std: float | None = Field(
        default=None,
        ge=0.0,
        description="Độ lệch chuẩn giữa các thành viên ensemble. None khi K=1.",
    )


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
    defer: bool
    defer_threshold: float = Field(
        ge=0.0, le=1.0, description="Ngưỡng confidence khoá trên validation; dưới ngưỡng thì defer."
    )
    confidence: float = Field(ge=0.0, le=1.0, description="max-prob của phân phối đã hiệu chỉnh.")
    heatmap_slices: list[str] = Field(
        default_factory=list,
        description="Grad-CAM base64 PNG. Rỗng khi chưa có — frontend vẽ gạch chéo.",
    )
    inference_ms: int | None = None
    provenance: Provenance


class PhaseInfo(BaseModel):
    index: int
    name: str
    file_token: str
    label_vi: str
    description_vi: str


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


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    sample_dir_present: bool
