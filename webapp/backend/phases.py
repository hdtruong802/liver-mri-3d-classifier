"""Tám thì MRI của LLD-MMRI và cách nhận diện chúng từ tên file.

Contract ở `docs/liver_mri_3d_classification_plan.md` §8.1: backend nhận diện thì
theo **token trong tên file**, không dựa vào thứ tự người dùng chọn. Frontend dùng
picker đa tệp nên thứ tự là ngẫu nhiên.

Nguồn sự thật của danh sách thì là `configs/data.yaml` (khối `phases`). Ở đây chép
lại thành hằng số vì lớp serve **không được kéo theo pyyaml và cả stack train**
(`AGENTS.md` §5: hai file requirements tách nhau). `tests/test_webapp_phases.py`
đối chiếu hằng số này với `configs/data.yaml` nên hai bên không thể trôi khỏi nhau.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

NUM_PHASES = 8


@dataclass(frozen=True)
class Phase:
    """Một thì MRI.

    `name` là tên trong annotation JSON, `file_token` là token trong tên file ảnh.
    Hai cái khác nhau ở In Phase / Out Phase: annotation có dấu cách, tên file thì
    không (xem ghi chú trong `configs/data.yaml`).
    """

    index: int
    name: str
    file_token: str
    label_vi: str
    description_vi: str


PHASES: tuple[Phase, ...] = (
    Phase(0, "C-pre", "C-pre", "C-pre", "Trước tiêm thuốc tương phản"),
    Phase(1, "C+A", "C+A", "C+A", "Thì động mạch"),
    Phase(2, "C+V", "C+V", "C+V", "Thì tĩnh mạch cửa, thì tham chiếu"),
    Phase(3, "C+Delay", "C+Delay", "C+Delay", "Thì muộn"),
    Phase(4, "T2WI", "T2WI", "T2WI", "Chuỗi xung T2, nhạy với dịch"),
    Phase(5, "DWI", "DWI", "DWI", "Khuếch tán"),
    Phase(6, "In Phase", "InPhase", "In Phase", "T1 cùng pha"),
    Phase(7, "Out Phase", "OutPhase", "Out Phase", "T1 nghịch pha"),
)

PHASE_BY_TOKEN: dict[str, Phase] = {p.file_token: p for p in PHASES}
PHASE_BY_NAME: dict[str, Phase] = {p.name: p for p in PHASES}

# Token dài phải thử trước token ngắn: 'C+V' là con của 'C+Delay'? không, nhưng
# 'C-pre' và 'C+A' đều ngắn hơn 'InPhase'/'OutPhase', và quan trọng hơn: 'InPhase'
# là hậu tố của 'OutPhase'. Khớp 'InPhase' trước sẽ gán nhầm file Out Phase.
_TOKENS_LONGEST_FIRST: tuple[str, ...] = tuple(
    sorted((p.file_token for p in PHASES), key=len, reverse=True)
)

_SUFFIX_RE = re.compile(r"\.nii(\.gz)?$", re.IGNORECASE)


class PhaseDetectionError(ValueError):
    """Không suy ra được thì từ tên file, hoặc bộ file không hợp lệ."""


def strip_suffix(filename: str) -> str:
    """Bỏ đuôi `.nii` hoặc `.nii.gz`, giữ nguyên phần còn lại."""
    return _SUFFIX_RE.sub("", filename.strip())


def detect_phase(filename: str) -> Phase:
    """Suy ra thì từ tên file.

    Khớp không phân biệt hoa thường, và khớp token DÀI trước token ngắn — nếu không
    thì `MR-1_1_OutPhase.nii` bị bắt bởi token `InPhase` (hậu tố của `OutPhase`) và
    gán sai thì. Đây là lỗi im lặng: nó không crash, chỉ hoán hai kênh đầu vào.
    """
    stem = strip_suffix(filename).lower()
    for token in _TOKENS_LONGEST_FIRST:
        if token.lower() in stem:
            return PHASE_BY_TOKEN[token]
    raise PhaseDetectionError(
        f"không nhận ra thì nào trong tên file {filename!r}; "
        f"tên file phải chứa một trong {[p.file_token for p in PHASES]}"
    )


def detect_phase_set(filenames: list[str]) -> dict[str, str]:
    """Map `file_token -> filename` cho một bộ file, kiểm đủ 8 thì và không trùng.

    Raise `PhaseDetectionError` khi thiếu thì, thừa file, hoặc hai file cùng trỏ về
    một thì. Không tự đoán bù: bộ đầu vào sai thì kết quả suy luận vô nghĩa, và im
    lặng chấp nhận sẽ tạo ra một con số trông hợp lý.
    """
    found: dict[str, str] = {}
    duplicates: list[str] = []
    for filename in filenames:
        phase = detect_phase(filename)
        if phase.file_token in found:
            duplicates.append(f"{phase.name}: {found[phase.file_token]!r} và {filename!r}")
        else:
            found[phase.file_token] = filename

    if duplicates:
        raise PhaseDetectionError("hai file cùng trỏ về một thì — " + "; ".join(duplicates))

    missing = [p.name for p in PHASES if p.file_token not in found]
    if missing:
        raise PhaseDetectionError(f"thiếu {len(missing)} thì: {missing}")
    return found
