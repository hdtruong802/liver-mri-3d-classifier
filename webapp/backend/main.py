"""FastAPI app cho web app demo.

    uvicorn webapp.backend.main:app --reload

Chạy local. Kaggle không phải server và không bao giờ host API ở đó (`AGENTS.md` §7).
"""

from __future__ import annotations

import tempfile
from pathlib import Path, PurePosixPath
from zipfile import BadZipFile, ZipFile, ZipInfo

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import Response
from src.data.taxonomy import CLASS_NAMES, MALIGNANT_INDICES, NUM_CLASSES, SHORT_NAMES

from webapp.backend import demo_cases, inference
from webapp.backend.config import (
    DEFAULT_DEFER_THRESHOLD,
    RUO_NOTICE,
    SAMPLE_DIR,
    UPLOAD_MAX_ENTRIES,
    UPLOAD_MAX_UNCOMPRESSED_BYTES,
)
from webapp.backend.phases import PHASES, PhaseDetectionError, detect_phase
from webapp.backend.schemas import (
    CaseDetail,
    CaseSummary,
    ClassInfo,
    HealthResponse,
    MetaResponse,
    PhaseInfo,
    PredictResult,
    UploadPhaseState,
    UploadPhaseValidation,
    UploadPredictionResult,
    UploadValidationResult,
)
from webapp.backend.upload_views import upload_studies
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
    "/api/uploads/{upload_id}/slice",
    responses={200: {"content": {"image/png": {}}}},
    response_class=Response,
)
def upload_slice(upload_id: str, phase: str, z: int, mask: bool = False) -> Response:
    """Render the short-lived ROI crop retained for a completed upload.

    The crop is the exact 112×112×14 input seen by UniFormer. It is not the
    raw NIfTI and the optional overlay is the user's supplied annotation, not
    a segmentation output from this classifier.
    """
    try:
        payload = upload_studies.render(upload_id, phase, z, annotation=mask)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except IndexError as exc:
        raise HTTPException(status_code=416, detail=str(exc)) from exc
    if payload is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Ảnh của bộ MRI tải lên đã hết hạn hoặc server đã khởi động lại. "
                "Hãy tải ZIP lên lại."
            ),
        )
    return Response(content=payload, media_type="image/png", headers={"Cache-Control": "no-store"})


@app.get(
    "/api/cases/{case_id}/model-view",
    responses={200: {"content": {"image/png": {}}}},
    response_class=Response,
)
def case_model_view(
    case_id: str,
    phase: str = "C-pre",
    z: int = 0,
    annotation: bool = False,
    heatmap: bool = False,
) -> Response:
    """Render crop E4 theo thứ tự MRI → heatmap → nhãn người chú giải."""
    from webapp.backend import model_heatmaps

    artifact = model_heatmaps.get(case_id)
    if artifact is None:
        raise HTTPException(status_code=404, detail=f"chưa có heatmap đa thì cho ca {case_id!r}")
    try:
        payload = model_heatmaps.render_png(
            artifact, phase, z, annotation=annotation, heatmap=heatmap
        )
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
    try:
        return inference.predict(case_id)
    except LookupError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


def _is_nifti(name: str) -> bool:
    return name.lower().endswith((".nii", ".nii.gz"))


def _archive_role(name: str) -> str | None:
    """Classify a NIfTI by its directory, never by upload order."""
    parts = [part.lower() for part in PurePosixPath(name.replace("\\", "/")).parts[:-1]]
    if "images" in parts:
        return "image"
    if "masks" in parts:
        return "mask"
    return None


