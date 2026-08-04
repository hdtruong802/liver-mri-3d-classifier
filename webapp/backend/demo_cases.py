"""Ca demo dựng sẵn — đường đi chính của bản demo.

`PRODUCT.md` mục *Operating Context*: "Ca demo dựng sẵn (3–5 ca) là **đường đi chính**,
không phải phương án dự phòng." Lý do kỹ thuật: pipeline thật cắt bám tổn thương
(`crop_mode: lesion_tight` trong `configs/preprocess_e4.yaml`), nên suy luận cần ROI
của tổn thương. Tám file `.nii` thô mà người dùng tải lên **chưa đủ** để chạy đúng
như lúc train.

Bốn ca, tất cả đều có **dự đoán out-of-fold thật** — model chấm chúng chưa từng thấy
chúng khi train. Không ca nào lấy từ test-104 (`AGENTS.md` §3.4: held-out khoá kín,
chạm đúng một lần; tiêu lần chạm đó cho một ảnh minh hoạ là lãng phí).

Chúng được chọn theo hành vi đo được, mỗi ca một trạng thái mà giao diện phải xử lý:
nhận quyết, từ chối, ác tính bắt đúng, và **sai mà không tự biết**. Ca cuối là ca khó
chịu nhất và vì thế bắt buộc phải có.

Ảnh trích bằng `scripts/export_demo_cases.py` (chạy trên Kaggle), đặt ở
`data/sample/<bệnh nhân>/`. `data/` bị .gitignore — máy khác clone repo sẽ không có,
và `available=False` là trạng thái hợp lệ, app phải xuống thang tử tế.
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
    """Một ca demo.

    ⚠️ `case_id` và `file_stem` **khác nhau**, và gộp chúng lại là một lỗi im lặng.

    - `case_id` là **bệnh nhân** (`MR207769`) — khoá tra cứu dự đoán out-of-fold.
    - `file_stem` có thêm **chỉ số tổn thương** (`MR207769_3`) — tên file trên đĩa.

    Chỉ số tổn thương khác nhau giữa các bệnh nhân (0, 1, 3…), nên không suy ra được.
    Nếu dùng `file_stem` để tra dự đoán thì `normalize_pid("MR207769_3")` cho `2077693`,
    không khớp bệnh nhân nào, và app sẽ lặng lẽ rơi về số mô phỏng thay vì báo lỗi.
    """

    case_id: str
    file_stem: str
    label_vi: str
    directory: Path
    source_note: str


# Bốn ca chọn từ HÀNH VI ĐO ĐƯỢC của model trên out-of-fold (WORKLOG S-089), không
# phải chọn cho đẹp. Mỗi ca là một trạng thái giao diện phải xử lý được — kể cả trạng
# thái model sai mà không tự biết. Trích bằng `scripts/export_demo_cases.py`.
_SAMPLE = SAMPLE_DIR

DEMO_CASES: tuple[DemoCase, ...] = (
    DemoCase(
        case_id="MR170828",
        file_stem="MR170828_0",
        label_vi="U máu — mô hình nhận quyết",
        directory=_SAMPLE / "MR170828",
        source_note=(
            "Đoán đúng u máu. Các lượt dự đoán đồng thuận gần như tuyệt đối "
            "(bất định 0.0000), nên mô hình nhận quyết. Trạng thái tự tin và có quyền tự tin."
        ),
    ),
    DemoCase(
        case_id="MR207769",
        file_stem="MR207769_3",
        label_vi="Di căn — mô hình từ chối dù xác suất cao",
        directory=_SAMPLE / "MR207769",
        source_note=(
            "Nhãn thật là di căn; mô hình đoán áp-xe — SAI. Xác suất thô vẫn nói 0.936, "
            "nhưng các lượt dự đoán bất đồng mạnh nhất tập (0.3192) nên ca bị từ chối. "
            "Đây là ca cho thấy vì sao xếp hạng theo xác suất là không đủ."
        ),
    ),
    DemoCase(
        case_id="MR113627",
        file_stem="MR113627_1",
        label_vi="ICC — ác tính, bắt đúng",
        directory=_SAMPLE / "MR113627",
        source_note=(
            "Đoán đúng ung thư đường mật trong gan. Bất định 0.0993, dưới ngưỡng từ chối. "
            "Ca có ý nghĩa lâm sàng mà mô hình xử lý được."
        ),
    ),
    DemoCase(
        case_id="MR127280",
        file_stem="MR127280_3",
        label_vi="Di căn — mô hình sai mà không tự biết",
        directory=_SAMPLE / "MR127280",
        source_note=(
            "Nhãn thật là di căn; mô hình đoán u máu — SAI — với xác suất 0.977 và bất "
            "định 0.0000, nên KHÔNG bị từ chối. Cơ chế từ chối không bắt được ca này. "
            "Ca này có mặt vì giấu nó đi là trình bày sai mức tin cậy của hệ thống."
        ),
    ),
)

CASES_BY_ID: dict[str, DemoCase] = {c.case_id: c for c in DEMO_CASES}


def _case_provenance(case: DemoCase) -> Provenance:
    """Nguồn của phần MÔ TẢ ca (ảnh, hình học) — không phải của kết quả suy luận.

    Ảnh là thật, đọc thẳng từ đĩa. Kết quả suy luận có provenance riêng, gắn ở
    `PredictResult` (`webapp/backend/inference.py`), và hai thứ đó có thể khác nguồn:
    ảnh thật + số mô phỏng là tổ hợp hợp lệ khi ca không nằm trong 394 ca out-of-fold.
    """
    from webapp.backend.predictions import load_store

    store = load_store()
    known = store is not None and store.get(case.case_id) is not None
    return Provenance(
        source=ProvenanceSource.OOF if known else ProvenanceSource.SIMULATED,
        model_version=None,
        note=case.source_note,
    )


def case_is_available(case: DemoCase) -> bool:
    """Dữ liệu của ca có trên máy này không.

    `data/` bị .gitignore nên máy khác clone repo về sẽ **không** có. Đó là đúng: đây
    là dữ liệu bệnh nhân. App phải xuống thang tử tế chứ không crash.
    """
    return len(find_phase_files(case.directory, case.file_stem)) == len(PHASES)


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
    files = find_phase_files(case.directory, case.file_stem)

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
        provenance=_case_provenance(case),
    )


def volume_path(case_id: str, file_token: str) -> Path | None:
    case = CASES_BY_ID.get(case_id)
    if case is None:
        return None
    return find_phase_files(case.directory, case.file_stem).get(file_token)
