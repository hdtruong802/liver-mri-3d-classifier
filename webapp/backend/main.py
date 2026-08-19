"""FastAPI app cho web app demo.

    uvicorn webapp.backend.main:app --reload

Chạy local. Kaggle không phải server và không bao giờ host API ở đó (`AGENTS.md` §7).
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path, PurePosixPath
from zipfile import BadZipFile, ZipFile, ZipInfo

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import Response
from src.data.taxonomy import CLASS_NAMES, MALIGNANT_INDICES, NUM_CLASSES, SHORT_NAMES

from webapp.backend.config import (
    DEFAULT_DEFER_THRESHOLD,
    RUO_NOTICE,
    UPLOAD_MAX_ENTRIES,
    UPLOAD_MAX_UNCOMPRESSED_BYTES,
)
from webapp.backend.phases import PHASES, PhaseDetectionError, detect_phase
from webapp.backend.schemas import (
    ClassInfo,
    HealthResponse,
    MetaResponse,
    PhaseInfo,
    UploadPhaseState,
    UploadPhaseValidation,
    UploadPredictionResult,
    UploadValidationResult,
)
from webapp.backend.upload_views import upload_studies

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
    from webapp.backend import live_inference

    return HealthResponse(status="ok", model_loaded=live_inference.is_available())


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


@app.get(
    "/api/uploads/{upload_id}/slice",
    responses={200: {"content": {"image/png": {}}}},
    response_class=Response,
)
def upload_slice(upload_id: str, phase: str, z: int, mask: bool = False) -> Response:
    """Render the original MRI retained briefly for a completed upload.

    The image is the source NIfTI, not the UniFormer crop. The optional overlay
    is the user's supplied annotation, not a segmentation output from this
    classifier.
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
            image_errors.append(f"{name!r} phải nằm trong thư mục images/ hoặc masks/ của ZIP.")
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

    temporary_directory: Path | None = None
    retained_by_viewer = False
    try:
        with ZipFile(archive.file) as bundle:
            infos = _safe_zip_infos(bundle)
            manifest, image_names, mask_names = _inspect_upload(
                archive_name, [entry.filename for entry in infos]
            )
            if not manifest.inference_ready:
                return UploadPredictionResult(**manifest.model_dump(), prediction=None)
            temporary_directory = Path(tempfile.mkdtemp(prefix="liver-mri-upload-"))
            image_paths, mask_paths = _extract_for_inference(
                bundle, infos, image_names, mask_names, temporary_directory
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
            prediction = live_inference.predict_uploaded(archive_name, image_paths, mask_paths)
            upload_view = upload_studies.create(image_paths, mask_paths, temporary_directory)
            retained_by_viewer = True
    except BadZipFile as exc:
        raise HTTPException(status_code=422, detail="File tải lên không phải ZIP hợp lệ.") from exc
    except (OSError, ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        if temporary_directory is not None and not retained_by_viewer:
            shutil.rmtree(temporary_directory, ignore_errors=True)
    return UploadPredictionResult(
        **manifest.model_dump(), prediction=prediction, upload_view=upload_view
    )
