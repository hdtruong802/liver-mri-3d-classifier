"""FastAPI app cho web app demo.

    uvicorn webapp.backend.main:app --reload

Chạy local. Kaggle không phải server và không bao giờ host API ở đó (`AGENTS.md` §7).
"""

from __future__ import annotations

import time

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import Response
from src.data.taxonomy import CLASS_NAMES, MALIGNANT_INDICES, NUM_CLASSES, SHORT_NAMES

from webapp.backend import demo_cases, inference
from webapp.backend.config import DEFAULT_DEFER_THRESHOLD, RUO_NOTICE, SAMPLE_DIR
from webapp.backend.phases import PHASES, PhaseDetectionError, detect_phase_set
from webapp.backend.schemas import (
    CaseDetail,
    CaseSummary,
    ClassInfo,
    HealthResponse,
    MetaResponse,
    PhaseInfo,
    PredictResult,
)
from webapp.backend.volumes import render_slice_png

app = FastAPI(
    title="Liver MRI 3D Classifier — demo API",
    description=(
        "Research Use Only, chưa kiểm định lâm sàng. "
        "Mọi phản hồi mang trường `provenance` cho biết con số từ đâu ra."
    ),
    version="0.1.0",
)


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        model_loaded=inference.model_is_loaded(),
        sample_dir_present=SAMPLE_DIR.is_dir(),
    )


@app.get("/api/meta", response_model=MetaResponse)
def meta() -> MetaResponse:
    """Taxonomy và danh sách thì — nguồn sự thật cho frontend.

    Frontend không khai báo lại hai danh sách này. Bản bolt tự khai một taxonomy
    riêng và nó sai: thiếu ICC và áp-xe, thừa một lớp "gan khoẻ mạnh" không có trong
    bài toán này.
    """
    return MetaResponse(
        classes=[
            ClassInfo(
                index=i,
                name=CLASS_NAMES[i],
                label_vi=SHORT_NAMES[i],
                malignant=i in MALIGNANT_INDICES,
            )
            for i in range(NUM_CLASSES)
        ],
        phases=[
            PhaseInfo(
                index=p.index,
                name=p.name,
                file_token=p.file_token,
                label_vi=p.label_vi,
                description_vi=p.description_vi,
            )
            for p in PHASES
        ],
        ruo_notice=RUO_NOTICE,
        default_defer_threshold=DEFAULT_DEFER_THRESHOLD,
    )


@app.get("/api/cases", response_model=list[CaseSummary])
def list_cases() -> list[CaseSummary]:
    return demo_cases.list_cases()


@app.get("/api/cases/{case_id}", response_model=CaseDetail)
def case_detail(case_id: str) -> CaseDetail:
    if case_id not in demo_cases.CASES_BY_ID:
        raise HTTPException(status_code=404, detail=f"không có ca demo {case_id!r}")
    if not demo_cases.case_is_available(demo_cases.CASES_BY_ID[case_id]):
        raise HTTPException(
            status_code=503,
            detail=(
                f"dữ liệu của ca {case_id!r} không có trên máy này. "
                f"Đặt LLDMMRI_SAMPLE_DIR trỏ tới thư mục chứa 8 file .nii của ca."
            ),
        )
    return demo_cases.get_case_detail(case_id)