def _inspect_upload(
    archive_name: str, names: list[str]
) -> tuple[UploadValidationResult, dict[str, str], dict[str, str]]:
    """Validate ZIP layout and return accepted image/mask paths by phase token."""
    image_found: dict[str, list[str]] = {phase.file_token: [] for phase in PHASES}
    mask_found: dict[str, list[str]] = {phase.file_token: [] for phase in PHASES}
    image_errors: list[str] = []
    mask_errors: list[str] = []
    nifti_names = [name for name in names if _is_nifti(name)]
    if not nifti_names:
        image_errors.append("ZIP không chứa file NIfTI .nii hoặc .nii.gz.")

    for name in nifti_names:
        role = _archive_role(name)
        if role is None:
            image_errors.append(
                f"{name!r} phải nằm trong thư mục images/ hoặc masks/ của ZIP."
            )
            continue
        leaf_name = name.replace("\\", "/").rsplit("/", 1)[-1]
        try:
            phase = detect_phase(leaf_name)
        except PhaseDetectionError as exc:
            (image_errors if role == "image" else mask_errors).append(str(exc))
            continue
        target = image_found if role == "image" else mask_found
        target[phase.file_token].append(name)

    rows: list[UploadPhaseValidation] = []
    images: dict[str, str] = {}
    masks: dict[str, str] = {}
    for phase in PHASES:
        image_files = image_found[phase.file_token]
        mask_files = mask_found[phase.file_token]
        image_filename = " · ".join(image_files) if image_files else None
        mask_filename = " · ".join(mask_files) if mask_files else None
        image_state = (
            UploadPhaseState.DUPLICATE
            if len(image_files) > 1
            else UploadPhaseState.READY
            if image_files
            else UploadPhaseState.MISSING
        )
        mask_state = (
            UploadPhaseState.DUPLICATE
            if len(mask_files) > 1
            else UploadPhaseState.READY
            if mask_files
            else UploadPhaseState.MISSING
        )
        if image_state is UploadPhaseState.DUPLICATE:
            image_errors.append(f"trùng ảnh thì {phase.label_vi}: {image_filename}")
        elif image_state is UploadPhaseState.READY:
            images[phase.file_token] = image_files[0]
        if mask_state is UploadPhaseState.DUPLICATE:
            mask_errors.append(f"trùng mask thì {phase.label_vi}: {mask_filename}")
        elif mask_state is UploadPhaseState.READY:
            masks[phase.file_token] = mask_files[0]
        rows.append(
            UploadPhaseValidation(
                index=phase.index,
                file_token=phase.file_token,
                label_vi=phase.label_vi,
                filename=image_filename,
                state=image_state,
                mask_filename=mask_filename,
                mask_state=mask_state,
            )
        )

    valid = not image_errors and len(images) == len(PHASES)
    inference_ready = valid and not mask_errors and len(masks) == len(PHASES)
    errors = [*image_errors, *mask_errors]
    if inference_ready:
        message = "Bộ MRI và 8 mask hợp lệ. Sẵn sàng chạy ensemble UniFormer."
    elif valid:
        message = (
            "Đủ 8 ảnh MRI. Cần thêm đúng 8 mask tổn thương trong masks/ "
            "để dựng crop ROI UniFormer và chạy AI."
        )
    else:
        message = (
            "Bộ MRI chưa đúng cấu trúc. Hãy đặt 8 ảnh vào images/ và đặt tên file có token thì MRI."
        )
    return (
        UploadValidationResult(
            archive_name=archive_name,
            valid=valid,
            inference_ready=inference_ready,
            message=message,
            errors=errors,
            phases=rows,
        ),
        images,
        masks,
    )


def _safe_zip_infos(bundle: ZipFile) -> list[ZipInfo]:
    infos = [entry for entry in bundle.infolist() if not entry.is_dir()]
    if len(infos) > UPLOAD_MAX_ENTRIES:
        raise HTTPException(status_code=422, detail="ZIP có quá nhiều file.")
    total_size = 0
    for entry in infos:
        pure_path = PurePosixPath(entry.filename.replace("\\", "/"))
        if pure_path.is_absolute() or any(part in {"", ".", ".."} for part in pure_path.parts):
            raise HTTPException(status_code=422, detail="ZIP chứa đường dẫn file không an toàn.")
        total_size += entry.file_size
        if total_size > UPLOAD_MAX_UNCOMPRESSED_BYTES:
            raise HTTPException(status_code=422, detail="ZIP vượt dung lượng giải nén cho phép.")
    return infos


