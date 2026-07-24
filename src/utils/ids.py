"""Chuẩn hoá patient ID LLD-MMRI.

Ba nguồn ID không đồng nhất về hình thức:
- annotation JSON: 16/498 key dạng `MR-xxxxxx` (có gạch nối), còn lại `MRxxxxxx`;
- file split (từ ZHEGG): `MRxxxxxx`;
- tên file ảnh: `MR-xxxxxx_<lesion>_<phase>_0000.nii.gz`.

Khoá map tin cậy duy nhất = **phần chữ số**. Mọi so khớp file↔annotation↔split
phải đi qua `normalize_pid()`; không so khớp chuỗi thô.
"""

from __future__ import annotations

import re

_NON_DIGIT = re.compile(r"\D")


def normalize_pid(patient_id: str) -> str:
    """Trả về phần chữ số của patient ID, dùng làm khoá map thống nhất.

    Ví dụ: ``"MR-391135" -> "391135"``, ``"MR207602" -> "207602"``.
    """
    digits = _NON_DIGIT.sub("", patient_id)
    if not digits:
        raise ValueError(f"patient id không chứa chữ số: {patient_id!r}")
    return digits
