"""Taxonomy 7 lớp LLD-MMRI (chốt Spec Sheet §1).

Chỉ số theo `Category_info` trong annotation. Benign [0,2,4,5] / Malignant [1,3,6].
Đây là nguồn tên lớp duy nhất — không hardcode tên rải rác nơi khác.
"""

from __future__ import annotations

CLASS_NAMES: dict[int, str] = {
    0: "Hepatic_hemangioma",
    1: "Intrahepatic_cholangiocarcinoma",
    2: "Hepatic_abscess",
    3: "Hepatic_metastasis",
    4: "Hepatic_cyst",
    5: "FOCAL_NODULAR_HYPERPLASIA",
    6: "Hepatocellular_carcinoma",
}

# Nhãn ngắn tiếng Việt cho báo cáo/UI.
SHORT_NAMES: dict[int, str] = {
    0: "u máu",
    1: "ICC",
    2: "áp-xe",
    3: "di căn",
    4: "nang",
    5: "FNH",
    6: "HCC",
}

MALIGNANT_INDICES: frozenset[int] = frozenset({1, 3, 6})
NUM_CLASSES = 7


def is_malignant(class_index: int) -> bool:
    """True nếu lớp thuộc nhóm ác (ICC / di căn / HCC)."""
    return class_index in MALIGNANT_INDICES