def _copy_zip_entry(bundle: ZipFile, entry: ZipInfo, destination: Path) -> None:
    written = 0
    with bundle.open(entry) as source, destination.open("wb") as target:
        while chunk := source.read(1024 * 1024):
            written += len(chunk)
            if written > UPLOAD_MAX_UNCOMPRESSED_BYTES:
                raise ValueError("NIfTI trong ZIP vượt dung lượng giải nén cho phép")
            target.write(chunk)


def _extract_for_inference(
    bundle: ZipFile,
    infos: list[ZipInfo],
    image_names: dict[str, str],
    mask_names: dict[str, str],
    directory: Path,
) -> tuple[dict[str, Path], dict[str, Path]]:
    by_name = {entry.filename: entry for entry in infos}

    def extract_group(names: dict[str, str], prefix: str) -> dict[str, Path]:
        paths: dict[str, Path] = {}
        for token, source_name in names.items():
            entry = by_name.get(source_name)
            if entry is None:
                raise ValueError(f"không tìm thấy {source_name!r} trong ZIP")
            suffix = ".nii.gz" if source_name.lower().endswith(".nii.gz") else ".nii"
            target = directory / f"{prefix}_{token}{suffix}"
            _copy_zip_entry(bundle, entry, target)
            paths[token] = target
        return paths

    return extract_group(image_names, "image"), extract_group(mask_names, "mask")


def _upload_manifest(archive_name: str, names: list[str]) -> UploadValidationResult:
    """Compatibility wrapper for callers that need only the upload manifest."""
    return _inspect_upload(archive_name, names)[0]


@app.post("/api/validate-upload", response_model=UploadValidationResult)
async def validate_upload(archive: UploadFile) -> UploadValidationResult:
    """Kiểm tra manifest một ZIP MRI, không lưu file, không tạo prediction."""
    archive_name = archive.filename or "upload.zip"
    if not archive_name.lower().endswith(".zip"):
        raise HTTPException(status_code=422, detail="Chỉ nhận một file .zip.")

    try:
        with ZipFile(archive.file) as bundle:
            names = [entry.filename for entry in _safe_zip_infos(bundle)]
    except BadZipFile as exc:
        raise HTTPException(status_code=422, detail="File tải lên không phải ZIP hợp lệ.") from exc

    return _upload_manifest(archive_name, names)


@app.post("/api/predict-upload", response_model=UploadPredictionResult)
async def predict_upload(archive: UploadFile) -> UploadPredictionResult:
    """Run UniFormer only when ZIP contains the complete MRI + mask contract."""
    archive_name = archive.filename or "upload.zip"
    if not archive_name.lower().endswith(".zip"):
        raise HTTPException(status_code=422, detail="Chỉ nhận một file .zip.")

    try:
        with ZipFile(archive.file) as bundle:
            infos = _safe_zip_infos(bundle)
            manifest, image_names, mask_names = _inspect_upload(
                archive_name, [entry.filename for entry in infos]
            )
            if not manifest.inference_ready:
                return UploadPredictionResult(**manifest.model_dump(), prediction=None)
            with tempfile.TemporaryDirectory(prefix="liver-mri-upload-") as temp_dir:
                image_paths, mask_paths = _extract_for_inference(
                    bundle, infos, image_names, mask_names, Path(temp_dir)
                )
                from webapp.backend import live_inference

                if not live_inference.is_available():
                    raise HTTPException(
                        status_code=503,
                        detail=(
                            "Máy chủ chưa có đủ weights UniFormer hoặc runtime PyTorch "
                            "để chạy suy luận."
                        ),
                    )
                inference_result = live_inference.predict_uploaded(
                    archive_name, image_paths, mask_paths
                )
    except BadZipFile as exc:
        raise HTTPException(status_code=422, detail="File tải lên không phải ZIP hợp lệ.") from exc
    except (OSError, ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    upload_view = upload_studies.create(
        inference_result.crop_volume,
        inference_result.annotation_masks,
        inference_result.spacing_mm,
    )
    return UploadPredictionResult(
        **manifest.model_dump(), prediction=inference_result.prediction, upload_view=upload_view
    )
