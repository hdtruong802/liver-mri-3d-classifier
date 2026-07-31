"""Nhận diện thì từ tên file (contract plan §8.1).

Lỗi ở lớp này không crash — nó hoán hai kênh đầu vào rồi cho ra một con số trông
hợp lý. Đó là lý do phần này được khoá bằng test chứ không tin vào đọc code.
"""

from __future__ import annotations

import pytest
import yaml
from webapp.backend.phases import (
    NUM_PHASES,
    PHASES,
    PhaseDetectionError,
    detect_phase,
    detect_phase_set,
    strip_suffix,
)

REPO_CONFIG = "configs/data.yaml"


def test_phase_list_matches_data_yaml() -> None:
    """Hằng số trong lớp serve phải khớp `configs/data.yaml`.

    Backend chép lại danh sách thì thay vì đọc YAML (để không kéo pyyaml vào lớp
    serve). Test này là thứ duy nhất giữ hai bên khỏi trôi khỏi nhau.
    """
    with open(REPO_CONFIG, encoding="utf-8") as handle:
        config = yaml.safe_load(handle)

    expected = [(entry["name"], entry["file"]) for entry in config["phases"]]
    actual = [(p.name, p.file_token) for p in PHASES]
    assert actual == expected


def test_has_eight_phases() -> None:
    assert len(PHASES) == NUM_PHASES == 8


def test_no_adc_or_hepatobiliary_phase() -> None:
    """Bản bolt dùng ADC và HBP — hai thì KHÔNG có trong LLD-MMRI.

    Dataset có In Phase và Out Phase ở hai vị trí đó. Giữ test này để lần sau không
    ai chép lại danh sách thì từ một bản dựng nào khác.
    """
    tokens = {p.file_token.lower() for p in PHASES}
    assert "adc" not in tokens
    assert not any("hepatobiliary" in t or t == "hbp" for t in tokens)
    assert "inphase" in tokens
    assert "outphase" in tokens


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("MR-391135_1_C-pre_0000.nii", "C-pre"),
        ("MR-391135_1_C+A_0000.nii", "C+A"),
        ("MR-391135_1_C+V_0000.nii", "C+V"),
        ("MR-391135_1_C+Delay_0000.nii", "C+Delay"),
        ("MR-391135_1_T2WI_0000.nii", "T2WI"),
        ("MR-391135_1_DWI_0000.nii", "DWI"),
        ("MR-391135_1_InPhase_0000.nii", "In Phase"),
        ("MR-391135_1_OutPhase_0000.nii", "Out Phase"),
    ],
)
def test_detect_phase_on_real_filenames(filename: str, expected: str) -> None:
    assert detect_phase(filename).name == expected


def test_outphase_not_swallowed_by_inphase() -> None:
    """`InPhase` là hậu tố của `OutPhase`.

    Khớp token ngắn trước sẽ gán file Out Phase thành In Phase, im lặng, và đổi thứ
    tự hai kênh đầu vào của model. Đây là bug đắt nhất mà module này có thể có.
    """
    assert detect_phase("MR-1_1_OutPhase_0000.nii").name == "Out Phase"
    assert detect_phase("patient_OUTPHASE.nii.gz").name == "Out Phase"


def test_detect_phase_is_case_insensitive() -> None:
    assert detect_phase("MR-1_1_c+v_0000.NII").name == "C+V"
    assert detect_phase("MR-1_1_t2wi_0000.nii").name == "T2WI"


def test_detect_phase_rejects_unknown() -> None:
    with pytest.raises(PhaseDetectionError, match="không nhận ra thì"):
        detect_phase("MR-1_1_ADC_0000.nii")


def test_strip_suffix() -> None:
    assert strip_suffix("a_C+V_0000.nii") == "a_C+V_0000"
    assert strip_suffix("a_C+V_0000.nii.gz") == "a_C+V_0000"
    assert strip_suffix("a_C+V_0000.NII.GZ") == "a_C+V_0000"


def _full_set() -> list[str]:
    return [f"MR-391135_1_{p.file_token}_0000.nii" for p in PHASES]


def test_detect_phase_set_accepts_full_set_in_any_order() -> None:
    """Thứ tự người dùng chọn file là ngẫu nhiên; contract nói không được phụ thuộc."""
    names = _full_set()
    forward = detect_phase_set(names)
    backward = detect_phase_set(list(reversed(names)))
    assert forward == backward
    assert len(forward) == 8


def test_detect_phase_set_rejects_missing() -> None:
    names = _full_set()[:-1]
    with pytest.raises(PhaseDetectionError, match="thiếu 1 thì"):
        detect_phase_set(names)


def test_detect_phase_set_rejects_duplicate() -> None:
    names = _full_set()
    names[0] = names[1].replace("_0000", "_0001")  # hai file cùng trỏ về C+A
    with pytest.raises(PhaseDetectionError, match="cùng trỏ về một thì"):
        detect_phase_set(names)