@app.get(
    "/api/cases/{case_id}/slice",
    responses={200: {"content": {"image/png": {}}}},
    response_class=Response,
)
def case_slice(case_id: str, phase: str, z: int, mask: bool = False) -> Response:
    """Render một lát của một thì ra PNG.

    `phase` là `file_token` (vd `C+V`, `InPhase`). Ảnh thật, đọc từ NIfTI trên đĩa.

    `mask=true` phủ **nhãn segmentation official của LLD-MMRI** lên. Đây là nhãn do
    người chú giải, không phải đầu ra của model — dự án không làm segmentation
    (AGENTS.md §3.9). Ca không có mask thì trả 404 thay vì lặng lẽ trả ảnh trần: gọi
    xin mask mà nhận ảnh không mask là một sự im lặng dễ bị đọc nhầm thành
    "model không tìm thấy tổn thương nào".
    """
    path = demo_cases.volume_path(case_id, phase)
    if path is None:
        raise HTTPException(
            status_code=404, detail=f"không có volume cho ca {case_id!r} thì {phase!r}"
        )
    overlay = None
    if mask:
        overlay = demo_cases.mask_path(case_id, phase)
        if overlay is None:
            raise HTTPException(
                status_code=404, detail=f"không có mask cho ca {case_id!r} thì {phase!r}"
            )
    try:
        payload = render_slice_png(path, z, overlay)
    except IndexError as exc:
        raise HTTPException(status_code=416, detail=str(exc)) from exc
    except ValueError as exc:  # mask lệch hình học so với ảnh
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    # Ảnh bệnh nhân: cache ở trình duyệt trong phiên, không để proxy trung gian giữ.
    return Response(
        content=payload, media_type="image/png", headers={"Cache-Control": "private, max-age=3600"}
    )


@app.get(
    "/api/cases/{case_id}/gradcam",
    responses={200: {"content": {"image/png": {}}}},
    response_class=Response,
)
def case_gradcam(case_id: str, z: int, target: str = "pred") -> Response:
    """Một lát của bản đồ chú ý, phủ lên khối 112×112×32 mà mô hình thực sự nhìn.

    ⚠️ Ảnh này **không cùng không gian** với `/slice`: đó là lát gốc 480×480, còn đây
    là khối đã cắt bám tổn thương. Số lát cũng khác nhau.

    `target='true'` chỉ có khi mô hình đoán sai — khi đó so hai bản đồ cho thấy mô
    hình đã nhìn nhầm chỗ nào.
    """
    from webapp.backend import gradcam as gradcam_store

    cam = gradcam_store.get(case_id)
    if cam is None:
        raise HTTPException(status_code=404, detail=f"chưa có bản đồ chú ý cho ca {case_id!r}")
    try:
        payload = gradcam_store.render_png(cam, target, z)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except IndexError as exc:
        raise HTTPException(status_code=416, detail=str(exc)) from exc
    return Response(
        content=payload, media_type="image/png", headers={"Cache-Control": "private, max-age=3600"}
    )


@app.post("/api/cases/{case_id}/predict", response_model=PredictResult)
def predict_case(case_id: str) -> PredictResult:
    """Suy luận trên một ca demo dựng sẵn — đường đi chính."""
    if case_id not in demo_cases.CASES_BY_ID:
        raise HTTPException(status_code=404, detail=f"không có ca demo {case_id!r}")
    started = time.perf_counter()
    result = inference.predict(case_id)
    result.inference_ms = int((time.perf_counter() - started) * 1000)
    return result


@app.post("/api/predict", response_model=PredictResult)
async def predict_upload(files: list[UploadFile]) -> PredictResult:
    """Suy luận trên bộ 8 file người dùng tải lên — đường phụ.

    Nhận diện thì theo **token trong tên file**, không theo thứ tự chọn (contract
    plan §8.1). Bộ file thiếu hoặc trùng thì bị từ chối thẳng: chấp nhận im lặng một
    bộ đầu vào sai sẽ cho ra một con số trông hợp lý mà vô nghĩa.

    Giới hạn đã biết, hiển thị luôn ở frontend: pipeline train cắt bám tổn thương nên
    đường này chưa có ROI và chưa chạy đúng như lúc train. Đó là lý do ca demo dựng
    sẵn mới là đường đi chính.
    """
    names = [f.filename or "" for f in files]
    try:
        detected = detect_phase_set(names)
    except PhaseDetectionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # Định danh ca tất định theo bộ tên file, để cùng bộ upload cho cùng màn hình.
    case_id = "upload:" + ",".join(sorted(detected.values()))
    started = time.perf_counter()
    result = inference.predict(case_id)
    result.case_id = "upload"
    result.inference_ms = int((time.perf_counter() - started) * 1000)
    return result
