"""Ca demo dựng sẵn — đường đi chính của bản demo.

`PRODUCT.md` mục *Operating Context*: "Ca demo dựng sẵn (3–5 ca) là **đường đi chính**,
không phải phương án dự phòng." Lý do kỹ thuật: pipeline thật cắt bám tổn thương
(`crop_mode: lesion_tight` trong `configs/preprocess_e4.yaml`), nên suy luận cần ROI
của tổn thương. Tám file `.nii` thô mà người dùng tải lên **chưa đủ** để chạy đúng
như lúc train.

Hiện có đúng một ca: `MR-391135_1` trong `data/sample/`, ảnh thật, đủ 8 thì. Ở W5,
khi CV 5-fold xong, thay bằng 3–5 ca có prediction out-of-fold thật — **không dùng
test-104** (`AGENTS.md` §3.4: held-out khoá kín, chạm đúng một lần).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from webapp.backend.config import SAMPLE_DIR
from webapp.backend.phases import PHASES
from webapp.backend.schemas import (
    CaseDetail,
    CaseSummary,
    CaseVolumeInfo,
    Provenance,
    ProvenanceSource,
)
from webapp.backend.volumes import find_phase_files, read_geometry

REFERENCE_PHASE = "C+V"  # Thì tham chiếu theo Spec Sheet §2 và `configs/preprocess_e4.yaml`.


@dataclass(frozen=True)
class DemoCase:
    case_id: str
    label_vi: str
    directory: Path
    source_note: str


DEMO_CASES: tuple[DemoCase, ...] = (
    DemoCase(
        case_id="MR-391135_1",
        label_vi="Ca mẫu LLD-MMRI, đủ 8 thì",
        directory=SAMPLE_DIR,
        source_note=(
            "Ảnh MRI thật từ dataset LLD-MMRI, đọc trực tiếp từ đĩa. "
            "Kết quả suy luận đi kèm là số minh hoạ, chưa có model."
        ),
    ),
)

CASES_BY_ID: dict[str, DemoCase] = {c.case_id: c for c in DEMO_CASES}


def _simulated_provenance(case: DemoCase) -> Provenance:
    return Provenance(
        source=ProvenanceSource.SIMULATED,
        model_version=None,
        note=case.source_note,
    )


def case_is_available(case: DemoCase) -> bool:
    """Dữ liệu của ca có trên máy này không.

    `data/` bị .gitignore nên máy khác clone repo về sẽ **không** có. Đó là đúng: đây
    là dữ liệu bệnh nhân. App phải xuống thang tử tế chứ không crash.
    """
    return len(find_phase_files(case.directory, case.case_id)) == len(PHASES)


def list_cases() -> list[CaseSummary]:
    return [
        CaseSummary(
            case_id=c.case_id,
            label_vi=c.label_vi,
            source_note=c.source_note,
            available=case_is_available(c),
        )
        for c in DEMO_CASES
    ]


def get_case_detail(case_id: str) -> CaseDetail:
    """Hình học thật của 8 volume, đọc từ header NIfTI."""
    case = CASES_BY_ID[case_id]
    files = find_phase_files(case.directory, case.case_id)

    volumes: list[CaseVolumeInfo] = []
    for phase in PHASES:
        path = files.get(phase.file_token)
        if path is None:
            continue
        shape, spacing = read_geometry(path)
        volumes.append(
            CaseVolumeInfo(
                phase_name=phase.name,
                file_token=phase.file_token,
                shape=list(shape),
                spacing_mm=[round(v, 4) for v in spacing],
                n_slices=shape[2],
            )
        )

    return CaseDetail(
        case_id=case.case_id,
        label_vi=case.label_vi,
        source_note=case.source_note,
        volumes=volumes,
        reference_phase=REFERENCE_PHASE,
        provenance=_simulated_provenance(case),
    )


def volume_path(case_id: str, file_token: str) -> Path | None:
    case = CASES_BY_ID.get(case_id)
    if case is None:
        return None
    return find_phase_files(case.directory, case.case_id).get(file_token)
