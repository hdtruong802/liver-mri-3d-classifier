"""Short-lived in-memory MRI crops for uploaded studies.

The original ZIP and NIfTI files are deleted as soon as inference completes.
This store retains only the normalized, deterministic ROI crop passed to
UniFormer and its paired human annotation mask, long enough for the user to
inspect the result in the same server session.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from uuid import uuid4

import numpy as np

from webapp.backend.config import UPLOAD_VIEW_MAX_STUDIES, UPLOAD_VIEW_TTL_SECONDS
from webapp.backend.phases import PHASE_BY_TOKEN, PHASES
from webapp.backend.schemas import CaseVolumeInfo, UploadViewInfo
from webapp.backend.volumes import render_array_slice_png


@dataclass(frozen=True)
class UploadStudy:
    """One retained ROI study; no raw patient file paths or uploads are stored."""

    volumes: dict[str, np.ndarray]
    masks: dict[str, np.ndarray]
    expires_at: float


class UploadStudyStore:
    """Thread-safe bounded cache for the upload image viewer."""

    def __init__(
        self,
        *,
        ttl_seconds: int = UPLOAD_VIEW_TTL_SECONDS,
        max_studies: int = UPLOAD_VIEW_MAX_STUDIES,
    ) -> None:
        if ttl_seconds <= 0 or max_studies <= 0:
            raise ValueError("upload viewer cache limits phải lớn hơn 0")
        self._ttl_seconds = ttl_seconds
        self._max_studies = max_studies
        self._studies: dict[str, UploadStudy] = {}
        self._lock = threading.RLock()

    def _prune(self, now: float) -> None:
        expired = [key for key, study in self._studies.items() if study.expires_at <= now]
        for key in expired:
            del self._studies[key]
        overflow = len(self._studies) - self._max_studies
        if overflow > 0:
            oldest = sorted(self._studies.items(), key=lambda item: item[1].expires_at)
            for key, _ in oldest[:overflow]:
                del self._studies[key]

    def create(
        self, volume: np.ndarray, masks: np.ndarray, spacing_mm: np.ndarray
    ) -> UploadViewInfo:
        """Retain the exact model crop and return safe viewer metadata."""
        if volume.ndim != 4 or volume.shape[0] != len(PHASES):
            raise ValueError(f"MRI crop upload phải có shape (8, X, Y, Z), nhận {volume.shape}")
        if masks.shape != volume.shape:
            raise ValueError(f"mask crop upload {masks.shape} khác MRI crop {volume.shape}")
        if len(spacing_mm) != 3:
            raise ValueError("spacing crop upload phải có đúng 3 giá trị")

        shape = [int(value) for value in volume.shape[1:]]
        spacing = [float(value) for value in spacing_mm]
        volumes: dict[str, np.ndarray] = {}
        annotations: dict[str, np.ndarray] = {}
        infos: list[CaseVolumeInfo] = []
        for index, phase in enumerate(PHASES):
            image = np.ascontiguousarray(volume[index], dtype=np.float32).copy()
            mask = np.ascontiguousarray(masks[index] > 0, dtype=np.uint8).copy()
            image.setflags(write=False)
            mask.setflags(write=False)
            volumes[phase.file_token] = image
            annotations[phase.file_token] = mask
            mask_slices = np.flatnonzero(mask.any(axis=(0, 1))).astype(int).tolist()
            infos.append(
                CaseVolumeInfo(
                    phase_name=phase.name,
                    file_token=phase.file_token,
                    shape=shape,
                    spacing_mm=spacing,
                    n_slices=shape[2],
                    has_mask=True,
                    mask_slices=mask_slices,
                )
            )

        now = time.monotonic()
        upload_id = uuid4().hex
        with self._lock:
            self._prune(now)
            self._studies[upload_id] = UploadStudy(
                volumes=volumes,
                masks=annotations,
                expires_at=now + self._ttl_seconds,
            )
            self._prune(now)
        return UploadViewInfo(
            upload_id=upload_id,
            volumes=infos,
            expires_in_seconds=self._ttl_seconds,
            note=(
                "Ảnh là crop ROI đã tiền xử lý đúng như UniFormer nhận. "
                "Bản xem chỉ tồn tại tạm thời trong bộ nhớ phiên này; ZIP và NIfTI gốc đã được xoá."
            ),
        )

    def render(self, upload_id: str, phase_token: str, z: int, *, annotation: bool) -> bytes | None:
        """Render an upload crop, or return ``None`` when it has expired."""
        if phase_token not in PHASE_BY_TOKEN:
            raise ValueError(f"không có thì MRI {phase_token!r}")
        now = time.monotonic()
        with self._lock:
            self._prune(now)
            study = self._studies.get(upload_id)
            if study is None:
                return None
            volume = study.volumes[phase_token]
            mask = study.masks[phase_token] if annotation else None
        return render_array_slice_png(volume, z, mask)


upload_studies = UploadStudyStore()
