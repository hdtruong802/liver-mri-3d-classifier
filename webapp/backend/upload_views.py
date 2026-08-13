"""Short-lived source-MRI viewer for a completed upload.

The classifier receives a lesion-tight UniFormer crop, but the reader needs
the original MRI volume for anatomical context. This cache owns one private
temporary extraction directory and deletes it on expiry or replacement.
"""

from __future__ import annotations

import shutil
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from webapp.backend.config import UPLOAD_VIEW_MAX_STUDIES, UPLOAD_VIEW_TTL_SECONDS
from webapp.backend.phases import PHASE_BY_TOKEN, PHASES
from webapp.backend.schemas import CaseVolumeInfo, UploadViewInfo
from webapp.backend.volumes import mask_slice_flags, read_geometry, render_slice_png


@dataclass(frozen=True)
class UploadStudy:
    """One temporary source study. Paths are owned by ``directory``."""

    images: dict[str, Path]
    masks: dict[str, Path]
    directory: Path
    expires_at: float


class UploadStudyStore:
    """Thread-safe bounded owner for temporary source MRI files."""

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

    @staticmethod
    def _delete(study: UploadStudy) -> None:
        shutil.rmtree(study.directory, ignore_errors=True)

    def _drop(self, upload_id: str) -> None:
        study = self._studies.pop(upload_id, None)
        if study is not None:
            self._delete(study)

    def _prune(self, now: float) -> None:
        for upload_id, study in list(self._studies.items()):
            if study.expires_at <= now:
                self._drop(upload_id)
        overflow = len(self._studies) - self._max_studies
        if overflow > 0:
            oldest = sorted(self._studies.items(), key=lambda item: item[1].expires_at)
            for upload_id, _ in oldest[:overflow]:
                self._drop(upload_id)

    def create(
        self,
        images: dict[str, Path],
        masks: dict[str, Path],
        directory: Path,
    ) -> UploadViewInfo:
        """Transfer ownership of extracted source NIfTI files to this cache."""
        if not directory.is_dir():
            raise ValueError("thư mục tạm chứa MRI tải lên không còn tồn tại")
        infos: list[CaseVolumeInfo] = []
        for phase in PHASES:
            image_path = images.get(phase.file_token)
            mask_path = masks.get(phase.file_token)
            if image_path is None or mask_path is None:
                raise ValueError(f"thiếu ảnh hoặc mask thì {phase.label_vi} cho viewer")
            shape, spacing = read_geometry(image_path)
            flags = mask_slice_flags(mask_path)
            if len(flags) != shape[2]:
                raise ValueError(f"mask thì {phase.label_vi} không khớp số lát ảnh MRI")
            infos.append(
                CaseVolumeInfo(
                    phase_name=phase.name,
                    file_token=phase.file_token,
                    shape=list(shape),
                    spacing_mm=list(spacing),
                    n_slices=shape[2],
                    has_mask=True,
                    mask_slices=[index for index, present in enumerate(flags) if present],
                )
            )

        now = time.monotonic()
        upload_id = uuid4().hex
        with self._lock:
            self._prune(now)
            self._studies[upload_id] = UploadStudy(
                images=dict(images),
                masks=dict(masks),
                directory=directory,
                expires_at=now + self._ttl_seconds,
            )
            self._prune(now)
        return UploadViewInfo(
            upload_id=upload_id,
            volumes=infos,
            expires_in_seconds=self._ttl_seconds,
            note=(
                "Ảnh MRI gốc của bộ vừa tải lên, chưa crop. "
                "Bản xem tạm thời bị xoá khi hết hạn hoặc khi bạn tải bộ MRI mới."
            ),
        )

    def render(self, upload_id: str, phase_token: str, z: int, *, annotation: bool) -> bytes | None:
        """Render a source slice, or return ``None`` after the cache expires."""
        if phase_token not in PHASE_BY_TOKEN:
            raise ValueError(f"không có thì MRI {phase_token!r}")
        with self._lock:
            self._prune(time.monotonic())
            study = self._studies.get(upload_id)
            if study is None:
                return None
            return render_slice_png(
                study.images[phase_token],
                z,
                study.masks[phase_token] if annotation else None,
            )


upload_studies = UploadStudyStore()
